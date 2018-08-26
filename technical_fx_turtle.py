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

    def get_HIGH_MA(self, HIGH):  # price=1*N (N>61)
        ma_high=self.T_MAX(HIGH,23)
        return ma_high

    def get_LOW_MA(self, LOW):  # price=1*N (N>61)
        ma_low=self.T_MIN(LOW,23)
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
        (buyprice, sellprice)=(high_price_ma[-2][0],low_price_ma[-2][0])
        a=(int(buyprice), int(sellprice))
        #print(a)
        return (int(buyprice), int(sellprice), int(close_price[-1]))

