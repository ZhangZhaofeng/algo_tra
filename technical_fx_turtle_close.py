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
        #print("HILO initialized")
        self.btc_charts = historical_fx.charts()

    def T_MAX(self, ndarray, timeperiod=5):
        x = np.array([talib.MAX(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def T_MIN(self, ndarray, timeperiod=5):
        x = np.array([talib.MIN(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_HIGH_MA(self, HIGH, num=39):  # price=1*N (N>61)
        ma_high=self.T_MAX(HIGH,num)
        return ma_high

    def get_LOW_MA(self, LOW, num=39):  # price=1*N (N>61)
        ma_low=self.T_MIN(LOW,num)
        return ma_low

    def get_long_price(self, HIGH, num=39):
        ma_high=self.get_HIGH_MA(HIGH, num)
        return ma_high

    def get_short_price(self, LOW, num=39):
        ma_low = self.get_LOW_MA(LOW, num)
        return ma_low

    def publish_current_hilo_price(self, num=100, periods="1H"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)
        midhigh, midlow = self.get_mid_hilo(open_price, high_price, low_price, close_price)
        low_price_ma = self.get_short_price(midlow)
        high_price_ma = self.get_long_price(midhigh)
        low_price_ma_half = self.get_short_price(low_price, 19)
        high_price_ma_half = self.get_long_price(high_price, 19)
        low_price_real = self.get_short_price(low_price, 39)
        high_price_real = self.get_long_price(high_price, 39)

        (buyprice, sellprice)=(high_price_ma[-2][0],low_price_ma[-2][0])
        (quitshort, quitlong) = (high_price_ma_half[-2][0], low_price_ma_half[-2][0])
        (inhoursell, inhourbuy) = (low_price_real[-2][0],high_price_real[-2][0])
        #print(a)
        return (int(buyprice), int(sellprice), int(close_price[-1]), int(high_price[-1]), int(low_price[-1]), int(quitshort), int(quitlong), int(inhourbuy),int(inhoursell))

    def get_mid_hilo(self, open, high, low, close):
        mid_factor = 0.5
        mid_high = []
        mid_low = []
        for i in range(0,len(open)):
            if open[i] != 0 and high[i] != 0 and low[i] != 0 and close[i] != 0:
                if open[i] > close[i]:
                    midhigh = (high[i] - open[i]) * mid_factor + open[i]
                    midlow = close[i] - (close[i] - low[i]) * mid_factor
                else:
                    midhigh = (high[i] - close[i]) * mid_factor + close[i]
                    midlow = open[i] - (open[i] - low[i]) * mid_factor
                mid_high.append(midhigh)
                mid_low.append(midlow)
            else:
                mid_high.append(0)
                mid_low.append(9999999)
        nparray_mid_high = np.array(mid_high)
        nparray_mid_low = np.array(mid_low)
        return(nparray_mid_high, nparray_mid_low)


if __name__ == '__main__':
    hilo = HILO()
    result = hilo.publish_current_hilo_price()
    print(result)