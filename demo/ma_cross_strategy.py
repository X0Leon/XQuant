# -*- coding: utf-8 -*-

"""
使用双均线策略测试backtest模块），及底层核心模块

@author: X0Leon
@version: 0.2
"""

import os
import datetime
import pandas as pd

from xquant import SignalEvent, Strategy, CSVDataHandler, \
    SimulatedExecutionHandler, BasicPortfolio, Backtest


class MovingAverageCrossStrategy(Strategy):
    """
    移动双均线策略
    """
    def __init__(self, bars, events, long_window=10, short_window=5):
        """
        初始化移动平均线策略
        参数：
        bars: DataHandler对象
        events: Event队列对象
        long_window: 长期均线的长度
        short_window: 短期均线的长度
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.long_window = long_window
        self.short_window = short_window

        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        """
        添加symbol的持有情况到字典，初始化为未持有
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
                bars = self.bars.get_latest_bars(s, N=self.long_window) # 元组列表
                if bars is not None and bars != [] and len(bars) >= self.long_window:
                    cols = ['symbol','datetime','open','high','low','close','volume']
                    df = pd.DataFrame(bars,columns=cols)
                    df['MA_long'] = pd.rolling_mean(df['close'],self.long_window,min_periods=1)
                    df['MA_short'] = pd.rolling_mean(df['close'],self.short_window,min_periods=1)
                    if float(df['MA_long'][-1:]) < float(df['MA_short'][-1:]) and \
                                    float(df['MA_long'][-2:-1]) > float(df['MA_short'][-2:-1]):
                        if not self.bought[s]:
                            signal = SignalEvent(bars[-1][0],bars[-1][-1], 'LONG')
                            self.events.put(signal)
                            self.bought[s] = True
                    elif float(df['MA_long'][-1:]) < float(df['MA_short'][-1:]) and \
                                    float(df['MA_long'][-2:-1]) < float(df['MA_short'][-2:-1]):
                        if self.bought[s]:
                            signal = SignalEvent(bars[-1][0], bars[-1][0], 'EXIT')
                            self.events.put(signal)
                            self.bought[s] = False


if __name__ == '__main__':
    csv_dir = os.path.join(os.path.dirname(os.getcwd()),'testdata')# testdata地址
    symbol_list = ['600008', '600018']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2015, 11, 2, 0, 0)

    backtest = Backtest(csv_dir, symbol_list, initial_capital, heartbeat,
        start_date, CSVDataHandler, SimulatedExecutionHandler,
        BasicPortfolio, MovingAverageCrossStrategy)
    backtest.simulate_trading()

