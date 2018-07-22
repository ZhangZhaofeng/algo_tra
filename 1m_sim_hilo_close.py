#!/usr/bin/python3
# coding=utf-8


import talib
import numpy as np
import historical_fx
import os
import pandas as pd
# import plot_chart as plc
import matplotlib.pyplot as plt
# from matplotlib.finance import candlestick_ohlc as plot_candle
import time


class HILO:
    def __init__(self):
        print("HILO initialized")
        self.btc_charts = historical_fx.charts()

    def get_ATR(self, HIGH,LOW,CLOSE,timeperiod=14):  # price=1*N (N>61)
        ma_high=talib.ATR(HIGH,LOW,CLOSE,timeperiod)
        return ma_high

    def MA(self, ndarray, timeperiod=5):
        x = np.array([talib.SMA(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_HIGH_MA(self, HIGH):  # price=1*N (N>61)
        ma_high=self.MA(HIGH,7)
        return ma_high

    def get_LOW_MA(self, LOW):  # price=1*N (N>61)
        ma_low=self.MA(LOW,8)
        return ma_low

    def get_long_price(self, HIGH):
        ma_high=self.get_HIGH_MA(HIGH)
        return ma_high

    def get_short_price(self, LOW):
        ma_low = self.get_LOW_MA(LOW)
        return ma_low

    def publish_current_hilo_price(self, num=100, periods="1H"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)

        low_price_ma = self.get_short_price(low_price)
        high_price_ma = self.get_long_price(high_price)
        (buyprice, sellprice)=(high_price_ma[-1][0],low_price_ma[-1][0])
        a=(int(buyprice), int(sellprice))
        # print(a)
        return (int(buyprice), int(sellprice))

    def simulate(self, num=100, periods="1m" ,end_offset=0):
        mode=0  #0: both long and short;
                #1: only long;
                #2: only short;

        target_diff = 2000
        target_diff2 = 4000
        target_diff3 = 6000
        target_diff4 = 8000
        target_diff5 = 10000
        target_diff6 = 12000
        target_diff7 = 14000
        target_diff8 = 16000
        target_diff9 = 18000
        target_diff10 = 20000
        buffer=700
        temp_line= 0


        leverage = 1.0
        fee_ratio = 0.000  # trading fee percent
        ################Simulation#######################
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time() - end_offset, num=num, periods=periods, converter=True)


        all = np.c_[time_stamp, open_price, high_price, low_price, close_price]
        long_price = self.get_long_price(high_price)
        short_price = self.get_short_price(low_price)

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(len(long_price))
        print(len(short_price))


        amount = np.zeros([len(all), 8])
        long = False
        short = False
        cash = 10000.
        prev_cash=cash
        btc = 0.
        value = cash
        long_times = 0
        short_times = 0
        short_start_price= 0.
        long_start_price = 0.
        trade_back=0
        for t in range(50, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)
            #current hour's operation price initialization
            buy_price = long_price[t]
            sell_price = short_price[t]


            if not short and not long:
                if all[t][4] < sell_price and all[t][1] > sell_price:   #low price is lower than sell_price
                    #short starts
                    short = True
                    short_start_price = all[t][4]
                    trading_cash = cash
                    short_times += 1
                    amount[t][6] = 555
                    cash=0.

                elif all[t][4] > buy_price and all[t][1] < buy_price: # high price is higher than buy_price
                    # long starts
                    long = True
                    long_start_price = all[t][4]
                    trading_cash = cash
                    long_times += 1
                    amount[t][5] = 888
                    cash = 0.

            elif short and not long:
                if all[t][1]>buy_price:
                    buy_price=all[t][1]-30

                if all[t][4] > buy_price:  # close price is higher than reverse_price
                    # short over
                    short = False
                    short_over_price=all[t][4]
                    cash = (1+(short_start_price-short_over_price)/short_start_price)*trading_cash
                    if cash<0:
                        cash==0
                    short_start_price = 0.
                    trading_cash = 0.
                    amount[t][5] = 888

                    # long starts
                    long = True
                    long_start_price = all[t][4]
                    trading_cash = cash
                    cash = 0.
                    long_times += 1
                    amount[t][5] = 888
                elif short_start_price-all[t][4]>target_diff and temp_line==0:
                    temp_line = short_start_price - target_diff + buffer
                elif short_start_price-all[t][4]>target_diff2:
                    temp_line = short_start_price - target_diff2 + buffer
                elif short_start_price-all[t][4]>target_diff3:
                    temp_line = short_start_price - target_diff3 + buffer
                elif short_start_price-all[t][4]>target_diff4:
                    temp_line = short_start_price - target_diff4 + buffer
                elif short_start_price-all[t][4]>target_diff6:
                    temp_line = short_start_price - target_diff6 + buffer
                elif short_start_price-all[t][4]>target_diff7:
                    temp_line = short_start_price - target_diff7 + buffer
                elif short_start_price-all[t][4]>target_diff8:
                    temp_line = short_start_price - target_diff8 + buffer
                elif short_start_price-all[t][4]>target_diff9:
                    temp_line = short_start_price - target_diff9 + buffer
                elif short_start_price-all[t][4]>target_diff10:
                    temp_line = short_start_price - target_diff10 + buffer
                elif all[t][4] >temp_line and temp_line >0:
                    # short over
                    short = False
                    short_over_price = all[t][4]
                    cash = (1 + (short_start_price - short_over_price) / short_start_price) * trading_cash
                    if cash < 0:
                        cash == 0
                    short_start_price = 0.
                    trading_cash = 0.
                    amount[t][5] = 444
                    temp_line=0


            elif not short and long:
                if all[t][1]<sell_price:
                    sell_price=all[t][1]+30

                if all[t][4] < sell_price:  # close price is lower than reverse_price
                    #long over
                    long = False
                    long_over_price=all[t][4]
                    cash = (1 - (long_start_price - long_over_price) / long_start_price) * trading_cash
                    if cash < 0:
                        cash == 0
                    long_start_price = 0.
                    trading_cash = 0.
                    amount[t][6] = 555

                    # short starts
                    short = True
                    short_start_price = all[t][4]
                    trading_cash = cash
                    cash=0.
                    short_times += 1
                    amount[t][6] = 555
                elif all[t][4]-long_start_price>target_diff and temp_line==0:
                    temp_line=long_start_price+target_diff-buffer
                elif long_start_price-all[t][4]>target_diff2:
                    temp_line = long_start_price+target_diff2-buffer
                elif long_start_price-all[t][4]>target_diff3:
                    temp_line = long_start_price+target_diff3-buffer
                elif long_start_price-all[t][4]>target_diff4:
                    temp_line = long_start_price+target_diff4-buffer
                elif long_start_price-all[t][4]>target_diff5:
                    temp_line = long_start_price+target_diff5-buffer
                elif long_start_price-all[t][4]>target_diff6:
                    temp_line = long_start_price+target_diff6-buffer
                elif long_start_price-all[t][4]>target_diff7:
                    temp_line = long_start_price+target_diff7-buffer
                elif long_start_price-all[t][4]>target_diff8:
                    temp_line = long_start_price+target_diff8-buffer
                elif long_start_price-all[t][4]>target_diff9:
                    temp_line = long_start_price+target_diff9-buffer
                elif long_start_price-all[t][4]>target_diff10:
                    temp_line = long_start_price+target_diff10-buffer
                elif all[t][4]<temp_line and temp_line>0:
                    long = False
                    long_over_price = all[t][4]
                    cash = (1 - (long_start_price - long_over_price) / long_start_price) * trading_cash
                    if cash < 0:
                        cash == 0
                    long_start_price = 0.
                    trading_cash = 0.
                    amount[t][6] = 444
                    temp_line=0


            #result log
            if cash==0 and long:
                value = (1-(long_start_price-all[t][4])/long_start_price)*trading_cash
                if value<0:
                    print("Asset reset to zero")
                    break
            elif cash==0 and short:
                value = (1+(short_start_price-all[t][4])/short_start_price)*trading_cash
                if value<0:
                    print("Asset reset to zero")
                    break
            else:
                value = cash


            amount[t][0] = buy_price
            amount[t][1] = sell_price
            amount[t][2] = cash
            amount[t][3] = btc
            amount[t][4] = value
            print("value: %s" % value)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, long_price,short_price, amount]

        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10","11","12","13", "14", "15"})

        print("============================")
        print(long_times)
        print(short_times)

        cwd = os.getcwd()
        data.to_csv(
            cwd + "_jpy.csv",
            index=True)

        print("trade_back= %s "  %trade_back)

        return value, trade_back


if __name__ == '__main__':
    # directly

    btc_charts = historical_fx.charts()

    (time_stamp, open_price, high_price, low_price, close_price) = btc_charts.get_price_array_till_finaltime()

    hilo = HILO()


    sum = 0.
    counter_sum= 0
    length = 4
    for i in range(length):
        value,counter = hilo.simulate(num=60*24*1 + 50, periods="1m", end_offset=3600 * 24 * (i + 0))
        sum = sum + value
        counter_sum = counter_sum+counter


    print(sum / length)
    print(counter_sum / length)

