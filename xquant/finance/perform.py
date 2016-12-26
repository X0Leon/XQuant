# -*- coding: utf-8 -*-

"""
评估策略优劣的功能函数模块

@author: Leon Zhang
@version: 0.4
"""

import numpy as np
import pandas as pd


# def create_equity_curve(total_series):
#     """
#     计算资金曲线
#     参数：
#     portfolio对象中all_holdings的DataFrame
#     展示profit and loss (PnL)
#     """
#     curve = total_series.to_frame('total')
#     curve['returns'] = curve['total'].pct_change()  # 计算百分比变化
#     curve['equity_curve'] = (1.0 + curve['returns']).cumprod()  # 计算累计值
#     return curve
#
# def create_sharpe_ratio(returns, periods=252):
#     """
#     计算策略夏普率，基准为0，未使用无风险利率信息
#     参数：
#     returns: pandas Series格式的每个bar周期的百分比收益
#     periods: 一天的252，每小时的252*4，每分钟的为252*4*60
#     """
#     return np.sqrt(periods) * (np.mean(returns))/np.std(returns)
#
# def create_drawdowns(equity_curve):
#     """
#     计算PnL曲线的最大回撤，以及持续时间
#     参数：
#     equity_curve: 资金曲线的Series
#
#     return: drawdown, duration
#     Ref: http://stackoverflow.com/questions/22607324/start-end-and-duration-of-maximum-drawdown-in-python
#     """
#     # 计算累计收益，记录最高收益（High Water Mark）
#     df = equity_curve.to_frame('equity_curve')
#     df['cum_max'] = df['equity_curve'].cummax()
#     df['dd'] = df['cum_max'] / df['equity_curve'] - 1  #
#     i = df['dd'].index.get_loc(df['dd'].idxmax())  # 获取回撤周期的结束row序号
#     j = df['dd'].index.get_loc(df['equity_curve'].iloc[:i].idxmax())  # 回撤开始的row
#
#     return df['dd'], df['dd'].iloc[-1], i-j
#
# def create_drawdowns_slow(pnl):
#     """
#     非矢量化计算最大回撤，计算速度慢
#     pnl: pandas Series格式的百分比收益
#     """
#     # 计算累计收益，记录最高收益（High Water Mark）
#     hwm = [0] # 历史最大值序列
#
#     idx = pnl.index
#     drawdown = pd.Series(index=idx)
#     duration = pd.Series(index=idx)
#
#     for t in range(1, len(idx)):
#         hwm.append(max(hwm[t-1], pnl[t]))
#         drawdown[t] = hwm[t] - pnl[t]
#         duration[t] = (0 if drawdown[t] == 0  else duration[t-1]+1)
#     return drawdown, drawdown.max(), duration.max()


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
    ret = perform['equity_curve'][-1] - 1  # 回测期间收益率
    sharpe_ratio = np.sqrt(periods) * np.mean(perform['return']) / np.std(perform['return'])  # 夏普率

    perform['cum_max'] = perform['equity_curve'].cummax()
    perform['drawdown'] = perform['equity_curve'] / perform['cum_max'] - 1  # 回撤向量
    max_dd = perform['drawdown'].min()  # 最大回撤

    # i = holdings['drawdown'].index.get_loc(holdings['drawdown'].idxmax())  # 获取回撤周期的结束row序号
    # j = holdings['dd'].index.get_loc(holdings['equity_curve'].iloc[:i].idxmax())  # 回撤开始的row

    return perform, ret, sharpe_ratio, max_dd


def detail_blotter(backtest, positions, holdings, mode='simplified'):
    """
    分品种获取详细交易状况，合并市场数据、交易情况和账户变动
    参数：
    backtest, positions, holdings为回测引擎返回的变量
    mode: 'simplified'则市场行情数据只保留'close'列
    （DataFrame的字典）
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
        else:  # 'full'
            data = data.set_index('datetime')

        trades_symb = trades[trades['symbol']==symb][['direction','fill_price', 'commission', 'cost']]
        holdings_symb = pd.Series(holdings[symb], name='holdings')
        positions_symb = pd.Series(positions[symb], name='positions')
        merge = data.join([positions_symb, holdings_symb, trades_symb], how='outer').iloc[1:, :].fillna(0.)
        # 计算每根bar结束后的盈亏
        merge['pnl'] = merge['holdings'] - merge['holdings'].shift(1) - merge['cost'].shift(1) - \
                       merge['commission'].shift(1)
        merge.ix[0, 'pnl'] = 0.  # NaN
        # 回测结束时对可能存在的强制平仓进行额外计算
        merge.ix[-1, 'pnl'] = merge['holdings'].iloc[-1] - merge['holdings'].iloc[-2] - merge['cost'].iloc[-1] - \
                              merge['commission'].iloc[-1]
        # 以回测第一根bar收盘价作为起始资本
        merge['adj_total'] = merge['pnl'].cumsum() + merge['close'].iloc[0]
        del merge['cost']
        blotter[symb] = merge

    return blotter
