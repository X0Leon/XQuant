# -*- coding: utf-8 -*-

"""
评估策略优劣的功能函数模块

@author: X0Leon
@version: 0.4
"""

import numpy as np
import pandas as pd


# def create_equity_curve_dataframe(holdings):
#     """
#     计算资金曲线
#     参数：
#     portfolio对象中all_holdings的DataFrame
#     展示profit and loss (PnL)
#     """
#     curve = holdings
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
# def create_drawdowns(holdings):
#     """
#     计算PnL曲线的最大回撤，以及持续时间
#     holdings为持仓情况
#
#     return: drawdown, duration
#     Ref: http://stackoverflow.com/questions/22607324/start-end-and-duration-of-maximum-drawdown-in-python
#     """
#     # 计算累计收益，记录最高收益（High Water Mark）
#     df = holdings
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
#
# def output_summary_stats(curve):
#     """
#     利用portfolio对象生成组合的一些统计信息
#     参数：
#     curve: 已计算equity_curve的DataFrame
#     """
#     total_return = curve['equity_curve'][-1]
#     returns = curve['returns']
#     pnl = curve['equity_curve']
#
#     sharpe_ratio = create_sharpe_ratio(returns, periods=252)
#     drawdown, max_dd, dd_duration = create_drawdowns(pnl)
#     curve['drawdown'] = drawdown
#
#     stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
#              ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
#              ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
#              ("Drawdown Duration", "%d" % dd_duration)]
#
#     # curve.to_csv('equity.csv')
#     return stats


def perform_metrics(total_series, periods=252):
    """
    资金曲线，夏普率和最大回撤的计算
    参数：
    total_series为账户资金的Series
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
    分品种获取详细交易状况（DataFrame的字典）
    合并市场数据、交易情况和账户变动
    如果mode为'simplified'，则市场数据只保留close列
    示例：
    blotter = detail_blotter(backtest, positions, holdings)
    blotter_rb = blotter['RB']
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
        merge['pnl'].iloc[0] = 0.  # NaN
        # 回测结束时对可能存在的强制平仓进行额外计算
        merge['pnl'].iloc[-1] = merge['holdings'].iloc[-1] - merge['holdings'].iloc[-2] - merge['cost'].iloc[-1] - \
                                merge['commission'].iloc[-1]
        # 以回测第一根bar收盘价作为起始资本
        merge['adj_total'] = merge['pnl'].cumsum() + merge['close'].iloc[0]
        del merge['cost']
        blotter[symb] = merge

    return blotter
