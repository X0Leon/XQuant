# -*- coding: utf-8 -*-

"""
使用双均线策略测试

@author: Leon Zhang
@version: 0.5.2
"""

import os
import datetime
import pandas as pd

from xquant import SignalEvent, Strategy, CSVDataHandler, SimulatedExecutionHandler, BasicPortfolio, Backtest


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

        self.bought = self._calculate_initial_bought()  # 或 {s: False for s in self.symbol_list}

    def _calculate_initial_bought(self):
        """
        添加symbol的持有情况到字典，初始化为未持有
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = False  # 或者'EXIT'
        return bought

    def calculate_signals(self, event):
        """
        当短期均线（如5日线）上穿长期均线（如10日线），买入；反之，卖出
        """
        if event.type == 'BAR':
            for s in self.symbol_list:
                bar = self.bars.get_latest_bar(s)
                if bar is None or bar == []: continue

                bars = self.bars.get_latest_bars(s, N=self.long_window)
                if len(bars) >= self.long_window:
                    df = pd.DataFrame(bars, columns=['symbol','datetime','open','high','low','close','volume'])
                    df['MA_l'] = df['close'].rolling(self.long_window, min_periods=1).mean()
                    df['MA_s'] = df['close'].rolling(self.short_window, min_periods=1).mean()
                    if df['MA_l'].iloc[-1] < df['MA_s'].iloc[-1] and df['MA_l'].iloc[-2] > df['MA_s'].iloc[-2]:
                        if not self.bought[s]:
                            signal = SignalEvent(bar.symbol, bar.datetime, 'LONG')
                            self.events.put(signal)
                            self.bought[s] = True
                    elif df['MA_l'].iloc[-1] < df['MA_s'].iloc[-1] and df['MA_l'].iloc[-2] < df['MA_s'].iloc[-2]:
                        if self.bought[s]:
                            signal = SignalEvent(bar.symbol, bar.datetime, 'EXIT')
                            self.events.put(signal)
                            self.bought[s] = False


if __name__ == '__main__':
    csv_dir = os.path.join(os.path.dirname(os.getcwd()), 'demo/testdata')
    symbol_list = ['600008', '600018']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2015, 10, 2, 0, 0)
    end_date = datetime.datetime(2015, 12, 30, 23, 59)

    backtest = Backtest(csv_dir, symbol_list, initial_capital, heartbeat,
                        start_date, end_date, CSVDataHandler, SimulatedExecutionHandler,
                        BasicPortfolio, MovingAverageCrossStrategy,
                        slippage_type='fixed', commission_type='default',
                        long_window=10, short_window=5)

    positions, holdings = backtest.simulate_trading()
    print(holdings.tail())
