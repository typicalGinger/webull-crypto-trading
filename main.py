from webull import webull, endpoints
from webull.streamconn import StreamConn
import paho.mqtt.client as mqtt
import numpy as np
import pandas as pd
from datetime import datetime
import time
import json
import talib._ta_lib as ta

symbol = 'BTC/USD'
period = None
timeframe = None
hist = []
new_hist = []
wb = webull()
f = None
loginInfo = None
webullpassword = open('C:\\Account IDs\\email.txt', 'r').read()
email = open('C:\\Account IDs\\webullpassword.txt', 'r').read()

def login():
    print("Logging in to WeBull...")
    #login to Webull
    try:
        f = open("C:\\Account IDs\\webulltoken.txt", "r")
        loginInfo = json.load(f)
    except:
        print("First time login.")
    #If first time save login as token
    if not loginInfo:
        wb.get_mfa(email) #mobile number should be okay as well.
        code = input('Enter MFA Code : ')
        loginInfo = wb.login(email, webullpassword, 'My Device', code)
        f = open("C:\\Account IDs\\webulltoken.txt", "w")
        f.write(json.dumps(loginInfo))
        f.close()
    else:
        wb.refresh_login()
        loginInfo = wb.login(email, webullpassword)
    print('Logged In!')
    return loginInfo

def get_data():
    tickerID = wb.get_ticker(symbol)
    print(tickerID)
    print('ok')
    hist = wb.get_bars(stock=symbol.upper(), interval='m1', count=20)
    hist = pd.DataFrame(hist)
    calc_ema(hist)
    return hist

def calc_ema(dataframe):
    dataframe['ema5'] = ta.EMA(dataframe['close'],timeperiod=5)
    dataframe['ema10'] = ta.EMA(dataframe['close'],timeperiod=10)
    dataframe['ema20'] = ta.EMA(dataframe['close'],timeperiod=20)
    return dataframe

def buy_sell_calc(self, dataframe, ticker):
    # make sure we get the actual symbol
    ticker_symbol = ticker['symbol']
    # check if we can sell
    #TODO can probably add check if ticker_symbol postion is None so that it doesn't have to calculate all of this
    if (dataframe['ema5'][dataframe.index[-1]] > dataframe['ema10'][dataframe.index[-1]] and dataframe['ema5'][dataframe.index[-1]] > dataframe['ema20'][dataframe.index[-1]] and dataframe['ema10'][dataframe.index[-1]] > dataframe['ema20'][dataframe.index[-1]]):
        if (dataframe['ema5'][dataframe.index[-2]] > dataframe['ema10'][dataframe.index[-2]] and dataframe['ema5'][dataframe.index[-2]] > dataframe['ema20'][dataframe.index[-2]] and dataframe['ema10'][dataframe.index[-2]] > dataframe['ema20'][dataframe.index[-2]]): # making sure the it is tending to move upwards
            if (((dataframe['ema5'][dataframe.index[-1]]-dataframe['ema10'][dataframe.index[-1]])/dataframe['ema10'][dataframe.index[-1]]*100) > .5 and ((dataframe['ema5'][dataframe.index[-1]]-dataframe['ema20'][dataframe.index[-1]])/dataframe['ema20'][dataframe.index[-1]]*100) > 2):
                if self.get_positions_sell(ticker_symbol) is not None:
                    qty, orderside = self.get_positions_sell(ticker_symbol)
                    if orderside == 'long':
                        #limit_price = round(dataframe['close'][dataframe.index[-1]],2) #TODO either take out limit for sell or make it from low column not close
                        self.submitOrder_sell(qty,ticker_symbol,'sell')
    # check if we can buy
    if (dataframe['ema5'][dataframe.index[-1]] < dataframe['ema10'][dataframe.index[-1]] and dataframe['ema5'][dataframe.index[-1]] < dataframe['ema20'][dataframe.index[-1]] and dataframe['ema10'][dataframe.index[-1]] < dataframe['ema20'][dataframe.index[-1]]):
        if (dataframe['ema5'][dataframe.index[-2]] < dataframe['ema10'][dataframe.index[-2]] and dataframe['ema5'][dataframe.index[-2]] < dataframe['ema20'][dataframe.index[-2]] and dataframe['ema10'][dataframe.index[-2]] < dataframe['ema20'][dataframe.index[-2]]):
            if (dataframe['ema5'][dataframe.index[-3]] < dataframe['ema10'][dataframe.index[-3]] and dataframe['ema5'][dataframe.index[-3]] < dataframe['ema20'][dataframe.index[-3]] and dataframe['ema10'][dataframe.index[-3]] < dataframe['ema20'][dataframe.index[-3]]):
                can_buy = self.get_positions_buy(ticker_symbol)
                if can_buy == True:
                    quantity = self.calc_num_of_stocks(dataframe)
                    #limit = round(dataframe['close'][dataframe.index[-1]],2)
                    stop = str(round(dataframe['close'][dataframe.index[-1]]*.95,2))
                    stop_loss = {"stop_price": stop, "limit_price": stop}
                    self.submitOrder_buy(quantity,ticker_symbol,'buy',stop_loss)

def main():
    loginInfo = login()
    hist = get_data()
    conn = StreamConn(debug_flg=False)
    if not loginInfo['accessToken'] is None and len(loginInfo['accessToken']) > 1:
        conn.connect(loginInfo['uuid'], access_token=loginInfo['accessToken'])
    else:
        conn.connect(wb.did)
    ct = datetime.now().strftime("%S")
    while ct != "58":
        ct = datetime.now().strftime("%S")
        if ct == "58":
            continue
    conn.subscribe(symbol)
    while True:
        try:
            new_hist = wb.get_bars(stock=symbol.upper(), interval='m1', count=1)
            new_hist = pd.DataFrame(new_hist)
            hist = hist.append(new_hist, ignore_index=True)
            calc_ema(hist)
            if len(hist) > 25:
                hist = hist.drop(hist.index[0])
            print(hist)
            print(wb.get_positions())
            time.sleep(60)
        except Exception as e:
            print(f'Error: {str(e)}')

if __name__ == '__main__':
    main()