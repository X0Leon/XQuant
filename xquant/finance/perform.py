# -*- coding: utf-8 -*-

"""
评估策略优劣的功能函数模块

@author: X0Leon
@version: 0.3.0
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


def perform_metrics(holdings, periods=252):
    """
    资金曲线，夏普率和最大回撤的计算
    参数：
    holdings为Backtest返回的持仓DataFrame，含投资品种市值、cash、commission、total四列
    默认是日间报告，如果是日内策略，需要resample('D', how={})，或者修改periods
    """
    holdings['return'] = holdings['total'].pct_change()
    holdings['equity_curve'] = (1.0 + holdings['return']).cumprod()
    ret = holdings['equity_curve'][-1] - 1  # 回测期间收益率
    SR = np.sqrt(periods) * np.mean(holdings['return']) / np.std(holdings['return'])  # 夏普率

    holdings['cum_max'] = holdings['equity_curve'].cummax()
    holdings['drawdown'] = holdings['equity_curve'] / holdings['cum_max'] - 1  # 回撤向量
    max_dd = holdings['drawdown'].min()  # 最大回撤

    # i = holdings['drawdown'].index.get_loc(holdings['drawdown'].idxmax())  # 获取回撤周期的结束row序号
    # j = holdings['dd'].index.get_loc(holdings['equity_curve'].iloc[:i].idxmax())  # 回撤开始的row

    return holdings, ret, SR, max_dd


def detail_blotter(backtest, positions, holdings):
    """
    获取详细交割单
    参数：
    backtest, positions和holdings为回测后得到的对象
    返回：
    字典：键为symbol，值为行情数据和详细交割单合并后的DataFrame

    示例：
    detail_orders = detail_orders(backtest, positions, holdings)['RB']
    使用pandas自带的可视化，
        detail_orders['RB'].plot.area(stacked=False, ylim=(-1.2, 1.2), alpha=0.3)
        detail_orders['close'].plot(secondary_y=True)
    """
    blotter = dict()
    data_dict = backtest.data_handler.latest_symbol_data
    for symb in data_dict.keys():
        data = pd.DataFrame(data_dict[symb], columns=['symbol', 'datetime', 'open', 'high', 'low',
                                                      'close', 'volume']).set_index('datetime')
        blotter[symb] = data.join([positions[symb].to_frame(symb+'_p'), holdings], how='outer').iloc[1:,:]  # 第一行NaN
    return blotter
