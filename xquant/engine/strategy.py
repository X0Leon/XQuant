# -*- coding: utf-8 -*-

"""
Strategy类
Strategy对象计算市场数据，产生signal给Portfolio对象
market data by DataHandler -> Strategy -> signal for Portfolio

@author: Leon Zhang
@version: 0.3
"""

import pandas as pd
from abc import ABCMeta, abstractmethod
from .event import SignalEvent


class Strategy(object):
    """
    Strategy抽象基类
    此类及其继承类通过对Bars(SD-OHLCV)（由DataHandler对象生成）处理产生Signal对象
    Strategy类对历史数据和实时数据均有效，实际上它对数据来源不知晓，直接从queue对象获取bar元组
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self, *args):
        """
        提供计算信号的机制
        """
        raise NotImplementedError("Should implement calculate_signals()!")


######################### 以下为使用的例子，请直接参考demo文件夹 ###############
# 例1：买入并持有的策略
class BuyAndHoldStrategy(Strategy):
    """
    最简单的例子：对所以股票持多头策略
    用于：测试代码；作为benchmark
    """

    def __init__(self, bars, events):
        """
        初始化买入持有策略
        参数：
        bars: DataHandler对象的数据，它有诸多属性和方法，参见data模块
        events: Event对象
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        self.bought = self._calculate_initial_bought()  # 字典

    def _calculate_initial_bought(self):
        """
        添加key到bought字典，将所有股票的值设为False，意指尚未持有
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought

    def calculate_signals(self, event):
        """
        此策略对每只股票只产生一个信号，那就是买入，没有exit信号
        从策略初始化的那个时间买入持有
        参数：
        event: MarketEvent对象
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=1)
                if bars is not None and bars != [] and self.bought[s] is False:
                    # 格式(Symbol, Datetime, Type = LONG, SHORT or EXIT)
                    signal = SignalEvent(bars[0][0], bars[0][1], 'LONG')
                    self.events.put(signal)
                    self.bought[s] = True


# 例2：移动双均线策略（最简单的动量策略）
class MovingAverageCrossStrategy(Strategy):
    """
    移动双均线策略
    """

    def __init__(self, bars, events, long_window=10, short_window=5):
        """
        初始化移动双均线策略
        参数：
        bars：DataHandler类的对象，属性和方法可以具体参考data模块
        events: Event对象
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.long_window = long_window  # 长期均线
        self.short_window = short_window  # 短期均线

        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        """
        添加key到bought字典，将所有股票的值设为False，意指尚未持有
        TODO：是否可以用组合中虚拟账户来监控，strategy只管发信号呢？
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought

    def calculate_signals(self, event):
        """
        当短期均线（如5日线）上穿长期均线（如10日线），买入
        反之，卖出；不做空
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=self.long_window)  # 元组的列表
                if bars is not None and bars != [] and len(bars) >= self.long_window:
                    # 转换成DataFrame计算，代码量少一些，暂不考虑速度
                    cols = ['symbol', 'datetime', 'open', 'high', 'low', 'close', 'volume']
                    df = pd.DataFrame(bars, columns=cols)
                    df['MA_long'] = df['close'].rolling(center=False, window=self.long_window, min_periods=1).mean()
                    df['MA_short'] = df['close'].rolling(center=False, window=self.short_window, min_periods=1).mean()
                    if df['MA_long'].iloc[-1] < df['MA_short'].iloc[-1] and df['MA_long'].iloc[-2] \
                            > df['MA_short'].iloc[-2] and not self.bought[s]:
                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG')
                        self.events.put(signal)
                        self.bought[s] = True

                    elif df['MA_long'].iloc[-1] > df['MA_short'].iloc[-1] and df['MA_long'].iloc[-2] \
                            < df['MA_short'].iloc[-2] and self.bought[s]:
                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'EXIT')
                        self.events.put(signal)
                        self.bought[s] = False
