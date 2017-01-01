# XQuant文档

Backtest frame for equity/futures market. 股票和期货的量化投资回测框架。

## 安装

* 方式1：python setup.py install
* 方式2：pip install xquant (推荐)

## 快速入门

在事件驱动的回测框架中，引擎逐个读取Bar或Tick并处理。数据采集模块生成市场数据事件，流经策略模块（Strategy类）产生交易信号，资产组合模块根据策略信号，并结合风险管理来判断是否委托下单，模拟的交易所根据滑点、手续费状况等返回成交结果。

大部分时候我们不需要关心底层是如何处理的，只需要在Strategy类中完成从数据到信号的处理即可，这有利于我们快速开发策略。

### backtest引擎

假如我们已经写好了一个策略，我们称之为DemoStrategy（或者更现实一点的为MovingAverageCrossStrategy），将这个策略类传入回测引擎Backtest类中，然后就可以直接回测。首先我们来看初始化Backtest类需要哪些参数：

    Backtest(csv_dir, symbol_list, initial_capital, heartbeat, start_date, 
             end_date,data_handler, execution_handler, portfolio, strategy, 
             commission_type='zero', slippage_type='zero', **params)

* csv_dir: CSV数据文件夹目录
* symbol_list: 股票代码str的list，如'600008'
* initial_capital: 初始资金，如10000.0
* heartbeat: k bar周期，以秒计，如分钟线为60，模拟交易使用，回测时设为0
* start_date: 策略回测起始时间，datetime类型
* end_date: 策略回测结束时间
* end_date: 策略回测结束时间
* data_handler: (Class) 处理市场数据的类
* execution_handler: (Class) 处理order/fill的类
* portfolio: (Class) 虚拟账户，追踪组合头寸等信息的类
* strategy: (Class) 根据市场数据生成信号的策略类
* commission_type: 交易费率模型，'zero', 'default'（A股市场）
* slippage_type: 滑点模型，'zero'，’fixed'（固定百分比）
* params: 策略参数的字典，如移动均线策略需传入可变的long_window/short_window

注意到需要传入一些类来初始化引擎，所以在策略文件一开始我们导入它们：

    from xquant import (SignalEvent, Strategy, CSVDataHandler, 
                        SimulatedExecutionHandler, BasicPortfolio, Backtest)
                        
其他一些变量可以直接传入，当然指定一个额外的变量使可读性更好：

    csv_dir = 'D:/data'
    symbol_list = ['600008', '600018', '600028']  # 需00008.csv这样的文件
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2015, 1, 1 0, 0)
    end_date = datetime.datetime.now()
    # 实例化回测引擎
    backtest = Backtest(csv_dir, symbol_list, initial_capital, heartbeat, 
                        start_date, end_date, CSVDataHandler, 
                        SimulatedExecutionHandler, BasicPortfolio, DemoStrategy)

### 获取数据

上例演示了我们用本地csv数据源进行回测，以600008.csv为例，其应该应该依次包含datetime, open, high, low, close, volume六列，然后CSVDataHandler自动为我们逐个bar播放数据。在策略中我们需要获得过去的数据，最主要的接口是：

    bars = DataHandler.get_latest_bars(N=1)
    # 获取最近的N根bars，返回的数据结构是元组的列表
    # 即[(symbol, datetime, open, high, low, close, volume),(),…]

对于每个bar，我们可以用bar.open这样的方式来获取成员。

### 发出信号

回测引擎用事件队列Events来完成各模块的通信，写策略时需要用的类是MarketEvent和SignalEvent。

MarketEvent.type是'MARKET'，此时如果收到DataHandler发来的新的市场数据，我们就要进行信号的生产工作了。在每个bar周期backtest都会调用Strategy类的calculate_signals()方法（每个策略都应该实现此方法），对资产在当前时间节点上做好判断后，就给出多头('LONG')、空头('SHORT')、离开市场('EXIT')三种指令，然后将信号放入队列中。

信号事件的构建：

    SignalEvent(symbol, datetime, signal_type, strategy_id=1, strength=1.0)

### 策略

熟悉上述更部分，我们就可以写策略啦，下面是移动双均线策略的示例：

    class MovingAverageCrossStrategy(Strategy):
        """
        移动双均线策略
        """
        def __init__(self, bars, events, long_window=10, short_window=5):
            """
            初始化移动平均线策略
            参数：
            bars: DataHandler对象
            events: Event队列对象
            long_window: 长期均线的长度
            short_window: 短期均线的长度
            """
            self.bars = bars
            self.symbol_list = self.bars.symbol_list
            self.events = events
            self.long_window = long_window
            self.short_window = short_window
    
            self.bought = self._calculate_initial_bought() 
    
        def _calculate_initial_bought(self):
            """
            添加symbol的持有情况到字典，初始化为未持有
            """
            bought = {}
            for s in self.symbol_list:
                bought[s] = False  # 或者'EXIT'
            return bought
    
        def calculate_signals(self, event):
            """
            当短期均线（如5日线）上穿长期均线（如10日线），买入；反之，卖出
            """
            if event.type == 'BAR':
                for s in self.symbol_list:
                    bar = self.bars.get_latest_bar(s)
                    if bar is None or bar == []: continue
    
                    bars = self.bars.get_latest_bars(s, N=self.long_window)
                    if len(bars) >= self.long_window:
                        df = pd.DataFrame(bars, columns=['symbol','datetime','open','high','low','close','volume'])
                        df['MA_l'] = df['close'].rolling(self.long_window, min_periods=1).mean()
                        df['MA_s'] = df['close'].rolling(self.short_window, min_periods=1).mean()
                        if df['MA_l'].iloc[-1] < df['MA_s'].iloc[-1] and df['MA_l'].iloc[-2] > df['MA_s'].iloc[-2]:
                            if not self.bought[s]:
                                signal = SignalEvent(bar.symbol, bar.datetime, 'LONG')
                                self.events.put(signal)
                                self.bought[s] = True
                        elif df['MA_l'].iloc[-1] < df['MA_s'].iloc[-1] and df['MA_l'].iloc[-2] < df['MA_s'].iloc[-2]:
                            if self.bought[s]:
                                signal = SignalEvent(bar.symbol, bar.datetime, 'EXIT')
                                self.events.put(signal)
                                self.bought[s] = False

### 结果分析

如何获得策略的策略的回测结果呢？调用Backtest的simulate_trading()方法即可：

    positions, holdings = backtest.simulate_trading()

positions是所有品种（symbol）持仓情况的DataFrame，holdings是账户净值情况的DataFrame，可以据此进一步分析，xquant.perform模块提供了夏普率、最大回测等常用的策略表现得评估函数：

    from xquant.perform import perform_metrics
    
    perform_metrics(holdings['total'], periods=252)  # 若为分钟periods=252*24*60
    perform, ret, sharpe_ratio, max_dd = holdings['total']

如果我们还想获得每笔成交情况，可以调用：

    trades = backtest.trade_record()

通常情况下，我们由positions, holdings和trades足以分析策略的表现。

对于多品种组合合适时，我们可能对各个品种单独的表现也很感兴趣，finance.perform中提供了一个便捷函数，用于获得详细的交易流水：

    from xquant.perform import detail_blotter
    
    blotter = detail_blotter(backtest, positions, holdings)  # 字典，值为df
    blotter1 = blotter['600008']

### 示例

## 例子

1. demo中的完整的移动双均线策略：[Moving Average Cross Strategy](https://github.com/X0Leon/XQuant/blob/master/demo/ma_cross_strategy.py)
2. 某商品期货策略的回测结果：

![chart demo](chart_demo.png)

Copyright (c) 2016 X0Leon (Leon Zhang) Email: pku09zl[at]gmail[dot]com
