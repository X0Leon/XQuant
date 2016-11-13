# -*- coding: utf-8 -*-

"""
Commission 佣金+费税模型
New in V0.3.4
思路参考：https://github.com/quantopian/zipline/blob/master/zipline/finance/commission.py

@author: X0Leon
@version: 0.3.4
"""

from abc import ABCMeta, abstractmethod


class Commission(object):
    """
    滑点模型
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_commission(self):
        raise NotImplementedError("未实现get_commission()，此方法是必须的！")


class PerShareCommission(Commission):
    pass


class PerTradeCommission(Commission):
    pass


class PerCostCommission(Commission):
    pass