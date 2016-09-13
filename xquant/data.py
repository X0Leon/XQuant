# -*- coding: utf-8 -*-

"""
DataHandler抽象基类
数据处理不区分历史数据还是实时数据

@author: X0Leon
@version: 0.2.0a
"""

import datetime
import os
# import numpy as np
import pandas as pd

from abc import ABCMeta, abstractmethod

from .event import MarketEvent


class DataHandler(object):
    """
    DataHandler抽象基本，不允许直接实例化，只用于继承
    继承的DataHandler对象用于对每个symbol生成bars序列（OLHCV）
    这里不区分历史数据和实时交易数据
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        从latest_symbol列表中返回最近的几根bar，
        如果可用值小于N，则返回全部所能的使用k bar
        """
        raise NotImplementedError("未实现get_latest_bars()，此方法是必须的！")

    @abstractmethod
    def update_bars(self):
        """
        将股票列表中bar(条状图，k线)更新到最近的那一根
        """
        raise NotImplementedError("未实现update_bars()，此方法是必须的！")


######################
# 对不同数据来源具体处理 #
######################

class CSVDataHandler(DataHandler):
    """
    CSVDataHandler类用于从硬盘中读取csv格式的历史数据，并实现最新的bar模拟实时交易的情况
    """
    def __init__(self, events, csv_dir, symbol_list):
        """
        初始化历史数据的处理，假设文件以股票代码+csv格式存储，如600008.csv
        日期升序排列，仅包含'datetime','open','high','low','close','volume'
        参数：
        events: 事件队列（Event Queue）
        cdv_dir：CSV文件的绝对路径，如"d:/data/"或者使用“d:\\..."
        symbol_list: 股票代码列表，如['600008', '600018']
        dfmt: 用于_get_new_bar()函数中转换datetime类型所用的日期字符串格式
              日间一般是：'%Y-%m-%d'，日内可能是：'%Y-%m-%d %H:%M:%S'
        """
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}  # key为股票代码，value为数据df iterrows()迭代器
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        从数据文件夹中打开CSV文件，转换成pandas的DataFrames格式，union所有股票index, 即datetime
        用_开头说明这是一个仅供内部使用的方法（私有方法）
            'datetime','open','high','low','close','volume'
            日期升序排列
        """
        comb_index = None  # datetime作为index，不同股票之间取并集，对数据做相应的填充
        for s in self.symbol_list:
            # 直接用pd.read_csv()
            self.symbol_data[s] = pd.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header=0, index_col=0, parse_dates=True,
                names=['datetime', 'open', 'high', 'low', 'close', 'volume']
            ).sort_index()  # 强制日期升序
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)  # 取datetime index的并集
                # 因为不同股票的交易时间不同

                # 将字典中该只股票的最新数据设置为None，例如{'600008':[],}
                # 不用担心，在下面update_bars()方法中会更新出实际意义的数据
            self.latest_symbol_data[s] = []

        for s in self.symbol_list:
            # 合并index后的股票数据，所有股票的index相同
            # method指明对缺失值的填充方式，pad/ffill是用向前取值
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()

    def _get_new_bar(self, symbol):
        """
        返回最新的bar，格式为(symbol, datetime, open, low, high, close, volume)
        生成器，每次调用生成一个新的bar，直到数据最后
        """
        for b in self.symbol_data[symbol]:
            # 测试日间数据，日内的话 '%Y-%m-%d %H:%M:%S'
            yield tuple([symbol, b[0], b[1][0], b[1][1], b[1][2], b[1][3], b[1][4]])

    # 实现ABC CSVDataHandler中方法get_latest_bars()
    def get_latest_bars(self, symbol, N=1):
        """
        从latest_symbol列表中返回最新的N个bar，或者所能返回的最大数量的bar
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("数据库中不存在此股票！")
        else:
            return bars_list[-N:]

    def get_latest_bar(self, symbol):
        """
        从latest_symbol列表中直接返回最后的bar
        而get_latest_bars(symbol, N=1)返回元素只有最后一个bar的list
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("数据库中不存在此股票！")
        else:
            return bars_list[-1]

    def get_latest_bar_datetime(self, symbol):
        """
        返回最后一个bar的Python datetime对象
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("数据库中不存在此股票")
        else:
            return bars_list[-1][1]

    # 实现ABC CSVDataHandler中方法update_bars()
    def update_bars(self):
        """
        对于symbol list中所有股票，将最新的bar更新到latest_symbol_data字典
        """
        for s in self.symbol_list:
            try:
                bar = self._get_new_bar(s).__next__()
            except StopIteration:
                self.continue_backtest = False  # 跳出回测while的flag
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())  # events是queue结构，put()和get()为进出队列


class DictDFDataHandler(DataHandler):
    """
    适应各种数据源的pandas DataFrame格式的数据处理，
    用户输入符合格式的dict of df，index为datetime类型，cols=(open,high,low,close,volume)
    输出为bars格式，list of tuples：[(symbol,open,high,low,close,volume),(...),(...)]
    """
    def __init__(self, events, dict_df):
        """
        日期升序排列，仅包含'datetime'(index),'open','high','low','close','volume'
        参数：
        events: 事件队列（Event Queue）
        dict_frame: pandas DataFrame的字典，key为股票代码str，如'600008’
        """
        self.events = events
        self.symbol_list = list(dict_df.keys())

        self.symbol_data = dict_df
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._convert_df()

    def _convert_df(self):
        """
        将不同股票的index取union存在symbol_data中
        """
        comb_index = None  # datetime作为index，不同股票之间取并集，对数据做相应的填充
        for s in self.symbol_list:
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)  # 取datetime index的并集
            self.latest_symbol_data[s] = []

        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()

    def _get_new_bar(self, symbol):
        """
        返回最新的bar，格式为(symbol, datetime, open, low, high, close, volume)
        生成器，每次调用生成一个新的bar，直到数据最后
        """
        for b in self.symbol_data[symbol]:
            yield tuple([symbol, b[0], b[1][0], b[1][1], b[1][2], b[1][3], b[1][4]])

    def get_latest_bars(self, symbol, N=1):
        """
        从latest_symbol列表中返回最新的N个bar，或者所能返回的最大数量的bar
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("数据库中不存在此股票！")
        else:
            return bars_list[-N:]

    def get_latest_bar(self, symbol):
        """
        从latest_symbol列表中直接返回最后的bar
        而get_latest_bars(symbol, N=1)返回元素只有最后一个bar的list
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("数据库中不存在此股票！")
        else:
            return bars_list[-1]

    def get_latest_bar_datetime(self, symbol):
        """
        返回最后一个bar的Python datetime对象
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("数据库中不存在此股票")
        else:
            return bars_list[-1][1]

    def update_bars(self):
        """
        对于symbol list中所有股票，将最新的bar更新到latest_symbol_data字典
        """
        for s in self.symbol_list:
            try:
                bar = self._get_new_bar(s).__next__()
            except StopIteration:
                self.continue_backtest = False  # 跳出回测while的flag
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())


class TushareDataHandler(DataHandler):
    pass


class HDF5DataHandler(DataHandler):
    pass
