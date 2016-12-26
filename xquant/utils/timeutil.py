# -*- coding: utf-8 -*-

"""
日期时间相关的功能函数模块

@author: Leon Zhang
@version: 0.3.1
"""

import datetime
from functools import lru_cache
import requests


def is_third_friday(dt):
    """
    判断是否为第三个周五（股指期货交割日，节假日除外）
    参数：
    dt: datetime格式的数据

    示例：dt = datetime.datetime(2015, 4, 5)
    """
    return dt.weekday() == 4 and 14 < dt.day < 22


@lru_cache()
def is_holiday(day):
    """
    判断是否节假日
    参数：
    day: 日期， 格式为 '20160404'
    return: bool
    """
    api = 'http://www.easybots.cn/api/holiday.php'
    params = {'d': day}
    rep = requests.get(api, params)
    res = rep.json()[day if isinstance(day, str) else day[0]]
    return True if res == "1" else False


def is_holiday_today():
    """
    判断今天是否时节假日
    return: bool
    """
    today = datetime.date.today().strftime('%Y%m%d')
    return is_holiday(today)
