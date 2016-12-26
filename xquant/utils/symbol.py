# -*- coding: utf-8 -*-

"""
判断投资品对应的金融市场，股票：上海交易所、深圳交易所
                     商品期货：上海期货交易所、大连商品交易所、郑州商品交易所
                     金融衍生品：中国金融期货交易所
New in V0.3.5

@author: Leon Zhang
@version: 0.3.5
"""

def get_exchange(symbol):
    """判断ID对应的证券市场
    匹配规则
    ['50', '51', '60', '90', '110'] 为SH
    ['00', '13', '18', '15', '16', '18', '20', '30', '39', '115'] 为SZ
    ['5', '6', '9'] 开头的为SH， 其余为SZ

    上期(SQ)：铜（CU）、铝（AL）、锌（ZN）、天胶（RU） 燃油（FU）、黄金（AU）、螺纹钢（RB）、线材（WR）、白银（AG）、沥青（BU）、
            燃料油（FU）、沪铅（PB）、热轧卷板（HC）
    大商(DS)：豆一（A）、豆粕（M）、豆油（Y）、玉米（C）、棕榈油（P）、乙烯（L）、PVC（V）、豆二（B）、焦煤（JM）、焦炭（J）、胶板（BB）、
            纤板（FB）、铁矿石（I）、鸡蛋（JD）、丙烯（PP）
    郑商(ZS)：棉花（CF）、玻璃（FG）、粳稻（JR)、晚稻（LR）、甲醇（MA）、菜油（OI）、普麦（PM）、早稻（RI）、菜粕（RM）、硅铁（SF）、
            硅锰（SM）、白糖（SR）、PTA（TA）、强麦（WH）、动力煤（ZC）
    中金(ZJ)：股指期货（IF）、国债（TF）
    """
    # assert type(stock_code) is str, 'symbol code need str type'
    if symbol.startswith(('50', '51', '60', '90', '110', '113', '132', '204')):
        return 'SH.EX'
    elif symbol.startswith(('00', '13', '18', '15', '16', '18', '20', '30', '39', '115', '1318')):
        return 'SZ.EX'

    elif symbol.startswith(('AG', 'AL', 'AU', 'BU', 'CU', 'FU', 'HC', 'PB', 'RB', 'RU', 'WR', 'ZN')):
        return 'SQ.EX'
    elif symbol.startswith(('A', 'B', 'BB', 'C', 'FB', 'I', 'J', 'JD', 'JM', 'L', 'M', 'P', 'PP', 'V', 'Y')):
        return 'DS.EX'
    elif symbol.startswith(('CF', 'FG', 'JR', 'LR', 'MA', 'OI', 'PM', 'RI', 'RM', 'SF', 'SM', 'SR', 'TA', 'WH', 'ZC')):
        return 'ZS.EX'
    elif symbol.startswith(('IF', 'TF')):
        return 'ZJ.EX'
    else:
        return 'Unknown Exchange'