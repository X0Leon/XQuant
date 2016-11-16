# -*- coding: utf-8 -*-

"""
绘制蜡烛图、成交量和指标（可选，如技术指标或交易信号）
New in V0.3.5

@author: X0Leon
@version: 0.3.5
"""

import datetime as dt

import matplotlib.dates as mdates
import matplotlib.finance as fplt
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def candlestick(df, **kwargs):
    """
    绘制和保存（可选）DataFrame数据源的蜡烛图
    参数：
    df : DataFrame，按顺序保存'datetime'(index),'open', 'high', 'low', 'close'和'volume'列
    title : str, 可选
    fname : str, 可选，'.png' or '.pdf'后缀的图片名
    events : DataFrame, 可选，相同index，最多四列，无事件则用np.nan
    band : DataFrame, 可选，需要包含'upper'和'lower'两列，例如布林带指标
    line : DataFrame, 可选，例如移动平均线
    """
    _make_chart(df, _candlestick_ax, **kwargs)


def close(df, **kwargs):
    """
    绘制和保存（可选）收盘价
    """
    _make_chart(df, _close_ax, **kwargs)


def _make_chart(df, chartfn, **kwargs):
    fig = plt.figure()
    ax1 = plt.subplot2grid((5, 4), (0, 0), rowspan=4, colspan=4)
    ax1.grid(True)
    plt.ylabel('Price')
    plt.setp(plt.gca().get_xticklabels(), visible=False)
    chartfn(df, ax1)
    if 'line' in kwargs:
        _plot_line(kwargs['line'])
    if 'band' in kwargs:
        _plot_band(kwargs['band'])
    if 'events' in kwargs:
        _plot_events(kwargs['events'])

    ax2 = plt.subplot2grid((5, 4), (4, 0), sharex=ax1, rowspan=1, colspan=4)
    volume = df['volume']
    pos = df['open'] - df['close'] <= 0  # mask
    neg = df['open'] - df['close'] > 0
    ax2.bar(volume[pos].index, volume[pos], color='red', width=0.4, align='center', alpha=0.5)
    ax2.bar(volume[neg].index, volume[neg], color='green', width=0.4, align='center', alpha=0.5)
    #ax2.bar(df.index, df.loc[:, 'volume'],align='center')
    ax2.xaxis.set_major_locator(mticker.MaxNLocator(12))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    if len(df.index) <= 128:  # 建议的时间序列长度，太久则渲染很慢
        ax2.xaxis.set_minor_locator(mdates.DayLocator())
    ax2.yaxis.set_ticklabels([])
    ax2.grid(True)
    plt.ylabel('Volume')
    plt.xlabel('DateTime')
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.subplots_adjust(left=.09, bottom=.18, right=.94, top=0.94, wspace=.20, hspace=0)
    if 'title' in kwargs:
        plt.suptitle(kwargs['title'])
    if 'fname' in kwargs:
        plt.savefig(kwargs['fname'], bbox_inches='tight')
    plt.show()
    #plt.close()


def _candlestick_ax(df, ax):
    quotes = df.reset_index()
    quotes.loc[:, 'datetime'] = mdates.date2num(quotes.loc[:, 'datetime'].astype(dt.date))
    fplt.candlestick_ohlc(ax, quotes.values, width=0.4, colorup='red', colordown='green')


def _close_ax(df, ax):
    ax.plot(df.index, df.loc[:, 'close'])


def _plot_band(banddf):
    plt.fill_between(banddf.index, banddf.loc[:, 'upper'].values,
                     banddf.loc[:, 'lower'].values, facecolor='gray', alpha=0.5)


def _plot_line(linedf):
    lines = plt.plot(linedf.index, linedf.iloc[:, 0].values)
    lines[0].set_color('g')


def _plot_events(events):
    colors = ['m^', 'bv', 'r*', 'gd']
    n_events = min({len(events.columns), len(colors)})
    for i in range(n_events):
        plt.plot(events.index, events.iloc[:, i].values, colors[i], alpha=0.8, ms=12.0)