# -*- coding: utf-8 -*-

"""
绘制蜡烛图、成交量和指标（可选，如技术指标或交易信号）

@author: X0Leon
@version: 0.4
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
    events : DataFrame, 可选，与df相同index，最多四列，无事件则用np.nan
    tracks: DataFrame，可选，与df相同index，最多两列，例如仓位变化
    band : DataFrame, 可选，需要包含'upper'和'lower'两列，例如布林带指标
    lines : DataFrame, 可选，例如移动平均线
    """
    _make_chart(df, _candlestick_ax, **kwargs)


def close(df, **kwargs):
    """
    绘制和保存（可选）收盘价
    """
    _make_chart(df, _close_ax, **kwargs)


def _make_chart(df, chartfn, **kwargs):
    fig = plt.figure()
    ax1 = plt.subplot2grid((6, 4), (1, 0), rowspan=4, colspan=4)
    ax1.grid(True)
    plt.ylabel('Price')
    plt.setp(plt.gca().get_xticklabels(), visible=False)
    chartfn(df, ax1)
    if 'lines' in kwargs:
        _plot_lines(kwargs['lines'])
    if 'band' in kwargs:
        _plot_band(kwargs['band'])
    if 'events' in kwargs:
        _plot_events(kwargs['events'])

    ax2 = plt.subplot2grid((6, 4), (5, 0), sharex=ax1, rowspan=1, colspan=4)
    volume = df['volume']
    pos = df['open'] - df['close'] <= 0  # mask
    neg = df['open'] - df['close'] > 0
    ax2.bar(volume[pos].index, volume[pos], color='red', width=0.4, align='center', alpha=0.5)
    ax2.bar(volume[neg].index, volume[neg], color='green', width=0.4, align='center', alpha=0.5)
    # ax2.bar(df.index, df.loc[:, 'volume'],align='center')
    ax2.xaxis.set_major_locator(mticker.MaxNLocator(12))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    if len(df.index) <= 500:
        ax2.xaxis.set_minor_locator(mdates.DayLocator())
    ax2.yaxis.set_ticklabels([])
    ax2.grid(True)
    plt.ylabel('Volume')
    plt.xlabel('DateTime')
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    ax3 = plt.subplot2grid((6, 4), (0, 0), sharex=ax1, rowspan=1, colspan=4)
    if 'tracks' in kwargs:
        _plot_tracks(kwargs['tracks'])
    ax3.yaxis.set_ticklabels([])
    # ax3.yaxis.tick_right()
    ax3.grid(True)
    ax3.xaxis.set_visible(False)
    ax3.set_ylabel('Observe')
    plt.subplots_adjust(left=.09, bottom=.18, right=.94, top=0.94, wspace=.20, hspace=0)
    if 'title' in kwargs:
        plt.suptitle(kwargs['title'])
    if 'fname' in kwargs:
        plt.savefig(kwargs['fname'], bbox_inches='tight')
    plt.show()
    # plt.close()


def _candlestick_ax(df, ax):
    quotes = df.reset_index()
    quotes.loc[:, 'datetime'] = mdates.date2num(quotes.loc[:, 'datetime'].astype(dt.date))
    fplt.candlestick_ohlc(ax, quotes.values, width=0.4, colorup='red', colordown='green')


def _close_ax(df, ax):
    ax.plot(df.index, df.loc[:, 'close'])


def _plot_band(band):
    plt.fill_between(band.index, band.loc[:, 'upper'].values,
                     band.loc[:, 'lower'].values, facecolor='gray', alpha=0.5)


def _plot_lines(lines):
    colors = ['g', 'b', 'r']
    n_lines = min(len(lines.columns), len(colors))
    for i in range(n_lines):
        plt.plot(lines.index, lines.iloc[:, i].values, colors[i])


def _plot_events(events):
    colors = ['m^', 'bv', 'r*', 'gd']
    n_events = min({len(events.columns), len(colors)})
    for i in range(n_events):
        plt.plot(events.index, events.iloc[:, i].values, colors[i], alpha=0.8, ms=12.0)


def _plot_tracks(tracks):
    colors = ['r', 'b']
    n_tracks = min({len(tracks.columns), len(colors)})
    for i in range(n_tracks):
        ob = tracks.iloc[:, i].values
        plt.plot(tracks.index, ob, colors[i], lw=0.5)
        plt.ylim(((1.1 if min(ob) < 0 else -1.1) * min(ob), 1.1 * max(ob)))
        if min(ob) < 0 < max(ob):
            plt.axhline(y=0.0, color='k', lw=0.5)