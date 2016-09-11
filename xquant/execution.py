# -*- coding: utf-8 -*-

"""
ExecutionHandler抽象基类/类
orders的执行，这里模拟交易所行为

目前只是简单地以当前市价成交所有orders
TODO: 可以大大扩展：如滑点，市场冲击等等

@author: X0Leon
@version: 0.1
"""

import datetime
import queue

from abc import ABCMeta, abstractmethod

from event import FillEvent, OrderEvent


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
    def __init__(self, bars, events):
        """
        初始化
        参数：
        bars: DataHandler结果bars，为了对回测时成交价做模拟处理
        events: Event队列
        """
        self.bars = bars
        self.events = events

    def execute_order(self, event):
        """
        简单地将Order对象转变成Fill对象
        参数：
        event: 含有order信息的Event对象
        """
        if event.e_type == 'ORDER':
            # 模拟设置成交价和手续费，暂时用k bar的close价
            # 如果考虑滑点、冲击成本等，可以update到下一根k bar的价格处理
            fill_cost = self.bars.get_latest_bars(event.symbol)[0][5]
            commission = 0.0

            if event.direction == 'BUY':
                commission = max(5.0, 3 / 10000.0 * event.quantity * fill_cost)
            elif event.direction == 'SELL':
                full_cost = event.quantity * fill_cost * 1 / 1000.0 \
                            + max(5.0, 3 / 10000.0 * event.quantity * event.fill_cost)
            else:
                pass


            timeindex = self.bars.get_latest_bars(event.symbol)[0][1]

            fill_event = FillEvent(timeindex, event.symbol, 'SimulatorExchange',
                                   event.quantity, event.direction, fill_cost,
                                   commission = commission)

            self.events.put(fill_event)