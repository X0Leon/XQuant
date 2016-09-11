# -*- coding: utf-8 -*-

"""
供开发人员测试使用！

测试event, data, strategy, portfolio, execution模块，仅是中间测试

@author: X0Leon
@version: 0.2
"""

import queue
import datetime

from xquant.data import CSVDataHandler
from xquant.execution import SimulatedExecutionHandler
from xquant.portfolio import BasicPortfolio
from xquant.strategy import BuyAndHoldStrategy

events = queue.Queue()
start_date = datetime.datetime(2015, 11, 2, 0, 0)

csv_dir = 'd:/thinkquant/XQuant/testdata'
symbol_list = ['600008', '600018']

bars = CSVDataHandler(events, csv_dir, symbol_list)
strategy = BuyAndHoldStrategy(bars, events)
port = BasicPortfolio(bars, events, start_date, initial_capital=1.0e5)
broker = SimulatedExecutionHandler(bars,events)

while True:
    if bars.continue_backtest:
        bars.update_bars()
    else:
        break

    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            break
        else:
            if event is not None:
                if event.type == 'MARKET':
                    strategy.calculate_signals(event)
                    port.update_timeindex(event)

                elif event.type == 'SIGNAL':
                    port.update_signal(event)

                elif event.type == 'ORDER':
                    broker.execute_order(event)

                elif event.type == 'FILL':
                    port.update_fill(event)

    # time.sleep(24*60*60)

port.create_equity_curve_dataframe()
print(port.equity_curve)
print(port.output_summary_stats())
