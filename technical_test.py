#!/usr/bin/python3
# coding=utf-8


import talib
import numpy as np
import historical
import os
import pandas as pd
import plot_chart as plc
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ohlc as plot_candle


class GMMA:
    def __init__(self):
        print("GMMA initialized")
        self.btc_charts = historical.charts()

    def EMA(self, ndarray, timeperiod=4):
        x = np.array([talib.EMA(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_GMMA(self,price):
        ema3 = self.EMA(price, 3)
        ema5 = self.EMA(price, 5)
        ema8 = self.EMA(price, 8)
        ema10 = self.EMA(price, 10)
        ema12 = self.EMA(price, 12)
        ema15 = self.EMA(price, 15)
        ema30 = self.EMA(price, 30)
        ema35 = self.EMA(price, 35)
        ema40 = self.EMA(price, 40)
        ema45 = self.EMA(price, 45)
        ema50 = self.EMA(price, 50)
        ema60 = self.EMA(price, 60)

        return (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60)

    def plot_chart_tillnow_to_csv(self, num=100, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            num=num, periods=periods, converter=False)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)

        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]

        plot_all = np.c_[
            time_stamp, open_price.astype(int), high_price.astype(int), low_price.astype(int), close_price.astype(int)]
        print(ema)

        figure, ax = plt.subplots()
        plot_candle(ax, plot_all, width=0.4, colorup='#77d879', colordown='#db3f3f')
        plt.plot(time_stamp, ema)
        plt.show()

    def save_chart_tillnow_to_csv(self, num=100, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            num=num, periods=periods, converter=False)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        all = np.c_[time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                                     "16", "17"})

        print(all)
        print("all")
        cwd = os.getcwd()
        data.to_csv(
            cwd + ".csv",
            index=True)

    def simulate(self,num=100, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            num=num, periods=periods, converter=False)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]

        gradient=np.zeros([len(all),12])
        print(gradient)
        for t in range(61, len(all)):
            for i in range(5,17):
                gradient[t][i-5]= (all[t][i]-all[t-1][i])/ float(self.btc_charts.period_converter(periods))
                # print("grad=",gradient[t][i])

                w_short=np.matrix([0.2,0.2,0.2,0.2,0.1,0.1, 0., 0., 0., 0., 0., 0.])
                w_long=np.matrix([ 0., 0., 0., 0., 0., 0., 0.2,0.2,0.2,0.2,0.1,0.1])

        grad_w=np.zeros([len(all),2])

        for t in range(len(gradient)):
                grad_w[t][0]=w_short*gradient[t].reshape(12,1)
                grad_w[t][1] = w_long * gradient[t].reshape(12,1)

        print(grad_w)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60,grad_w]
        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                                     "16", "17","18", "19"})

        cwd = os.getcwd()
        data.to_csv(
            cwd + ".csv",
            index=True)



if __name__ == '__main__':
    # directly

    btc_charts = historical.charts()

    (time_stamp, open_price, high_price, low_price, close_price) = btc_charts.get_price_array_till_finaltime()

    print(close_price)

    gmma = GMMA()
    # gmma.save_chart_tillnow_to_csv(num=1000, periods="1H")
    gmma.simulate(num=200, periods="1H")
