# -*- coding: utf-8 -*-

"""
ExecutionHandler抽象基类/类
orders的执行，这里模拟交易所行为

目前只是简单地以当前市价成交所有orders
TODO: 可以大大扩展：如滑点，市场冲击等等

@author: X0Leon
@version: 0.2.0a
"""

# import datetime
# import queue

from abc import ABCMeta, abstractmethod

from .event import FillEvent
# from .event import OrderEvent


class ExecutionHandler(object):
    """
    ExecutionHandler抽象基类，处理从Portofio发来的订单，
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
        raise NotImplementedError("未实现excute_order()，此方法是必须的！")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    简单的模拟交易所
    未考虑等待时间、滑点、部分成交等
    """
    def __init__(self, bars, events, commission=None, slippage=None):
        """
        初始化
        参数：
        bars: DataHandler结果bars，为了对回测时成交价做模拟处理
        events: Event队列
        commission: 费率，若为None则通过_calculate_commission计算
        slippage: 滑点模型，待考虑（TODO：加入滑点）
        """
        self.bars = bars
        self.events = events
        self.commission  = commission
        self.slippage = slippage

    def _calculate_commission(self, event):
        """
        计算股票和期货的手续费
        股票代码，如'600008'；股指期货代码，如'IC1604*'
        采用非常简单（但弹性）的识别方式
        """
        commission = 0.0
        fill_cost = self.bars.get_latest_bars(event.symbol)[0][5]  # 成交价
        full_cost = fill_cost * event.quantity  # 成交额

        if event.symbol.startswith('6'):
            if event.direction == 'BUY':
                # 上海市场，买入：过户费+佣金
                commission = max(event.quantity/1000, 1.0) + max(5.0, 3/10000.0*full_cost)
            elif event.direction == 'SELL':
                # 上海市场，卖出：印花税+过户费+佣金
                commission = 1/1000.0*full_cost + max(event.quantity/1000, 1.0) + max(5.0, 3/10000.0*full_cost)
            else:
                pass
        elif event.symbol.startswith(('0', '3')):
            if event.direction == 'BUY':
                # 深圳市场，买入：佣金
                commission = max(5.0, 3/10000.0*full_cost)
            elif event.direction == 'SELL':
                # 深圳市场，卖出：印花税+佣金
                commission = 1/1000.0*full_cost + max(5.0, 3/10000.0*full_cost)
            else:
                pass
        elif event.symbol.startswith('I'):
            # 股指期货，暂时不考虑平今的高额收费情况
            commission = full_cost*300*0.3/10000
        else:
            pass

        return commission

    def execute_order(self, event):
        """
        简单地将Order对象转变成Fill对象
        参数：
        event: 含有order信息的Event对象
        """
        if self.commission is None:
            self.commission = self._calculate_commission(event)

        if event.type == 'ORDER':
            # 模拟设置成交价和手续费，暂时用k bar的close价
            # 如果考虑滑点、冲击成本等，可以update到下一根k bar的价格处理
            fill_cost = self.bars.get_latest_bars(event.symbol)[0][5]
            if event.symbol.startswith('I'): # 股指期货每点300元
                fill_cost = fill_cost * 300

            timeindex = self.bars.get_latest_bars(event.symbol)[0][1]
            fill_event = FillEvent(timeindex, event.symbol, 'SimulatorExchange',
                                   event.quantity, event.direction, fill_cost,
                                   commission=self.commission)
            self.events.put(fill_event)
