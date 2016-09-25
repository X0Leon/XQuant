# -*- coding: utf-8 -*-

"""
日期时间相关的功能函数模块

@author: X0Leon
@version: 0.3.1
"""

import datetime

def is_third_friday(dt):
    """
    判断是否为第三个周五（股指期货交割日，节假日除外）
    参数：
    dt: datetime格式的数据

    示例：dt = datetime.datetime(2015, 4, 5)
    """
    return dt.weekday() == 4 and 14 < dt.day < 22