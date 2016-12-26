# -*- coding: utf-8 -*-

"""
Slippage 滑点模型
New in V0.3.4

@author: Leon Zhang
@version: 0.4
"""

from abc import ABCMeta, abstractmethod


class Slippage(object):
    """
    滑点模型
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_trade_price(self):
        raise NotImplementedError("Should implement get_trade_price()!")


class ZeroSlippage(Slippage):
    """
    无滑点
    """
    def get_trade_price(self, price):
        return price


class FixedPercentSlippage(Slippage):
    """
    固定比率的滑点模型
    """
    def __init__(self, percent=0.1):
        """
        参数
        rate: 滑点比率，如0.1，则买卖方向上各滑点0.1%
        """
        self.rate = percent / 100.0

    def get_trade_price(self, price, direction):
        slippage = price * self.rate * (1 if direction == "BUY" else -1)
        price = price + slippage

        return price


class VolumeShareSlippage(Slippage):
    def get_trade_price(self, price, direction):
        pass