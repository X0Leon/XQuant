# -*- coding: utf-8 -*-

"""
评估策略优劣的功能函数模块

@author: Leon Zhang
"""

import numpy as np
import pandas as pd


def perform_metrics(total_series, periods=252):
    """
    资金曲线，夏普率和最大回撤的计算
    
    参数：
    total_series：账户资金的Series
    periods：回测时间尺度，默认为天，用于计算年化夏普率
    
    返回：
    perform, ret, sharpe_ratio, max_dd的元组
    """
    perform = total_series.to_frame('total')
    perform['return'] = perform['total'].pct_change()
    perform['equity_curve'] = (1.0 + perform['return']).cumprod()
    ret = perform['equity_curve'][-1] - 1                                                     # 回测期间收益率
    sharpe_ratio = np.sqrt(periods) * np.mean(perform['return']) / np.std(perform['return'])  # 夏普率

    perform['cum_max'] = perform['equity_curve'].cummax()
    perform['drawdown'] = perform['equity_curve'] / perform['cum_max'] - 1                    # 回撤向量
    max_dd = perform['drawdown'].min()                                                        # 最大回撤

    return perform, ret, sharpe_ratio, max_dd


def detail_blotter(backtest, positions, holdings, mode='simplified'):
    """
    分品种获取详细交易状况，合并市场数据、交易情况和账户变动
    
    参数：
    backtest, positions, holdings为回测引擎返回的变量
    mode: 'simplified'则市场行情数据只保留'close'列（DataFrame的字典）
    
    返回：
    字典，键为symbol，值为DataFrame格式

    示例：
    blotter = detail_blotter(backtest, positions, holdings)
    blotter_rb = blotter['RB']
    blotter_br.head()
    """
    blotter = dict()
    data_dict = backtest.data_handler.latest_symbol_data
    trades = backtest.trade_record()
    trades['direction'] = [1 if d=='BUY' else -1 for d in trades['direction']]
    trades['cost'] = trades['direction'] * trades['fill_price'] * trades['quantity']
    for symb in data_dict.keys():
        data = pd.DataFrame(data_dict[symb], columns=['symbol', 'datetime', 'open', 'high', 'low',
                                                      'close', 'volume'])
        if mode == 'simplified':
            data = data[['datetime', 'close']].set_index('datetime')
        elif mode == 'completed':
            data = data.set_index('datetime')
        else:
            raise ValueError('Unknown value - %s for mode' % mode)

        trades_symb = trades[trades['symbol']==symb][['direction','fill_price', 'commission', 'cost']]
        holdings_symb = pd.Series(holdings[symb], name='holdings')
        positions_symb = pd.Series(positions[symb], name='positions')
        merge = data.join([positions_symb, holdings_symb, trades_symb], how='outer').iloc[1:, :].fillna(0.)

        merge['pnl'] = merge['holdings'] - merge['holdings'].shift(1) - \
                       merge['cost'].shift(1) - merge['commission'].shift(1)                     # 每根bar结束后盈亏
        merge.ix[0, 'pnl'] = 0.                                                                  # NaN
        merge.ix[-1, 'pnl'] = merge['holdings'].iloc[-1] - merge['holdings'].iloc[-2] - \
                              merge['cost'].iloc[-1] - merge['commission'].iloc[-1]              # 回测结束时强制平仓
        del merge['cost']
        blotter[symb] = merge
    
    if len(data_dict.keys()) == 1:
        return blotter[symb]

    return blotter
