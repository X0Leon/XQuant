# -*- coding: utf-8 -*-

"""
评估策略优劣的功能函数模块

@author: X0Leon
@version: 0.2.0a
"""

import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
    """
    计算策略夏普率，基准为0，未使用无风险利率信息
    参数：
    returns: pandas Series格式的每个bar周期的百分比收益
    periods: 一天的25,2，每小时的252*4，每分钟的为252*4*60
    """
    return np.sqrt(periods) * (np.mean(returns))/np.std(returns)

def create_drawdowns(pnl):
    """
    计算PnL曲线的最大回撤，以及持续时间
    pnl: pandas Series格式的百分比收益

    return: drawdown, duration
    """
    # 计算累计收益，记录最高收益（High Water Mark）
    hwm = [0] # 历史最大值序列

    idx = pnl.index
    drawdown = pd.Series(index=idx)
    duration = pd.Series(index=idx)

    for t in range(1, len(idx)):
        hwm.append(max(hwm[t-1], pnl[t]))
        drawdown[t] = hwm[t] - pnl[t]
        duration[t] = (0 if drawdown[t] == 0  else duration[t-1]+1)
    return drawdown, drawdown.max(), duration.max()
