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
    def excute_order(self, event):
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
    def __init__(self, events):
        """
        初始化
        参数：
        events: Event队列
        """
        self.events = events

    def execute_order(self, event):
        """
        简单地将Order对象转变成Fill对象
        参数：
        event: 含有order信息的Event对象
        """
        if event.e_type == 'ORDER':
            fill_event = FillEvent(datetime.datetime.utcnow(), event.symbol,
                                    'SimulatorExchange', event.quantity, event.direction)
            # 由于我们在NaivePortfolio对象中已经处理成交成本，这里设为'None'
            # 倒数第二个参数为fill_cost，即成交价，简单设置为k bar的close
            # 实际交易中我们可以从账户中获得这一数据
            self.events.put(fill_event)