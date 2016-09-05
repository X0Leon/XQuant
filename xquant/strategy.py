# -*- coding: utf-8 -*-

"""
Strategy类
Strategy对象计算市场数据，产生signal给Portfolio对象
market data by DataHandler -> Strategy -> signal for Portfolio

@author: X0Leon
@version: 0.1

TODO:
    技术指标的加入，可以支持TA-lib
"""

import datetime
import numpy as np
import pandas as pd
import queue # Python 2.x为Queue，判断：is_py2 = sys.version[0] == '2'

from abc import ABCMeta, abstractmethod

from event import SignalEvent

class Strategy(object):
	"""
	Strategy抽象基类
	此类及其继承类通过对Bars(OLHCV)（由DataHandler对象生成）处理产生Signal对象
	Strategy类对历史数据和实时数据均有效，实际上它对数据来源不知晓，直接从queue对象获取bar元组
	"""
	__metaclass__ = ABCMeta

	@abstractmethod
	def calculate_signals(self):
		"""
		提供计算信号的机制
		"""
		raise NotImplementedError("未实现calculate_signals()，此方法是必须的！")


	# 一个例子：买入并持有的策略
	class BuyAndHoldStrategy(Strategy):
		"""
		最简单的例子：对所以股票持多头策略
		用于：测试代码；作为benchmark
		"""
		def __init__(self, bars, events):
			"""
			初始化买入持有策略
			参数：
			bars: DataHandler对象的数据
			events: Event queue对象
			"""
			self.bars = bars
			self.symbol_list = self.bars.symbol_list
			self.events = events

			self.bought = self._calcualte_initial_bought() # 字典

			def _calculate_initial_bought(self):
				"""
				添加key到bought字典，将所有股票的值设为False，意指尚未持有
				"""
				bought = {}
				for s in self.symbol_list:
					bought[s] = False
				return bought

			def calculate_signals(self, event):
				"""
				此策略对每只股票只产生一个信号，那就是买入
				从策略初始化的那个时间买入持有
				参数：
				event: MarketEvent对象
				"""
				if event.type = 'MARKET':
					for s in self.symbol_list:
						bars = self.bars.get_latest_bars(s, N=1)
						if bars is not None and bars != []:
							if self.bought[s] = False:
								# 格式(Symbol, Datetime, Type = LONG, SHORT or EXIT)
								signal = SignalEvent(bars[0][0], bars[0][1], 'LONG')
								self.events.put(signal)
								self.bought[s] = True




