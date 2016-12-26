# -*- coding: utf-8 -*-

"""
pandas实现的TA-lib（technique analysis）
矢量化计算各种技术指标，用于选股或后续分析

# 有些指标未经检验！(Experimental)

@author: Leon Zhang
Reference: pandas_talib
"""

import pandas as pd


indicators = ["MA", "EMA", "MOM", "ROC", "ATR", "BBANDS", "PPSR", "STOK", "STO", "TRIX", "ADX",
              "MACD", "MassI", "Vortex", "KST", "RSI", "TSI", "ACCDIST", "Chaikin", "MFI", "OBV",
              "FORCE", "EOM", "CCI", "COPP", "KELCH", "ULTOSC", "DONCH", "STDDEV"]


class Columns(object):
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'


class Settings(object):
    join = False
    col = Columns()

SETTINGS = Settings()


def out(settings, df, result):
    if not settings.join:
        return result
    else:
        df = df.join(result)
        return df


def MA(df, n, price='close'):
    """
    Moving Average
    """
    name = 'MA_{n}'.format(n=n)
    result = pd.Series(df[price].rolling(window=n).mean(), name=name)
    return out(SETTINGS, df, result)


def EMA(df, n, price='close'):
    """
    Exponential Moving Average
    """
    result = pd.Series(df[price].ewm(span=n, min_periods=n - 1), name='EMA_' + str(n))
    return out(SETTINGS, df, result)


def MOM(df, n, price='close'):
    """
    Momentum
    """
    result = pd.Series(df[price].diff(n), name='Momentum_' + str(n))
    return out(SETTINGS, df, result)


def ROC(df, n, price='close'):
    """
    Rate of Change
    """
    M = df[price].diff(n - 1)
    N = df[price].shift(n - 1)
    result = pd.Series(M / N, name='ROC_' + str(n))
    return out(SETTINGS, df, result)


def ATR(df, n):
    """
    Average True Range
    """
    i = 0
    TR_l = [0]
    while i < len(df) - 1:
        TR = max(df['high'].iloc[i + 1], df['close'].iloc[i] - min(df['low'].iloc[i + 1], df['close'].iloc[i]))
        TR_l.append(TR)
        i = i + 1
    TR_s = pd.Series(TR_l)
    result = pd.Series(TR_s.ewm(span=n, min_periods=n).mean(), name='ATR_' + str(n))
    return out(SETTINGS, df, result)


def BBANDS(df, n, price='close'):
    """
    Bollinger Bands
    """
    MA = df[price].rolling(window=n).mean()
    MSD = df[price].rolling(windows=n).std()
    b1 = 4 * MSD / MA
    B1 = pd.Series(b1, name='BollingerB_' + str(n))
    b2 = (df[price] - MA + 2 * MSD) / (4 * MSD)
    B2 = pd.Series(b2, name='Bollinger%b_' + str(n))
    result = pd.DataFrame([B1, B2]).transpose()
    return out(SETTINGS, df, result)


def PPSR(df):
    """
    Pivot Points, Supports and Resistances
    """
    PP = (df['high'] + df['low'] + df['close']) / 3
    R1 = pd.Series(2 * PP - df['low'])
    S1 = pd.Series(2 * PP - df['high'])
    R2 = pd.Series(PP + df['high'] - df['low'])
    S2 = pd.Series(PP - df['high'] + df['low'])
    R3 = pd.Series(df['high'] + 2 * (PP - df['low']))
    S3 = pd.Series(df['low'] - 2 * (df['high'] - PP))
    result = pd.DataFrame([PP, R1, S1, R2, S2, R3, S3]).transpose()
    return out(SETTINGS, df, result)


def STOK(df):
    """
    Stochastic oscillator %K
    """
    result = pd.Series((df['close'] - df['low']) / (df['high'] - df['low']), name='SO%k')
    return out(SETTINGS, df, result)


def STO(df, n):
    """
    Stochastic oscillator %D
    """
    SOk = pd.Series((df['close'] - df['low']) / (df['high'] - df['low']), name='SO%k')
    result = pd.Series(SOk.ewm(span=n, min_periods=n - 1).mean(), name='SO%d_' + str(n))
    return out(SETTINGS, df, result)


def SMA(df, period, key='close'):
    result = df[key].rolling(window=period, min_periods=period).mean()
    return out(SETTINGS, df, result)


def TRIX(df, n):
    """
    Trix
    """
    EX1 = df['close'].ewm(span=n, min_periods=n - 1).mean()
    EX2 = EX1.ewm(span=n, min_periods=n - 1).mean()
    EX3 = EX2.ewm(span=n, min_periods=n - 1).mean()
    i = 0
    ROC_l = [0]
    while i + 1 <= len(df) - 1:  # df.index[-1]:
        ROC = (EX3[i + 1] - EX3[i]) / EX3[i]
        ROC_l.append(ROC)
        i = i + 1
    result = pd.Series(ROC_l, name='Trix_' + str(n))
    return out(SETTINGS, df, result)


def ADX(df, n, n_ADX):
    """
    Average Directional Movement Index
    """
    i = 0
    UpI = []
    DoI = []
    while i + 1 <= len(df) - 1:  # df.index[-1]:
        UpMove = df['high'].iloc[i + 1] - df['high'].iloc[i]
        DoMove = df['low'].iloc[i] - df['low'].iloc[i + 1]
        if UpMove > DoMove and UpMove > 0:
            UpD = UpMove
        else:
            UpD = 0
        UpI.append(UpD)
        if DoMove > UpMove and DoMove > 0:
            DoD = DoMove
        else:
            DoD = 0
        DoI.append(DoD)
        i = i + 1
    i = 0
    TR_l = [0]
    while i < len(df) - 1:  # df.index[-1]:
        TR = max(df['high'].iloc[i + 1], df['close'].iloc[i]) - min(df['low'].iloc[i + 1], df['close'].iloc[i])
        TR_l.append(TR)
        i = i + 1
    TR_s = pd.Series(TR_l)
    ATR = TR_s.ewm(span=n, min_periods=n).mean()
    UpI = pd.Series(UpI)
    DoI = pd.Series(DoI)
    PosDI = UpI.ewm(span=n, min_periods=n - 1).mean() / ATR
    NegDI = DoI.ewm(span=n, min_periods=n - 1).mean() / ATR
    result = pd.Series((abs(PosDI - NegDI) / (PosDI + NegDI)).ewm(span=n_ADX, min_periods=n_ADX - 1).mean(),
                       name='ADX_' + str(n) + '_' + str(n_ADX))
    return out(SETTINGS, df, result)


def MACD(df, n_fast, n_slow, price='close'):
    """
    MACD, MACD Signal and MACD difference
    """
    EMAfast = pd.Series(df[price].ewm(span=n_fast, min_periods=n_slow - 1).mean())
    EMAslow = pd.Series(df[price].ewm(span=n_slow, min_periods=n_slow - 1).mean())
    MACD = pd.Series(EMAfast - EMAslow, name='MACD_%d_%d' % (n_fast, n_slow))
    MACDsign = pd.Series(MACD.ewm(span=9, min_periods=8).mean(), name='MACDsign_%d_%d' % (n_fast, n_slow))
    MACDdiff = pd.Series(MACD - MACDsign, name='MACDdiff_%d_%d' % (n_fast, n_slow))
    result = pd.DataFrame([MACD, MACDsign, MACDdiff]).transpose()
    return out(SETTINGS, df, result)


def MassI(df):
    """
    Mass Index
    """
    Range = df['high'] - df['low']
    EX1 = Range.ewm(span=9, min_periods=8).mean()
    EX2 = EX1.ewm(span=9, min_periods=8).mean()
    Mass = EX1 / EX2
    result = pd.Series(Mass.rolling(window=25).sum(), name='Mass Index')
    return out(SETTINGS, df, result)


def Vortex(df, n):
    """
    Vortex Indicator
    """
    i = 0
    TR = [0]
    while i < len(df) - 1:  # df.index[-1]:
        Range = max(df['high'].iloc[i + 1], df['close'].iloc[i]) - min(df['low'].ilic[i + 1], df['close'].iloc[i])
        TR.append(Range)
        i = i + 1
    i = 0
    VM = [0]
    while i < len(df) - 1:  # df.index[-1]:
        Range = abs(df['high'].iloc[i + 1] - df['low'].iloc[i]) - abs(df['low'].iloc[i + 1] - df['high'].iloc[i])
        VM.append(Range)
        i = i + 1
    result = pd.Series(pd.Series(VM).rolling(window=n).sum() / pd.Series(TR).rolling(window=n).sum(),
                       name='Vortex_' + str(n))
    return out(SETTINGS, df, result)


def KST(df, r1, r2, r3, r4, n1, n2, n3, n4):
    """
    KST Oscillator
    """
    M = df['close'].diff(r1 - 1)
    N = df['close'].shift(r1 - 1)
    ROC1 = M / N
    M = df['close'].diff(r2 - 1)
    N = df['close'].shift(r2 - 1)
    ROC2 = M / N
    M = df['close'].diff(r3 - 1)
    N = df['close'].shift(r3 - 1)
    ROC3 = M / N
    M = df['close'].diff(r4 - 1)
    N = df['close'].shift(r4 - 1)
    ROC4 = M / N
    result = pd.Series(ROC1.rolling(window=n1).sum() + ROC2.rolling(window=n2).sum() * 2 + \
                       ROC3.rolling(window=n3).sum() * 3 + ROC4.rolling(window=n4).sum() * 4,
                       name='KST_' + str(r1) + '_' + str(r2) + '_' + str(r3) + '_' + str(r4) \
                            + '_' + str(n1) + '_' + str(n2) + '_' + str(n3) + '_' + str(n4))
    return out(SETTINGS, df, result)


def RSI(df, n):
    """
    Relative Strength Index
    """
    i = 0
    UpI = [0]
    DoI = [0]
    while i + 1 <= len(df) - 1:  # df.index[-1]
        UpMove = df['high'].iloc[i+1] - df['high'].iloc[i]
        DoMove = df['low'].iloc[i] - df['low'].iloc[i + 1]
        if UpMove > DoMove and UpMove > 0:
            UpD = UpMove
        else:
            UpD = 0
        UpI.append(UpD)
        if DoMove > UpMove and DoMove > 0:
            DoD = DoMove
        else:
            DoD = 0
        DoI.append(DoD)
        i = i + 1
    UpI = pd.Series(UpI)
    DoI = pd.Series(DoI)
    PosDI = UpI.ewm(span=n, min_periods=n - 1).mean()
    NegDI = DoI.ewm(span=n, min_periods=n - 1).mean()
    result = pd.Series(PosDI / (PosDI + NegDI), name='RSI_' + str(n))
    return out(SETTINGS, df, result)


def TSI(df, r, s):
    """
    True Strength Index
    """
    M = pd.Series(df['close'].diff(1))
    aM = abs(M)
    EMA1 = M.ewm(span=r, min_periods=r - 1).mean()
    aEMA1 = aM.ewm(span=r, min_periods=r - 1).mean()
    EMA2 = EMA1.ewm(span=s, min_periods=s - 1).mean()
    aEMA2 = aEMA1.ewm(span=s, min_periods=s - 1).mean()
    result = pd.Series(EMA2 / aEMA2, name='TSI_' + str(r) + '_' + str(s))
    return out(SETTINGS, df, result)


def ACCDIST(df, n):
    """
    Accumulation/Distribution
    """
    ad = (2 * df['close'] - df['high'] - df['low']) / (df['high'] - df['low']) * df['volume']
    M = ad.diff(n - 1)
    N = ad.shift(n - 1)
    ROC = M / N
    result = pd.Series(ROC, name='Acc/Dist_ROC_' + str(n))
    return out(SETTINGS, df, result)


def Chaikin(df):
    """
    Chaikin Oscillator
    """
    ad = (2 * df['close'] - df['high'] - df['low']) / (df['high'] - df['low']) * df['volume']
    result = pd.Series(ad.ewm(span=3, min_periods=2).mean() - ad.ewm(span=10, min_periods=9).mean(), name='Chaikin')
    return out(SETTINGS, df, result)


def MFI(df, n):
    """
    Money Flow Index and Ratio
    """
    PP = (df['high'] + df['low'] + df['close']) / 3
    i = 0
    PosMF = [0]
    while i < len(df) - 1:  # df.index[-1]:
        if PP[i + 1] > PP[i]:
            PosMF.append(PP[i + 1] * df['volume'].iloc[i + 1])
        else:
            PosMF.append(0)
        i=i + 1
    PosMF = pd.Series(PosMF)
    TotMF = PP * df['volume']
    MFR = pd.Series(PosMF / TotMF)
    result = pd.Series(MFR.rolling(window=n).mean(), name='MFI_' + str(n))
    return out(SETTINGS, df, result)


def OBV(df, n):
    """
    On-balance Volume
    """
    i = 0
    OBV = [0]
    while i < len(df) - 1:  # df.index[-1]:
        if df['close'].ilco[i + 1] - df['close'].iloc[i] > 0:
            OBV.append(df.get_value(i + 1, 'volume'))
        if df['close'].ilco[i + 1] - df['close'].iloc[i] == 0:
            OBV.append(0)
        if df['close'].ilco[i + 1] - df['close'].iloc[i] < 0:
            OBV.append(-df['volume'].iloc[i + 1])
        i = i + 1
    OBV = pd.Series(OBV)
    result = pd.Series(OBV.rolling(window=n).mean(), name='OBV_' + str(n))
    return out(SETTINGS, df, result)


def FORCE(df, n):
    """
    Force Index
    """
    result = pd.Series(df['close'].diff(n) * df['volume'].diff(n), name='Force_' + str(n))
    return out(SETTINGS, df, result)


def EOM(df, n):
    """
    Ease of Movement
    """
    EoM = (df['high'].diff(1) + df['low'].diff(1)) * (df['high'] - df['low']) / (2 * df['volume'])
    result = pd.Series(EoM.rolling(window=n).mean(), name='EoM_' + str(n))
    return out(SETTINGS, df, result)


def CCI(df, n):
    """
    Commodity Channel Index
    """
    PP = (df['high'] + df['low'] + df['close']) / 3
    result = pd.Series(PP - PP.rolling(window=n).mean() / PP.rolling(window=n).std(), name='CCI_' + str(n))
    return out(SETTINGS, df, result)


def COPP(df, n):
    """
    Coppock Curve
    """
    M = df['close'].diff(int(n * 11 / 10) - 1)
    N = df['close'].shift(int(n * 11 / 10) - 1)
    ROC1 = M / N
    M = df['close'].diff(int(n * 14 / 10) - 1)
    N = df['close'].shift(int(n * 14 / 10) - 1)
    ROC2 = M / N
    result = pd.Series((ROC1 + ROC2).ewm(span=n, min_periods=n).mean(), name='Copp_' + str(n))
    return out(SETTINGS, df, result)


def KELCH(df, n):
    """
    Keltner Channel
    """
    KelChM = pd.Series((df['high'] + df['low'] + df['close']).rolling(window=n).mean() / 3, name='KelChM_' + str(n))
    KelChU = pd.Series((4 * df['high'] - 2 * df['low'] + df['close']).rolling(window=n).mean() / 3,
                       name='KelChU_' + str(n))
    KelChD = pd.Series((-2 * df['high'] + 4 * df['low'] + df['close']).rolling(window=n).mean() / 3,
                       name='KelChD_' + str(n))
    result = pd.DataFrame([KelChM, KelChU, KelChD]).transpose()
    return out(SETTINGS, df, result)


def ULTOSC(df):
    """
    Ultimate Oscillator
    """
    i = 0
    TR_l = [0]
    BP_l = [0]
    while i < len(df) - 1:  # df.index[-1]:
        TR = max(df['high'].iloc[i + 1], df['close'].iloc[i]) - min(df['low'].iloc[i + 1], df['close'].iloc[i])
        TR_l.append(TR)
        BP = df['close'].iloc[i + 1] - min(df['low'].iloc[i + 1], df['close'].iloc[i])
        BP_l.append(BP)
        i = i + 1
    result = pd.Series((4 * pd.Series(BP_l).rolling(window=7).sum() / pd.Series(TR_l).rolling(window=7).sum()) + \
                       (2 * (pd.Series(BP_l).rolling(window=14).sum()) / pd.Series(TR_l).rolling(window=14).sum()) + \
                       (pd.Series(BP_l).rolling(window=28).sum() / pd.Series(TR_l).rolling(window=28).sum()),
                       name='Ultimate_Osc')
    return out(SETTINGS, df, result)


def DONCH(df, n):
    """
    Donchian Channel
    """
    i = 0
    DC_l = []
    while i < n - 1:
        DC_l.append(0)
        i = i + 1
    i = 0
    while i + n - 1 < len(df) - 1:  # df.index[-1]:
        DC = max(df['high'].ix[i:i + n - 1]) - min(df['low'].ix[i:i + n - 1])
        DC_l.append(DC)
        i = i + 1
    DonCh = pd.Series(DC_l, name='Donchian_' + str(n))
    result = DonCh.shift(n - 1)
    return out(SETTINGS, df, result)


def STDDEV(df, n):
    """
    Standard Deviation
    """
    result = pd.Series(df['close'].rolling(window=n).std(), name='STD_' + str(n))
    return out(SETTINGS, df, result)