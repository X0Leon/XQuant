# -*- coding: utf-8 -*-

"""
测试event, data, strategy, portfolio, execution模块，
仅是中间测试，上层接口为backtest模块

@author: X0Leon
@version: 0.1
"""

import queue
import datetime
import os

from data import CSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import NaivePortfolio
from strategy import BuyAndHoldStrategy

events = queue.Queue()
start_date = datetime.datetime(2015, 11, 2, 0, 0)

csv_dir = 'd:/thinkquant/XQuant/data'
symbol_list = ['600008', '600018']

bars = CSVDataHandler(events, csv_dir, symbol_list)
strategy = BuyAndHoldStrategy(bars, events)
port = NaivePortfolio(bars, events, start_date, initial_capital=1.0e5)
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
                if event.e_type == 'MARKET':
                    strategy.calculate_signals(event)
                    port.update_timeindex(event)

                elif event.e_type == 'SIGNAL':
                    port.update_signal(event)

                elif event.e_type == 'ORDER':
                    broker.execute_order(event)

                elif event.e_type == 'FILL':
                    port.update_fill(event)
    # 10-Minute heartbeat
    # time.sleep(10*60)

port.create_equity_curve_dataframe()
print(port.equity_curve)
print(port.output_summary_stats())
