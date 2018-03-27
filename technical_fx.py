#!/usr/bin/python3
# coding=utf-8


import talib
import numpy as np
import historical
import os
import pandas as pd
# import plot_chart as plc
import matplotlib.pyplot as plt
# from matplotlib.finance import candlestick_ohlc as plot_candle
import time


class GMMA:
    def __init__(self):
        print("GMMA initialized")
        self.btc_charts = historical.charts()

    def EMA(self, ndarray, timeperiod=4):
        x = np.array([talib.EMA(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_GMMA(self, price):  # price=1*N (N>61)
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

    def get_current_ema_realtime(self, last_ema, current_price, N):
        return current_price * 2 / (N + 1) + last_ema * (N - 1) / (N + 1)

    def get_current_GMMA_realtime(self, last_ema_all, current_price):  # price=1*N (N>61)
        ema3 = self.get_current_ema_realtime(last_ema_all[0], current_price, 3)
        ema5 = self.get_current_ema_realtime(last_ema_all[1], current_price, 5)
        ema8 = self.get_current_ema_realtime(last_ema_all[2], current_price, 8)
        ema10 = self.get_current_ema_realtime(last_ema_all[3], current_price, 10)
        ema12 = self.get_current_ema_realtime(last_ema_all[4], current_price, 12)
        ema15 = self.get_current_ema_realtime(last_ema_all[5], current_price, 15)
        ema30 = self.get_current_ema_realtime(last_ema_all[6], current_price, 30)
        ema35 = self.get_current_ema_realtime(last_ema_all[7], current_price, 35)
        ema40 = self.get_current_ema_realtime(last_ema_all[8], current_price, 40)
        ema45 = self.get_current_ema_realtime(last_ema_all[9], current_price, 45)
        ema50 = self.get_current_ema_realtime(last_ema_all[10], current_price, 50)
        ema60 = self.get_current_ema_realtime(last_ema_all[11], current_price, 60)

        return np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]

    def get_current_GMMA_gradient_realtime(self, last_ema_all, current_price, periods):
        current_ema_all = self.get_current_GMMA_realtime(last_ema_all, current_price)
        gradient = np.zeros([1, 12])

        # print(current_ema_all)

        for i in range(0, 12):
            gradient[0][i] = (current_ema_all[0][i] - last_ema_all[i]) / float(
                self.btc_charts.period_converter(periods))

        grad_w = np.zeros(2)
        w_short = np.matrix([0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0., 0., 0., 0., 0., 0.])
        w_long = np.matrix([0., 0., 0., 0., 0., 0., 0.2, 0.2, 0.2, 0.2, 0.1, 0.1])

        grad_w[0] = w_short * gradient[0].reshape(12, 1)
        grad_w[1] = w_long * gradient[0].reshape(12, 1)

        return (gradient, grad_w)

    def get_sellprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] < 0.0:
                break
            price -= delta

        return price

    def get_buyprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] > 0.2:
                break
            price += delta

        return price

    def get_divsellprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] > 15:
                break
            price += delta

        return price

    def get_divbuyprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] < -100:
                break
            price -= delta

        return price

    def get_GMMA_gradient(self, ema, periods):
        assert (len(ema) > 61)
        gradient = np.zeros([len(ema), 12])
        # print(gradient)

        # compute gradient for 12 EMA lines respectively.
        for t in range(61, len(ema)):
            for i in range(0, 12):
                gradient[t][i] = (ema[t][i] - ema[t - 1][i]) / float(self.btc_charts.period_converter(periods))
                # print("grad=",gradient[t][i])

        # compute weighted composite gradients for both 6 long and 6 short EMA lines, respectively.
        grad_w = np.zeros([len(ema), 2])
        w_short = np.matrix([0.1, 0.1, 0.1, 0.1, 0.2, 0.4, 0., 0., 0., 0., 0., 0.])
        w_long = np.matrix([0., 0., 0., 0., 0., 0., 0.2, 0.2, 0.2, 0.2, 0.1, 0.1])

        for t in range(len(gradient)):
            grad_w[t][0] = w_short * gradient[t].reshape(12, 1)
            grad_w[t][1] = w_long * gradient[t].reshape(12, 1)

        return grad_w

    def get_GMMA_divergence_ratio(self, ema):
        short_term_gmma, long_term_gmma = np.hsplit(ema, [6])
        divergence_ratio = np.zeros([len(ema), 2])
        for t in range(61, len(ema)):
            divergence_ratio[t][0] = max(short_term_gmma[t]) / min(short_term_gmma[t])
            divergence_ratio[t][1] = max(long_term_gmma[t]) / min(long_term_gmma[t])

        return divergence_ratio

    def plot_chart_tillnow_to_csv(self, num=100, periods="1m"):
        while 1:
            try:
                (time_stamp, open_price, high_price, low_price,
                 close_price) = self.btc_charts.get_price_array_till_finaltime(num=num, periods=periods,
                                                                               converter=False)
                (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(
                    close_price)
                ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
                break
            except Exception:
                continue

        plot_all = np.c_[
            time_stamp, open_price.astype(int), high_price.astype(int), low_price.astype(int), close_price.astype(int)]
        # print(ema)

        figure, ax = plt.subplots()
        # plot_candle(ax, plot_all, width=0.4, colorup='#77d879', colordown='#db3f3f')
        plt.plot(time_stamp, ema)
        plt.show()

    def save_chart_tillnow_to_csv(self, num=62, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            num=num, periods=periods, converter=False)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]

        print(all)
        print("all")
        cwd = os.getcwd()
        data.to_csv(
            cwd + ".csv",
            index=True)

    def publish_current_limit_price(self, num=100, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        ema_latest_hour = ema[len(ema) - 1]
        open_curr = close_price[len(close_price) - 1]

        [a,b]=self.get_current_GMMA_gradient_realtime(ema_latest_hour.astype(float), open_curr.astype(float), periods)
        grad_weighted=b[0]
        sellprice = self.get_sellprice(ema_latest_hour.astype(float), open_curr.astype(float), periods)
        buyprice = self.get_buyprice(ema_latest_hour.astype(float), open_curr.astype(float), periods)
        print("Current grad_weighted= %s" %b[0])
        print([time_stamp[len(time_stamp) - 1], open_curr[0], buyprice[0], sellprice[0]])
        return (buyprice, sellprice, grad_weighted)

    def lowest_in_rest_hour(self, final_unixtime, buy_price):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp = final_unixtime, num=3, periods="15m", converter=True)

        all=np.c_[time_stamp, open_price, high_price, low_price, close_price]

        print(all)

        assert open_price[0] <=buy_price
        for i in range(len(close_price)):
            low_price[i]<=buy_price
            break

        lowest_price=buy_price
        for j in range(i, len(close_price)):
            if low_price[i]<lowest_price:
                lowest_price=close_price[i]

        return lowest_price


    def simulate(self, num=100, periods="1m" ,end_offset=0):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time() - end_offset, num=num, periods=periods, converter=True)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        div_ratio = self.get_GMMA_divergence_ratio(ema)

        grad_w = self.get_GMMA_gradient(ema, periods)

        all = np.c_[time_stamp, open_price, high_price, low_price, close_price, ema, grad_w]

        # print(len(all))

        amount = np.zeros([len(all), 7])
        hold = False
        cash = 10000.
        btc = 0.
        value = cash
        buy_times = 0
        sell_times = 0
        prev_cash = 0.
        counter=0
        for t in range(61, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)

            leverage=1.0
            # print(ema[t - 1])
            fee_ratio=0.000 #trading fee percent
            if hold == False:
                buy_price = self.get_buyprice(ema[t - 1], all[t][1], periods)
                sell_price = self.get_sellprice(ema[t - 1], all[t][1], periods)
                div_buyprice = 0. #self.get_divbuyprice(ema[t - 1], all[t][1], periods)
                # if all[t][17] > 0.1 and all[t][17] < 1.3 and all[t][18] > 0.0 and div_ratio[t][0]<1.05 :
                if all[t][2] > buy_price:  # and #all[t-1][18] > 0.0:  #high price is higher than buy_price
                    hold = True
                    prev_cash=cash
                    btc = cash*leverage / buy_price*(1-fee_ratio)
                    cash = 0.
                    buy_times += 1
                    prev_buy_price=buy_price
                    amount[t][5] = 888
                    if all[t][4] < sell_price:  # if close < sell_price, sell within current hour
                        hold = False
                        cash = sell_price * btc * (1 - fee_ratio) - (leverage - 1) * prev_cash
                        btc = 0.
                        sell_times += 1
                        amount[t][6] = 666
                elif all[t][3] < div_buyprice:  # sell if too high
                    hold = True
                    prev_cash=cash
                    btc = cash*leverage / div_buyprice*(1-fee_ratio)
                    cash = 0.
                    buy_times += 1
                    prev_buy_price=buy_price
                    amount[t][5] = 999
            elif hold == True:
                buy_price = self.get_buyprice(ema[t - 1], all[t][1], periods)
                sell_price = self.get_sellprice(ema[t - 1], all[t][1], periods)
                div_sellprice = self.get_divsellprice(ema[t - 1], all[t][1], periods)
                assert (all[t][1] >= sell_price)
                if all[t][4] < sell_price:  # close price is lower than sell_price
                    hold = False
                    # print(prev_cash)
                    cash = sell_price * btc*(1-fee_ratio)- (leverage-1)*prev_cash
                    btc = 0.
                    sell_times += 1
                    prev_sell_price= sell_price
                    amount[t][6] = 555
                elif all[t][2]>div_sellprice: # buy if too low
                    hold = False
                    # print(prev_cash)
                    cash = div_sellprice * btc * (1 - fee_ratio) - (leverage - 1) * prev_cash
                    btc = 0.
                    sell_times += 1
                    prev_sell_price = sell_price
                    amount[t][6] = 777

            if cash == 0:
                value = all[t][4] * btc- (leverage-1)*prev_cash
            else:
                value = cash

            amount[t][0] = buy_price
            amount[t][1] = sell_price
            amount[t][2] = cash
            amount[t][3] = btc
            amount[t][4] = value
            print("value: %s" % value)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60, grad_w, amount]

        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                                     "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"})

        print("============================")
        print(buy_times)
        print(sell_times)

        cwd = os.getcwd()
        data.to_csv(
            cwd + "_jpy.csv",
            index=True)

        print(counter)

        return value


if __name__ == '__main__':
    # directly

    btc_charts = historical.charts()

    (time_stamp, open_price, high_price, low_price, close_price) = btc_charts.get_price_array_till_finaltime()

    # print(close_price)

    gmma = GMMA()
    # gmma.save_chart_tillnow_to_csv(num=1000, periods="1H")
    # gmma.simulate(num=24 *30*10 + 61, periods="1H",end_offset=3600*24*30*0)
    # gmma.simulate(num=60*24*6+61, periods="1H", end_offset=0)
    # a=gmma.publish_current_limit_price(periods="1H")

    sum = 0.
    length = 8
    for i in range(length):
        value = gmma.simulate(num=24 * 30 * 1 + 61, periods="1H", end_offset=3600 * 24 * 30 * i)
        sum = sum + value
    # gmma.simulate(num=60*24*50+61, periods="1m", end_offset=0)
    # a=gmma.publish_current_limit_price(periods="1H")

    print(sum / length)
