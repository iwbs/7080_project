import talib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import uuid
import const
from pandas.plotting import register_matplotlib_converters
from dateutil.relativedelta import relativedelta
register_matplotlib_converters()


# init capital, portfolio, transLog
ava_bal = const.CAPITAL
reserve = const.CAPITAL * const.RESERVE_RATIO
trans_log = pd.DataFrame(columns=['date', 'position_id' ,'name', 'price', 'qty', 'type', 'initial_margin', 'cost', 'net_profit'])
portfolio = pd.DataFrame(columns=['id', 'name', 'order_price', 'market_price', 'qty', 'type', 'profit'])



# Donchian Channel
def DONCH(low, high, timeperiod: int = 20):
    if len(high) != len(low):
        return [], []
    dc_low = []
    dc_high = []
    for i in range(0, len(high)):
        if i < timeperiod - 1:
            dc_low.append(np.nan)
            dc_high.append(np.nan)
        else:
            min_list = low.iloc[i - (timeperiod - 1): i]
            max_list = high.iloc[i - (timeperiod - 1): i]
            if len(min_list) == 0 or len(max_list) == 0:
                dc_low.append(np.nan)
                dc_high.append(np.nan)
            else:
                dc_min = min(min_list)
                dc_max = max(max_list)
                dc_low.append(dc_min)
                dc_high.append(dc_max)
    return dc_low, dc_high


def openPosition(name, price, qty, signal, date):
    global ava_bal
    global trans_log
    global portfolio
    initial_margin = qty * price * const.MULTIPLIER * const.INIT_MARGIN
    cost = qty * (const.COMMISSION + const.EXCHANGE_FEE + const.SFC_LEVY)
    uid = str(uuid.uuid4())[:8]
    
    # if there is enough balance
    if ava_bal - initial_margin - cost > reserve:
        # update transaction log
        trans_log = trans_log.append({
            'date' : date,
            'position_id' : uid,
            'name' : name,
            'type' : signal,
            'price' : price,
            'qty' : qty,
            'initial_margin' : initial_margin,
            'cost' : cost
        } , ignore_index=True)

        # update available balance
        ava_bal -= initial_margin + cost

        # update portfolio
        portfolio = portfolio.append({
            'id' : uid,
            'name' : name,
            'type' : signal,
            'order_price' : price,
            'market_price' : price,
            'qty' : qty,
            'initial_margin' : initial_margin,
            'profit' : 0
        } , ignore_index=True)
    else:
        print('order failed - exceed safety reserve')


def closePosition(portfolio_id, price, date):
    global ava_bal
    global trans_log
    global portfolio
    position = portfolio.loc[portfolio_id]
    cost = position['qty'] * (const.COMMISSION + const.EXCHANGE_FEE + const.SFC_LEVY)
    if position['type'] == 'long':
        profit = price - position['order_price']
    elif position['type'] == 'short':
        profit = position['order_price'] - price

    net_profit = position['qty'] * (profit * const.MULTIPLIER - const.COMMISSION - const.EXCHANGE_FEE - const.SFC_LEVY)

    # update transaction log
    trans_log = trans_log.append({
        'date' : date,
        'position_id' : position['id'],
        'name' : position['name'],
        'price' : price,
        'qty' : position['qty'],
        'type' : 'close',
        'cost' : cost,
        'net_profit' : net_profit
    } , ignore_index=True)

    # update available balance
    ava_bal += position['initial_margin'] + net_profit - cost

    # update portfolio
    portfolio = portfolio.drop(portfolio_id)


def plotGraph(df):
    fig, axes = plt.subplots(nrows=2, sharex=True)
    axes[0].plot(df['DATE'], df['close'], label='Close')
    axes[0].plot(df['DATE'], df['DC_HIGH'], label='DC_High')
    axes[0].plot(df['DATE'], df['DC_LOW'], label='DC_Low')
    axes[0].legend()
    axes[1].plot(df['DATE'], df['MACD'], label='MACD', color='red')
    axes[1].plot(df['DATE'], df['SIGNAL'], label='Signal', color='blue')
    axes[1].legend()
    plt.show()
    

def strat_donchian_macd(df, df_next, d_index, d_row):
    # Donchian long signal
    if df.loc[d_index, 'close'] > df.loc[d_index, 'DC_HIGH']:
        qty = 1
        date = d_row['DATE']
        # place next month order if > last trading day
        if d_row['DATE'] >= last_trade_date:
            price = (df_next.loc[d_index, 'high'] + df_next.loc[d_index, 'low']) / 2
            name = 'HSI ' + (date + relativedelta(months=+1)).strftime('(%b %Y)')
        else:
            price = (d_row['high'] + d_row['low']) / 2
            name = 'HSI ' + date.strftime('(%b %Y)')
        openPosition(name, price, qty, 'long', date)

    # MACD long signal
    if df.loc[d_index - 1, 'HIST'] < 0 and df.loc[d_index, 'HIST'] > 0:
        # close existing short position in portfolio
        for p_index, p_row in portfolio.iterrows():
            if p_row['name'] == 'HSI ' + d_row['DATE'].strftime('(%b %Y)') and p_row['type'] == 'short':
                price = d_row['close']
                closePosition(p_index, price, d_row['DATE'])
                
    # Donchian short signal
    if df.loc[d_index, 'close'] < df.loc[d_index, 'DC_LOW']:
        qty = 1
        date = d_row['DATE']
        # place next month order if > last trading day
        if d_row['DATE'] >= last_trade_date:
            price = (df_next.loc[d_index, 'high'] + df_next.loc[d_index, 'low']) / 2
            name = 'HSI ' + (date + relativedelta(months=+1)).strftime('(%b %Y)')
        else:
            price = (d_row['high'] + d_row['low']) / 2
            name = 'HSI ' + date.strftime('(%b %Y)')
        openPosition(name, price, qty, 'short', date)

    # MACD short signal
    if df.loc[d_index - 1, 'HIST'] > 0 and df.loc[d_index, 'HIST'] < 0:
        # close existing long position in portfolio
        for p_index, p_row in portfolio.iterrows():
            if p_row['name'] == 'HSI ' + d_row['DATE'].strftime('(%b %Y)') and p_row['type'] == 'long':
                price = d_row['close']
                closePosition(p_index, price, d_row['DATE'])

    # last trading day
    if d_row['DATE'] == last_trade_date:
        for p_index, p_row in portfolio.iterrows():
            # close and renew all positions
            price = d_row['close']
            closePosition(p_index, price, d_row['DATE'])

            if d_row['DATE'] < pd.to_datetime(const.TEST_END_DATE):
                qty = p_row['qty']
                price = (df_next.loc[d_index, 'high'] + df_next.loc[d_index, 'low']) / 2
                date = d_row['DATE']
                name = 'HSI ' + (date + relativedelta(months=+1)).strftime('(%b %Y)')
                openPosition(name, price, qty, p_row['type'], date)


def strat_macd(df, df_next, d_index, d_row):
    # MACD long signal
    if df.loc[d_index - 1, 'HIST'] < 0 and df.loc[d_index, 'HIST'] > 0:
        # close existing short position in portfolio
        for p_index, p_row in portfolio.iterrows():
            if p_row['name'] == 'HSI ' + d_row['DATE'].strftime('(%b %Y)') and p_row['type'] == 'short':
                price = d_row['close']
                closePosition(p_index, price, d_row['DATE'])

        qty = 1
        date = d_row['DATE']
        # place next month order if > last trading day
        if d_row['DATE'] >= last_trade_date:
            price = (df_next.loc[d_index, 'high'] + df_next.loc[d_index, 'low']) / 2
            name = 'HSI ' + (date + relativedelta(months=+1)).strftime('(%b %Y)')
        else:
            price = (d_row['high'] + d_row['low']) / 2
            name = 'HSI ' + date.strftime('(%b %Y)')
        openPosition(name, price, qty, 'long', date)

    # MACD short signal
    if df.loc[d_index - 1, 'HIST'] > 0 and df.loc[d_index, 'HIST'] < 0:
        # close existing long position in portfolio
        for p_index, p_row in portfolio.iterrows():
            if p_row['name'] == 'HSI ' + d_row['DATE'].strftime('(%b %Y)') and p_row['type'] == 'long':
                price = d_row['close']
                closePosition(p_index, price, d_row['DATE'])

        qty = 1
        date = d_row['DATE']
        # place next month order if > last trading day
        if d_row['DATE'] >= last_trade_date:
            price = (df_next.loc[d_index, 'high'] + df_next.loc[d_index, 'low']) / 2
            name = 'HSI ' + (date + relativedelta(months=+1)).strftime('(%b %Y)')
        else:
            price = (d_row['high'] + d_row['low']) / 2
            name = 'HSI ' + date.strftime('(%b %Y)')
        openPosition(name, price, qty, 'short', date)

    # last trading day
    if d_row['DATE'] == last_trade_date:
        for p_index, p_row in portfolio.iterrows():
            # close and renew all positions
            price = d_row['close']
            closePosition(p_index, price, d_row['DATE'])

            if d_row['DATE'] < pd.to_datetime(const.TEST_END_DATE):
                qty = p_row['qty']
                price = (df_next.loc[d_index, 'high'] + df_next.loc[d_index, 'low']) / 2
                date = d_row['DATE']
                name = 'HSI ' + (date + relativedelta(months=+1)).strftime('(%b %Y)')
                openPosition(name, price, qty, p_row['type'], date)



##########################################################################################################



# load market data
df = pd.read_csv("hsi_spot.csv") 
df_next = pd.read_csv("hsi_next.csv") 


# calculate MACD, Donchian channel
macd, signal, hist = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
dc_low, dc_high = DONCH(df['low'], df['high'])
df['MACD'] = macd
df['SIGNAL'] = signal
df['HIST'] = hist
df['DC_HIGH'] = dc_high
df['DC_LOW'] = dc_low
df['DATE'] = pd.to_datetime(df['time_key'])


# run strategy
testData = (df['DATE'] >= const.TEST_START_DATE) & (df['DATE'] <= const.TEST_END_DATE)
for d_index, d_row in df.loc[testData].iterrows():
    last_trade_date = pd.to_datetime(const.MTH_END_TRADE_DATE[d_row['DATE'].strftime('%Y%m')])

    # dochian channel + macd
    strat_donchian_macd(df, df_next, d_index, d_row)

    # macd only
    # strat_macd(df, df_next, d_index, d_row)

            
        
print('Available balance:')
print(ava_bal)
print('Transaction log:')
print(trans_log)


# plot graph
plotGraph(df)