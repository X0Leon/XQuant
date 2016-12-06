# -*- coding: utf-8 -*-

"""
DataHandler抽象基类

@author: X0Leon
@version: 0.4
"""

import datetime
import os
import sys
import pandas as pd
import functools
from collections import namedtuple
from abc import ABCMeta, abstractmethod

from .event import BarEvent


class DataHandler(object):
    """
    DataHandler抽象基类，不允许直接实例化，只用于继承
    继承的DataHandler对象用于对每个symbol生成bars序列（OHLCV）
    这里不区分历史数据和实时交易数据
    """
    # Bar = namedtuple('Bar', ('symbol', 'datetime', 'open', 'high', 'low', 'close', 'volume'))

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        从latest_symbol列表中返回最近的几根bar，
        如果可用值小于N，则返回全部所能的使用k bar
        """
        raise NotImplementedError("Should implement get_latest_bars()!")

    @abstractmethod
    def update_bars(self):
        """
        将股票列表中bar(条状图，k线)更新到最近的那一根
        """
        raise NotImplementedError("Should implement update_bars()！")


######################
# 对不同数据来源具体处理 #
######################

class CSVDataHandler(DataHandler):
    def __init__(self, events, csv_dir, symbol_list, start_date, end_date):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        从数据文件夹中打开CSV文件，转换成pandas的DataFrames格式，union所有股票index, 数据向前填充
        列：'datetime','open','high','low','close','volume' 日期升序排列
        """
        comb_index = None
        for s in self.symbol_list:
            self.symbol_data[s] = pd.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header=0, index_col=0, parse_dates=True,
                names=['datetime', 'open', 'high', 'low', 'close', 'volume']
            ).sort_index()[self.start_date:self.end_date]
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)
            self.latest_symbol_data[s] = []

        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()

    def _get_new_bar(self, symbol):
        """
        返回最新的bar，格式为(symbol, datetime, open, high, low, close, volume)
        生成器，每次调用生成一个新的bar，直到数据最后，在update_bars()中调用
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
            print("Not available symbol in the historical data set!")
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
            print("Not available symbol in the historical data set!")
        else:
            return bars_list[-1]

    def get_latest_bar_datetime(self, symbol):
        """
        返回最后一个bar的Python datetime对象
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Not available symbol in the historical data set!")
        else:
            return bars_list[-1][1]

    def update_bars(self):
        """
        对于symbol list中所有股票，将最新的bar更新到latest_symbol_data字典
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
                    self.events.put(BarEvent(bar))


class HDF5DataHandler(DataHandler):
    pass
