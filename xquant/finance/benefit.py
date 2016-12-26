# -*- coding: utf-8 -*-

"""
评估策略规则的优势率

@author: Leon Zhang
@version: 0.4
"""

import numpy as np
import pandas as pd


def entry(df, n=30):
    """
    入场规则优势率，返回结果为做多方向，做空取倒数
    参数：
    df: DataFrame，至少包含'entry', 'close','ATR' 三列
    n: 入场后观察窗口
    """
    rows_n = len(df)
    entry_rise = []
    entry_fall = []
    for i in range(rows_n):
        if df.iloc[i]['entry'] != 0 and df.iloc[i]['entry'] is not np.nan:
            max_rise = df.iloc[i+1:max(i+n+1, rows_n)]['close'].max()
            max_fall = df.iloc[i+1:max(i+n+1, rows_n)]['close'].min()
            adjust_rise = max_rise/df.iloc[i]['ATR']
            adjust_fall = max_fall/df.iat[i]['ATR']
            entry_rise.append(adjust_rise)
            entry_fall.append(adjust_fall)

    return np.mean(entry_rise)/np.mean(entry_fall)


def win_loss():
    pass
