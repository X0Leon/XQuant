# -*- coding: utf-8 -*-

"""
Portfolio抽象基类/类
头寸跟踪、订单管理、风险/收益分析等

@author: X0Leon
@version: 0.2.0a
"""

# import datetime
# import numpy as np
import pandas as pd
# import queue

from abc import ABCMeta, abstractmethod
# from math import floor # 返回下舍整数值

from .event import OrderEvent
from .performance import create_sharpe_ratio, create_drawdowns


class Portfolio(object):
    """
    Portfolio类处理头寸和持仓市值
    基本bar来计算，可以是秒、分钟、5分钟、30分钟、60分钟等的K线
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def update_signal(self, event):
        """
        基于portfolio的管理逻辑，使用SignalEvent产生新的orders
        """
        raise NotImplementedError("未实现update_signal()，此方法是必须的！")

    @abstractmethod
    def update_fill(self, event):
        """
        从FillEvent中更新组合当前的头寸和持仓市值
        """
        raise NotImplementedError("未实现update_fill()，此方法是必须的！")


# 一个基础的组合订单管理的类
class BasicPortfolio(Portfolio):
    """
    NaivePortfolio发送orders给brokerage对象，这里简单地使用固定的数量，
    不进行任何风险管理或仓位管理（这是不现实的！），仅供测试使用
    """
    def __init__(self, bars, events, start_date, initial_capital=1.0e5, periods=252):
        """
        使用bars和event队列初始化portfolio，同时包含其实时间和初始资本
        参数：
        bars: DataHandler对象，使用当前市场数据
        events: Event queue对象
        start_date: 组合其实的时间，实际上就是指某个k线
        initial_capital: 起始的资本
        periods: 交易周期数，日频数据为252, 60分钟为252*4, 1分钟为252*4*60，用于计算年化收益
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        self.periods = periods

        self.all_positions = self.construct_all_positions()  # 字典列表
        self.current_positions = dict((k,v) for k,v in [(s,0) for s in self.symbol_list]) # 字典

        self.all_holdings = self.construct_all_holdings()  # 字典列表
        self.current_holdings = self.construct_current_holdings()  # 字典

    def construct_all_positions(self):
        """
        构建头寸列表，其元素为通过字典解析产生的字典，每个symbol键的值为零
        且额外加入了datetime键
        """
        d = dict((k,v) for k,v in [(s,0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        """
        构建全部持仓市值
        包括现金、累计费率和合计值的键
        """
        d = dict((k,v) for k,v in [(s,0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        """
        构建当前持仓市值
        和construct_all_holdings()唯一不同的是返回字典，而非字典的列表
        """
        d = dict((k,v) for k,v in [(s,0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    # 市场发生交易，我们需要更新持仓市值
    def update_timeindex(self, event):
        """
        用于追踪新的持仓市值
        向持仓头寸中加入新的纪录，也就是刚结束的这根完整k bar
        从events队列中使用MarketEvent
        """
        bars = {}
        for sym in self.symbol_list:
            bars[sym] = self.bars.get_latest_bars(sym, N=1)
        # 更新头寸，字典
        dp = dict((k,v) for k,v in [(s,0) for s in self.symbol_list])
        dp['datetime'] = bars[self.symbol_list[0]][0][1]

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        # 添加当前头寸
        self.all_positions.append(dp)  # 注意all_positions是k bar周期的字典列表
        # 更新持仓，字典
        dh = dict((k,v) for k,v in [(s,0) for s in self.symbol_list])
        dh['datetime'] = bars[self.symbol_list[0]][0][1]
        dh['cash'] =  self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['total']

        for s in self.symbol_list:
            # 估计持仓市值
            market_value = self.current_positions[s] * bars[s][0][5]
            dh[s] = market_value
            dh['total'] += market_value

        self.all_holdings.append(dh)

    # (1) 与FillEvent对象交互: 通过两个工具函数来实现Portfolio抽象基类的update_fill()

    def update_position_from_fill(self, fill):
        """
        从FillEvent对象中读取数据以更新头寸position
        参数：
        fill: FillEvent对象
        """
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        self.current_positions[fill.symbol] += fill_dir*fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        从FillEvent对象中读取数据以更新头寸市值 (holdings value)
        参数：
        fill: FillEvent对象
        """
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # fill_cost = self.bars.get_latest_bars(fill.symbol)[0][5] # close price
        fill_cost = fill.fill_cost  # 成交价通过模拟交易所发回的Fill事件中读取
        cost = fill_dir * fill_cost * fill.quantity

        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        """
        从FillEvent中更新组合的头寸和市值，实现
        """
        if event.type == 'FILL':
            self.update_position_from_fill(event)
            self.update_holdings_from_fill(event)

    # (2) 与SignalEvent对象交互: 通过一个工具函数来实现Portfolio抽象基类的update_signal()

    def generate_naive_order(self, signal):
        """
        简单地将signal对象乘以固定的数量作为OrderEvent对象，
        此函数不采取任何风险管理和仓位控制
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        # strength = signal.strength
        # mkt_quantity = floor(100 * strength)
        if symbol.startswith(('0', '3', '6')):
            mkt_quantity = 1000  # 股票10手
        else:
            mkt_quantity = 1  # 期货1手

        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG' and cur_quantity == 0: 
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')  # 开多仓
        elif direction == 'LONG' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, 2*mkt_quantity, 'BUY')  # 空翻多
        elif direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')  # 开空仓
        elif direction == 'SHORT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, 2*mkt_quantity, 'SELL')  # 多翻空
        elif direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        elif direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        else:
            pass

        return order

    def update_signal(self, event):
        """
        基于组合管理的逻辑，通过SignalEvent对象来产生新的orders
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    # ====================================
    # 股票曲线的功能函数，用于performance的计算
    # ====================================
    def create_equity_curve_dataframe(self):
        """
        从all_holdings的字典列表中生成pandas的DataFrame
        展示profit and loss (PnL)
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)  # 就地修改，不生成新对象
        curve['returns'] = curve['total'].pct_change()  # 计算百分比变化
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()  # 计算累计值
        self.equity_curve = curve

    def output_summary_stats(self):
        """
        生成组合的一些统计信息
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns, periods=self.periods)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]

        # self.equity_curve.to_csv('equity.csv')
        return stats

