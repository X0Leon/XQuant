# -*- coding: utf-8 -*-

"""
Portfolio抽象基类/类
头寸跟踪、订单管理，可以进一步做收益分析、风险管理等

@author: Leon Zhang
"""

from abc import ABCMeta, abstractmethod
from .event import OrderEvent


class Portfolio(object):
    """
    Portfolio类处理头寸和持仓市值
    目前以Bar来计算，可以是秒、分钟、5分钟、30分钟、60分钟等的K线
    考虑支持Tick?
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def update_signal(self, event):
        """
        基于portfolio的管理逻辑，使用SignalEvent产生新的orders
        """
        raise NotImplementedError("Should implement update_signal()!")

    @abstractmethod
    def update_fill(self, event):
        """
        从FillEvent中更新组合当前的头寸和持仓市值
        """
        raise NotImplementedError("Should implement update_fill()!")


class BasicPortfolio(Portfolio):
    """
    BasicPortfolio发送orders给brokerage对象，这里简单地使用固定的数量，
    不进行任何风险管理或仓位管理（这是不现实的！），仅供测试使用
    """
    def __init__(self, bars, events, start_date, initial_capital=1.0e5):
        """
        使用bars和event队列初始化portfolio，同时包含起始时间和初始资本
        参数：
        bars: DataHandler对象，使用当前市场数据
        events: Event queue对象
        start_date: 组合起始的时间
        initial_capital: 起始的资本
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.current_datetime = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = {s:0 for s in self.symbol_list}

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

        self.all_trades = []

    def construct_all_positions(self):
        """
        构建头寸列表，其元素为通过字典解析产生的字典，每个symbol键的值为零
        且额外加入了datetime键
        """
        d = {s:0 for s in self.symbol_list}
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        """
        构建全部持仓市值
        包括现金、累计费率和合计值的键
        """
        d = {s:0 for s in self.symbol_list}
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
        d = {s:0 for s in self.symbol_list}
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self):
        """
        用于追踪新的持仓市值
        向持仓头寸中加入新的纪录，也就是刚结束的这根完整k bar，bar的时间理解成endTime
        从events队列中使用BarEvent
        """
        bars = {}

        for sym in self.symbol_list:
            bars[sym] = self.bars.get_latest_bars(sym, N=1)

        self.current_datetime = bars[self.symbol_list[0]][0][1]

        dp = {s:0 for s in self.symbol_list}
        dp['datetime'] = self.current_datetime


        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        self.all_positions.append(dp)

        dh = {s:0 for s in self.symbol_list}
        dh['datetime'] = self.current_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        for s in self.symbol_list:
            market_value = self.current_positions[s] * bars[s][0][5]
            dh[s] = market_value
            dh['total'] += market_value

        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
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

        self.current_positions[fill.symbol] += fill_dir * fill.quantity

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

        fill_price = fill.fill_price
        cost = fill_dir * fill_price * fill.quantity

        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= fill.commission

    def update_trades_from_fill(self, fill):
        """
        从FillEvent对象中读取全部数据作为交易记录
        参数：
        fill: FillEvent对象
        """
        current_trade = {}
        current_trade['datetime'] = fill.timeindex
        current_trade['symbol'] = fill.symbol
        current_trade['exchange'] = fill.exchange
        current_trade['quantity'] = fill.quantity
        current_trade['direction'] = fill.direction
        current_trade['fill_price'] = fill.fill_price
        current_trade['commission'] = fill.commission

        self.all_trades.append(current_trade)

    def update_fill(self, event):
        """
        从FillEvent中更新组合的头寸和市值
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
            self.update_trades_from_fill(event)

    def generate_naive_order(self, signal):
        """
        此函数未采取风险管理和仓位控制，实际流程应该是信号->风险控制->下单指令
        """
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength
        
        order_type = 'MKT'
        target_holdings = self.current_holdings['total'] * strength * (1 if direction=='LONG' else -1)
        cur_holdings = self.current_holdings[symbol]
        cur_quantity = self.current_positions[symbol]
        delta_holdings = target_holdings - cur_holdings
        price = self.bars.get_latest_bar(symbol).close
        
        if symbol.startswith(('0', '3', '6')):
            mkt_quantity = ((delta_holdings / price) // 100) * 100
        else:
            mkt_quantity = delta_holdings // price

        if direction == 'LONG':
            order = OrderEvent(symbol, order_type, abs(mkt_quantity), 'BUY' if mkt_quantity>0 else 'SELL')
        elif direction == 'SHORT':
            order = OrderEvent(symbol, order_type, abs(mkt_quantity), 'SELL' if mkt_quantity<0 else 'BUY')
        elif direction == 'EXIT':
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL' if cur_quantity>0 else 'BUY')
        else:
            raise ValueError('Unknown direction type: %s' % direction)

        return order

    def update_signal(self, event):
        """
        基于组合管理的逻辑，通过SignalEvent对象来产生新的orders
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)
