# -*- coding: utf-8 -*-

"""
file 2
DataHandler抽象基类
数据处理不区分历史数据还是实时数据

@author: X0Leon
@version: 0.1
"""

import datetime
import os, os.path
import pandas as pandas

from abc import ABCMeta, abstractmethod

from event import MarketEvent

class DataHandler(object):
	pass
