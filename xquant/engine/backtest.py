# -*- coding: utf-8 -*-

"""
回测的主要接口

@author: X0Leon
@version: 0.3.0
"""

# import datetime
# import time
import pandas as pd
try:
    import queue
except ImportError:  # 兼容python 2.7
    import Queue as queue


class Backtest(object):
    """
    封装回测设置和模块的接口
    """
    def __init__(self, csv_dir, symbol_list, initial_capital,
                 heartbeat, start_date, data_handler,
                 execution_handler, portfolio, strategy,
                 commission=None, slippage=None, log='silence', **params):
        """
        初始化回测
        csv_dir: CSV数据文件夹目录
        symbol_list: 股票代码str的list，如'600008'
        initial_capital: 初始资金，如10000.0
        heartbeat: k bar周期，以秒计，如分钟线为60，模拟交易使用
        start_date: 策略回测起始时间
        data_handler: (Class) 处理市场数据的类
        execution_handler: (Class) 处理order/fill的类
        portfolio: (Class) 虚拟账户，追踪组合头寸等信息的类
        strategy: (Class) 根据市场数据生成信号的策略类
        commission: 交易费率供模拟交易所使用：如为None则自行计算；如暂不考虑，请设置为0
        slippage: 滑点，待加入
        log: 日志flag
        params: 策略参数的字典
        """
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date

        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy

        self.commission = commission
        self.slippage = slippage
        self.log = log

        self.events = queue.Queue()

        self.params = params

        self.signals = 0
        self.orders = 0
        self.fills = 0

        self._generate_trading_instances()

    def _generate_trading_instances(self):
        """
        实例化类，得到data_handler(bars),strategy,portfolio(port),execution_handler(broker)对象
        """
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events, **self.params)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date,
                                            self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.data_handler, self.events,
                                                            commission=self.commission,
                                                            slippage=self.slippage)

    def _run_backtest(self):
        """
        执行回测
        """
        while True:
            # 更新k bar
            bars = self.data_handler
            if bars.continue_backtest:
                bars.update_bars()
            else:
                break

            # 处理events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)

                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)

                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)

            # time.sleep(self.heartbeat)

    def _output_performance(self):
        """
        输出策略的回测结果，待添加
        """
        print('生成回测结果...')
        print('策略产生交易信号数: %s' % self.signals)
        print('组合产生委托订单数: %s' % self.orders)
        print('回测交易成交订单数: %s' % self.fills)

    def simulate_trading(self):
        """
        模拟回测并输出结果，返回资金曲线和头寸的DataFrame
        """
        self._run_backtest()
        if self.log != 'silence':
            self._output_performance()

        positions = pd.DataFrame(self.portfolio.all_positions).set_index('datetime')
        holdings = pd.DataFrame(self.portfolio.all_holdings).set_index('datetime')
        return positions, holdings
