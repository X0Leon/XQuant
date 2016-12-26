# -*- coding: utf-8 -*-

"""
Monte Carlo模拟另类历史回测

@author: Leon Zhang
@version: 0.4
"""

import numpy as np


def reorder(a, chunks=1):
    """
    重新排序组合
    参数：
    a: 一维序列，例如每天的收益率(return/PnL)
    chunks: 分块数，例如周数或月数
    返回：
    重排后的序列
    """
    a = np.array_split(a, chunks)
    np.random.shuffle(a)
    a = np.concatenate(a)
    return a


def resample(a, chunks=1):
    """
    有放回的随机抽样，如果a长度不能被chunks整除，则自动取1
    参数：
    a: 一维序列，例如每天的收益率
    chunks: 分块数，要求a长度可以被其整分
    返回：
    重新随机生成的序列
    """
    try:
        a = np.split(a, chunks)
        index = np.random.choice(range(chunks), size=chunks)
        a = np.concatenate([a[i] for i in index])
    except:
        a = np.random.choice(a, size=len(a))
    return a


def monte_carlo(a, chunks=1, times=20, shuffle_type='reorder'):
    """
    蒙特卡洛模拟对序列a进行重新抽样组合
    参数：
    a: 一维序列
    chunks: 分块数，type='resample'时应该要求len(a)可以整除chunks
    times: 模拟的次数
    type: 'reorder'或‘resample'分别为无放回和有放回抽样
    返回：
    所有随机序列的list
    """
    if shuffle_type == 'reorder':
        shuffle = reorder
    elif shuffle_type == 'resample':
        shuffle = resample
    else:
        return None

    list_a = []
    for _ in range(times):
        list_a.append(shuffle(a, chunks=chunks))

    return list_a


if __name__ == '__main__':
    # 示例
    import matplotlib.pyplot as plt

    ret = (np.random.randn(100) + 0.1) / 100
    equity_curve = (1 + ret).cumprod()
    plt.plot(equity_curve, color='blue')
    generated_ret = monte_carlo(ret, chunks=20)

    for ret in generated_ret:
        curve = (1 + ret).cumprod()
        plt.plot(curve, color='grey', alpha=0.5)