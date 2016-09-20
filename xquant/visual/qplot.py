import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ohlc
import matplotlib.dates as dt
import matplotlib.ticker as mticker

import pandas as pd


def plot_bars(quotes, df, dfmt='%Y-%m-%d', width=0.1):
    """
    从bars画出k线和成交量
    参数：
    quotes: (datetime, open, high, low, close, volume) tuple的list
    dfmt: 横轴数据的datemate格式，供matplotlib.dates调用
    width：k bar宽度，日线如0.6，分钟线如1.0e-3
    """
    fig = plt.figure(figsize=(10,5))
    ax = plt.subplot2grid((6,1), (0,0), rowspan=4, colspan=1)
    candlestick_ohlc(ax, quotes, width=width, colorup='red', colordown='green')
    # colorup='#CA0000',colordown='#72DADA'

    # plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    ax.xaxis.set_major_formatter(dt.DateFormatter(dfmt))  # '%Y-%m-%d'如果下面用sharex，这个设置就没意义啦，都一样
    ax.xaxis.set_major_locator(mticker.MaxNLocator(10))
    # ax.yaxis.set_ticks_position("left")

    ax.set_ylabel('Price', size=16)
    # ax.yaxis.set_label_position("right")
    ax.set_axis_bgcolor('black')
    ax.grid(color='red', linewidth=1)

    ############################# 成交量ax2 ################################
    ax2 = plt.subplot2grid((6,1), (4,0), rowspan=4, colspan=1, sharex=ax)
    ax2.xaxis.set_ticks_position('bottom')

    volume = df['volume']
    pos = df['open']-df['close'] < 0  # mask
    neg = df['open']-df['close'] > 0
    ax2.bar(list(map(dt.date2num, volume[pos].index)), volume[pos], color='red', width=width, align='center')
    ax2.bar(list(map(dt.date2num, volume[neg].index)), volume[neg], color='green', width=width, align='center')

    # ax2.set_yticks([])
    yticks = ax2.get_yticks()
    ax2.set_yticks(yticks[::3])
    # ax2.yaxis.set_label_position("right")
    # ax2.yaxis.set_ticks_position("left")

    ax2.set_ylabel('Volume', size=16)
    for label in ax2.xaxis.get_ticklabels():
        label.set_rotation(15)
    ax2.xaxis.set_major_formatter(dt.DateFormatter(dfmt))  # '%Y-%m-%d'
    ax2.xaxis.set_major_locator(mticker.MaxNLocator(10))
    ax2.set_axis_bgcolor('black')

    # fig.suptitle('600008', y =0.94, fontsize=14, color='red')

    plt.tight_layout()

    return fig


# if __name__ == "__main__":
#     q = pd.read_hdf('D:/thinkquant/data/daily.h5', '600008', format='table')
#     q = q.loc['2016-05-08':'2015-12-18']
#     quotes = [(dt.date2num(q.ix[i].name), q.ix[i]['open'], q.ix[i]['high'],
#               q.ix[i]['low'], q.ix[i]['close'], q.ix[i]['volume']) for i in range(len(q))]
#
#
#     plot_bars(quotes,q)
#     print('Run plot_bars()!')


def plot_portfolio(backtest, symbol):
    """
    画出投资组合曲线、close曲线与持仓symbol的投资、价值对比
    参数:
    backtest: 回测Backtest类的实例
    symbol：股票或期货代码，如'IC1604'
    """
    cols = ['symbol', 'datetime', 'open', 'high', 'low', 'close', 'volume']
    bars = pd.DataFrame(backtest.data_handler.latest_symbol_data[symbol], columns=cols).set_index('datetime')
    df = pd.concat([backtest.portfolio.equity_curve, bars], axis=1).ix[1:-1]  # 剔除0和-1两行，冗余
    x = list(range(len(df)))

    fig = plt.figure(figsize=(7,6))
    ax = plt.subplot2grid((6,1), (0,0), rowspan=2, colspan=1)
    ax.plot(x, df['close'], 'blue')
    ax.set_ylabel('Close Price')

    axt = ax.twinx()
    axt.plot(x, df['volume'], 'green', alpha=0.3)
    axt.set_ylabel('Volume')

    ax2 = plt.subplot2grid((6,1), (2,0), rowspan=3, colspan=1, sharex=ax)
    ax2.plot(x, df['equity_curve'])
    fmt = '%3.1f%%'
    yticks = mticker.FormatStrFormatter(fmt)
    ax2.yaxis.set_major_formatter(yticks)
    ax2.set_ylabel('Equity Curve')
   
    ax2t = ax2.twinx()
    y = df[symbol]
    ax2t.fill_between(x, 0, y, where=y >= 0, facecolor='blue', alpha=0.3, lw = 0.0, edgecolor='blue')
    ax2t.fill_between(x, 0, y, where=y <= 0, facecolor='blue', alpha=0.3, edgecolor='blue')
    ax2t.set_ylabel('%s Holding' % symbol)

    ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(5))

    plt.tight_layout()
    plt.show()

    return fig
