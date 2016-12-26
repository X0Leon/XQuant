# -*- coding: utf-8 -*-

"""
ExecutionHandler抽象基类/类
orders的执行，这里模拟交易所行为

@author: Leon Zhang
@version: 0.4
"""

# import datetime
# import queue

from abc import ABCMeta, abstractmethod

from .event import FillEvent
# from .event import OrderEvent
from .commission import ZeroCommission, PerShareCommission, PerMoneyCommission
from ..utils.symbol import get_exchange
from .slippage import ZeroSlippage, FixedPercentSlippage


class ExecutionHandler(object):
    """
    ExecutionHandler抽象基类，处理从Portfolio发来的订单，
    产生实际成交的Fill对象，即真实出现在市场中的成交
    继承的子类既可以是模拟的交易所，也可以是真正的实时交易API接口
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        """
        取一个Order事件并执行，产生Fill事件并放入Events队列
        参数：
        event: 包含order信息的事件
        """
        raise NotImplementedError("Should implement execute_order()!")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    简单的模拟交易所
    未考虑等待时间、滑点、部分成交等
    """
    def __init__(self, bars, events, slippage_type='fixed', commission_type='default'):
        """
        初始化
        参数：
        bars: DataHandler结果bars，为了对回测时成交价做模拟处理
        events: Event队列
        commission_type: 费率模型
        slippage_type: 滑点模型
        """
        self.bars = bars
        self.events = events
        self.commission_type = commission_type
        self.slippage_type = slippage_type
        self.commission = 0.0

    def _trade_with_slippage(self, event):
        """
        考虑滑点后的成交价
        """
        order_price = self.bars.get_latest_bars(event.symbol)[0][5]
        if self.slippage_type == 'zero':
            return ZeroSlippage().get_trade_price(order_price)

        elif self.slippage_type == 'fixed':
            fixed_slippage = FixedPercentSlippage(percent=0.1)
            return fixed_slippage.get_trade_price(order_price, event.direction)
        else:
            return order_price

    def _get_commission_commission(self, event):
        """
        计算股票或期货的手续费
        """
        self.fill_price = self._trade_with_slippage(event)
        full_cost = self.fill_price * event.quantity

        if self.commission_type == 'zero':
            commission = ZeroCommission().get_commission()

        elif self.commission_type == 'default':
            if event.symbol.startswith('6'):  # 上海交易所
                if event.direction == 'BUY':  # 买入：过户费1000股1元+佣金单向万3
                    commission = PerShareCommission(rate=0.0001, min_comm=1.0).get_commission(event.quantity) + \
                                 PerMoneyCommission(rate=3.0e-4, min_comm=5.0).get_commission(full_cost)
                else:  # 卖出：印花税+过户费+佣金
                    commission = PerMoneyCommission(rate=1.0e-3).get_commission(full_cost) + \
                                 PerShareCommission(rate=0.0001, min_comm=1.0).get_commission(event.quantity) + \
                                 PerMoneyCommission(rate=3.0e-4, min_comm=5.0).get_commission(full_cost)
            elif event.symbol.startswith(('0', '3')):  # 深圳交易所
                if event.direction == 'BUY':  # 买入：佣金
                    commission = PerMoneyCommission(rate=3.0e-4, min_comm=5.0).get_commission(full_cost)
                else:  # 卖出：印花税+佣金
                    commission = PerMoneyCommission(rate=1.0e-3).get_commission(full_cost) + \
                                 PerMoneyCommission(rate=3.0e-4, min_comm=5.0).get_commission(full_cost)
            elif event.symbol.startswith('I'):  # 股指期货，按照点数计算
                commission = PerMoneyCommission(rate=3.0e-5).get_commission(full_cost)
            elif get_exchange(event.symbol) in ('SQ.EX', 'DS.EX', 'ZS.EX'):  # 商品期货，按照点数计算
                commission = PerMoneyCommission(rate=1.5e-4).get_commission(full_cost)
            else:
                commission = 0.0
        else:
            commission = 0.0

        return commission

    def execute_order(self, event):
        """
        简单地将Order对象转变成Fill对象
        参数：
        event: 含有order信息的Event对象
        """
        if event.type == 'ORDER':
            self.commission = self._get_commission_commission(event)
            # assert type(self.commission) is float, 'Commission should be float'
            timeindex = self.bars.get_latest_bars(event.symbol)[0][1]  # 成交实际上发生在下一根K bar
            fill_event = FillEvent(timeindex, event.symbol, 'SimulatedExchange',
                                   event.quantity, event.direction, self.fill_price,
                                   self.commission)
            self.events.put(fill_event)
