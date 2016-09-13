# -*- coding: utf-8 -*-

"""
Event类，在数据、组合、交易所（或模拟交易所）间流动的事件

@author: X0Leon
@version: 0.2.0a
"""


class Event(object):
    """
    Event类是基类
    供子类（Market, Signal, Order, Fill）继承
    事件类是event-driven型回测框架的核心
    """
    pass


class MarketEvent(Event):
    """
    Market事件类
    """
    def __init__(self):
        """
        初始化
        """
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    Signal事件类
    处理：从Strategy对象发送Signal，由下游的Portfolio对象接受
    """

    def __init__(self, symbol, datetime, signal_type, strategy_id=1, strength=1.0):
        """
        初始化SignalEvent对象
        参数：
        symbol: 股票代号字符串，统一使用名称或者数字字符串中的一种
        datetime：signal产生的时间戳
        signal_type: 多头('LONG')、空头('SHORT')、平仓('EXIT')
        strategy_id: 策略的独特id，可以多策略并行
        strength: 用于给出交易数量的建议的信号强度，例如配对交易
        """
        self.type =  'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strategy_id = strategy_id
        self.strength = strength


class OrderEvent(Event):
    """
    Order事件类
    处理：发送一个Order给执行（execution）系统，
    其包含：symbol, type (market or limit, 即市价委托还是限价委托), quantity, direction
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        初始化OrderEvent对象
        设定市价委托('MKT')或者限价委托('LMT')，交易数量（整数），交易方向('BUY'或'SELL')
        参数：
        symbol: 交易的股票
        order_type: 'MKT' or 'LMT'
        quantity: 非负整数
        direction: 'BUY' or 'SELL'
        """
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        输出Order中的值
        """
        print("Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s" %
            (self.symbol, self.order_type,self.quantity, self.direction))


class FillEvent(Event):
    """
    Fill事件类
    Fill or Kill (FOK)指令，全部成交否则取消 [选用，符合A股吗？]
    [注：另一种是立即成交否则取消指令(Immediate or Cancel, IOC) ]
    存储实际成交的成交量和价格，以及佣金
    """
    def __init__(self, timeindex, symbol, exchange, quantity, direction,
                 fill_cost, commission):
        """
        初始化FillEvent对象，设定好参数
        如果费率没有提供，按照券商佣金万3来
        参数：
        timeindex: 成交时的bar，其实就是成交的那根k线
        symbol: 成交的交易代码
        exchange: 成交的交易所(exchange)
        quantity: 成交数量
        direction: 成交的方向
        fill_cost：成交价
        commission：费率
        """
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.commission = commission