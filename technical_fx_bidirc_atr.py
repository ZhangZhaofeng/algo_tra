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
        self.status = {"side": "null", "entry_size": [], "entry_price": [],
                       "rest": 100000.}  # "nth":[entry_cash, entry_price]
        self.one_unit_btc = 0.01
        self.five_pricelines = [0, 0, 0, 0, 0]
        self.line_position_no = 0
        self.atr_init = 20000
        self.atr = self.atr_init

    def get_ATR(self, HIGH, LOW, CLOSE, timeperiod=14):  # price=1*N (N>61)
        ma_high = talib.ATR(HIGH, LOW, CLOSE, timeperiod)
        return ma_high

    def initialize_status(self):
        self.status = {"side": "null", "entry_size": [], "entry_price": [],
                       "rest": 100000.}  # "nth":[entry_cash, entry_price]

    def get_intermediate_value(self):
        if self.status["side"] == "null":
            return self.status["rest"]
        elif self.status["side"] == "long":
            length = len(self.status["entry_size"])
            assert (length == len(self.status["entry_price"]))
            value = 0.
            for i in range(length):
                value += self.status["entry_size"][i] * self.five_pricelines[i]

            value += self.status["rest"]
            return value
        elif self.status["side"] == "short":
            length = len(self.status["entry_size"])
            assert (length == len(self.status["entry_price"]))
            value = 0.
            for i in range(length):
                value += self.status["entry_size"][i] * self.status["entry_price"][i] - self.status["entry_size"][i] * \
                         (self.five_pricelines[i] - self.status["entry_price"][i])

            value += self.status["rest"]
            return value
        else:
            raise Exception("No such side type!")

    def get_total_value(self, current_price):
        if self.status["side"] == "null":
            return self.status["rest"]
        elif self.status["side"] == "long":
            length = len(self.status["entry_size"])
            assert (length == len(self.status["entry_price"]))
            value = 0.
            for i in range(length):
                value += self.status["entry_size"][i] * current_price

            value += self.status["rest"]
            return value
        elif self.status["side"] == "short":
            length = len(self.status["entry_size"])
            assert (length == len(self.status["entry_price"]))
            value = 0.
            for i in range(length):
                value += self.status["entry_size"][i] * self.status["entry_price"][i] - self.status["entry_size"][i] * (
                        current_price - self.status["entry_price"][i])

            value += self.status["rest"]
            return value
        else:
            raise Exception("No such side type!")

    # return beyond line no.(0~M) (e. g., N means price is within (N-1,N))
    def get_beyond_priceline_no(self, all_pricelines, price, side="long"):
        if side == "long":
            for i in range(len(all_pricelines)):
                if all_pricelines[i] > price:
                    return i;

            return len(all_pricelines)

        else:
            for i in range(len(all_pricelines)):
                if all_pricelines[i] < price:
                    return i;

            return len(all_pricelines)

    def clear_all_positions(self):
        self.status["rest"] = self.get_intermediate_value()
        self.status["entry_size"] = []
        self.status["entry_price"] = []
        self.status["side"] = "null"

    def append_fake_position(self):
        length = len(self.status["entry_size"])

        for i in range(length, 5):
            self.status["entry_size"].append(0)
            self.status["entry_price"].append(0)

    # can only be used when side is null
    def create_all_positions(self, close, side="long"):
        assert (self.status["side"] == "null")

        if side == "long":

            beyond_line_num = self.get_beyond_priceline_no(self.five_pricelines, close, side="long")

            self.status["side"] = "long"
            for i in range(beyond_line_num):
                self.status["entry_size"].append(self.one_unit_btc)
                self.status["entry_price"].append(self.five_pricelines[i])
                self.status["rest"] -= self.one_unit_btc * self.five_pricelines[i]

        else:
            beyond_line_num = self.get_beyond_priceline_no(self.five_pricelines, close, side="short")

            self.status["side"] = "short"
            for i in range(beyond_line_num):
                self.status["entry_size"].append(self.one_unit_btc)
                self.status["entry_price"].append(self.five_pricelines[i])
                self.status["rest"] -= self.one_unit_btc * self.five_pricelines[i]

    # To make the position be continuous to the previous unit, lines needs to be adjust at the start of current unit.
    def adjust_five_pricelines_v2(self, open, atr_prev, side="long"):
        delta = 10
        if side == "long":
            first_price = self.five_pricelines[0]
            atr = atr_prev
            if self.line_position_no < self.get_beyond_priceline_no(self.five_pricelines, open, side):
                for i in range(10000):
                    atr += delta
                    assert (i < 9999)
                    assert (delta > 0)
                    self.five_pricelines = [first_price, first_price + 0.2 * atr, first_price + 0.4 * atr,
                                            first_price + 0.7 * atr,
                                            first_price + atr]
                    if self.line_position_no >= self.get_beyond_priceline_no(self.five_pricelines, open, side):
                        print("long:atr=%f" % atr)
                        break

            elif self.line_position_no > self.get_beyond_priceline_no(self.five_pricelines, open, side):
                for i in range(10000):
                    atr -= delta
                    assert (i < 9999)
                    assert (delta > 0)
                    self.five_pricelines = [first_price, first_price + 0.2 * atr, first_price + 0.4 * atr,
                                            first_price + 0.7 * atr,
                                            first_price + atr]
                    if self.line_position_no <= self.get_beyond_priceline_no(self.five_pricelines, open, side):
                        print("long:atr=%f" % atr)
                        break
        elif side == "short":
            first_price = self.five_pricelines[0]
            atr = -(self.five_pricelines[4] - first_price)

            if self.line_position_no < self.get_beyond_priceline_no(self.five_pricelines, open, side):
                for i in range(10000):
                    atr += delta
                    assert (i < 9999)
                    assert (delta > 0)
                    self.five_pricelines = [first_price, first_price - 0.2 * atr, first_price - 0.4 * atr,
                                            first_price - 0.7 * atr,
                                            first_price - atr]
                    if self.line_position_no >= self.get_beyond_priceline_no(self.five_pricelines, open, side):
                        print("short:atr= %f" % atr)
                        break

            elif self.line_position_no > self.get_beyond_priceline_no(self.five_pricelines, open, side):
                for i in range(10000):
                    atr -= delta
                    assert (i < 9999)
                    assert (delta > 0)
                    self.five_pricelines = [first_price, first_price - 0.2 * atr, first_price - 0.4 * atr,
                                            first_price - 0.7 * atr,
                                            first_price - atr]

                    if self.line_position_no <= self.get_beyond_priceline_no(self.five_pricelines, open, side):
                        print("short:atr= %f" % atr)
                        break

        return atr

        # To make the position be continuous to the previous unit, lines needs to be adjust at the start of current unit.

    def adjust_five_pricelines(self, open, hi_price, lo_price, side="long"):
        atr = 0.
        if side == "long":
            prev_no = self.line_position_no
            assert (open > lo_price)
            assert (prev_no > 0)

            if prev_no == 1:
                atr = (open - lo_price) / 0.25
            elif prev_no == 2:
                atr = (open - lo_price) / 0.6
            elif prev_no == 3:
                atr = (open - lo_price) / 0.8
            elif prev_no == 4:
                atr = (open - lo_price) / 0.95
            elif prev_no == 5:
                atr = (open - lo_price) - 300
            else:
                raise Exception("Wrong prev_no")

            self.five_pricelines = [lo_price, lo_price + 0.5 * atr, lo_price + 0.7 * atr, lo_price + 0.9 * atr,
                                    lo_price + atr]

        elif side == "short":
            prev_no = self.line_position_no
            assert (open < hi_price)
            assert (prev_no > 0)

            if prev_no == 1:
                atr = (hi_price - open) / 0.25
            elif prev_no == 2:
                atr = (hi_price - open) / 0.6
            elif prev_no == 3:
                atr = (hi_price - open) / 0.8
            elif prev_no == 4:
                atr = (hi_price - open) / 0.95
            elif prev_no == 5:
                atr = (hi_price - open) - 300
            else:
                raise Exception("Wrong prev_no")

            self.five_pricelines = [hi_price, hi_price - 0.5 * atr, hi_price - 0.7 * atr, hi_price - 0.9 * atr,
                                    hi_price - atr]
        else:
            pass

        assert (atr > 0)

        return atr

    def run_once(self, open, close, hi_price, lo_price,fixed_unit):
        atr = self.atr

        if self.status["side"] == "long":
            if open < lo_price:
                lo_price = open - 1000

            self.five_pricelines = [lo_price, lo_price + 0.5 * atr, lo_price + 0.7 * atr, lo_price + 0.9 * atr,
                                    lo_price + atr]

            if self.line_position_no != self.get_beyond_priceline_no(self.five_pricelines, open, self.status["side"]):
                atr = self.adjust_five_pricelines(open, hi_price, lo_price, side="long")
                if self.line_position_no != self.get_beyond_priceline_no(self.five_pricelines, open,
                                                                         self.status["side"]):
                    print("long:after")
                    print(self.line_position_no)
                    print(self.get_beyond_priceline_no(self.five_pricelines, open, self.status["side"]))
                    # assert(0)

            if close >= lo_price:  # continue long

                self.clear_all_positions()
                self.create_all_positions(close, side="long")
            else:  # first time short after change position
                self.clear_all_positions()
                atr = self.atr_init

                if not fixed_unit:
                    self.one_unit_btc=round(self.status["rest"][0]*0.8/(close*5),2)
                self.five_pricelines = [lo_price, lo_price - 0.1 * atr, lo_price - 0.5 * atr, lo_price - 0.8 * atr,
                                        lo_price - atr]
                self.create_all_positions(close, side="short")
                self.status["side"] = "short"
        elif self.status["side"] == "short":
            if open > hi_price:
                hi_price = open + 1000

            self.five_pricelines = [hi_price, hi_price - 0.5 * atr, hi_price - 0.7 * atr, hi_price - 0.9 * atr,
                                    hi_price - atr]

            if self.line_position_no != self.get_beyond_priceline_no(self.five_pricelines, open,
                                                                     self.status["side"]):
                atr = self.adjust_five_pricelines(open, hi_price, lo_price, side="short")
                if self.line_position_no != self.get_beyond_priceline_no(self.five_pricelines, open,
                                                                         self.status["side"]):
                    print("short:after")
                    print(self.line_position_no)
                    print(self.get_beyond_priceline_no(self.five_pricelines, open, self.status["side"]))
                    print(self.five_pricelines)
                    print(open)
                    # assert (0)

            if close < hi_price:  # continue short
                self.clear_all_positions()
                self.create_all_positions(close, side="short")
            else:  # first time long after change position
                self.clear_all_positions()
                atr = self.atr_init

                if not fixed_unit:
                    self.one_unit_btc=round(self.status["rest"][0]*0.8/(close*5),2)

                self.five_pricelines = [hi_price, hi_price + 0.1 * atr, hi_price + 0.5 * atr, hi_price + 0.8 * atr,
                                        hi_price + atr]
                self.create_all_positions(close, side="long")
                self.status["side"] = "long"
        else:  # Null case#
            if open > lo_price and close < lo_price:
                self.five_pricelines = [lo_price, lo_price - 0.1 * atr, lo_price - 0.5 * atr, lo_price - 0.8 * atr,
                                        lo_price - atr]
                self.clear_all_positions()
                self.create_all_positions(close, side="short")
                self.status["side"] = "short"
            elif open < hi_price and close > hi_price:
                self.five_pricelines = [hi_price, hi_price + 0.1 * atr, hi_price + 0.5 * atr, hi_price + 0.8 * atr,
                                        hi_price + atr]
                self.clear_all_positions()
                self.create_all_positions(close, side="long")
                self.status["side"] = "long"
            else:
                pass

        value = self.get_total_value(close)
        isLong = 0
        isShort = 0
        if self.status["side"] == "long":
            isLong = 88888;
        elif self.status["side"] == "short":
            isShort = 55555;

        self.line_position_no = self.get_beyond_priceline_no(self.five_pricelines, close, self.status["side"])
        self.atr = atr

        return (value, isLong, isShort)

    def MA(self, ndarray, timeperiod=5):
        x = np.array([talib.SMA(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_HIGH_MA(self, HIGH):  # price=1*N (N>61)
        ma_high = self.MA(HIGH, 17) * 1.000
        return ma_high

    def get_LOW_MA(self, LOW):  # price=1*N (N>61)
        ma_low = self.MA(LOW, 17) * 1.000
        return ma_low

    def get_long_price(self, HIGH):
        ma_high = self.get_HIGH_MA(HIGH)
        return ma_high

    def get_short_price(self, LOW):
        ma_low = self.get_LOW_MA(LOW)
        return ma_low

    def publish_current_hilo_price(self, num=100, periods="1H"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)

        low_price_ma = self.get_short_price(low_price)
        high_price_ma = self.get_long_price(high_price)
        (buyprice, sellprice) = (high_price_ma[-1][0], low_price_ma[-1][0])
        a = (int(buyprice), int(sellprice))
        print(a)
        return (int(buyprice), int(sellprice))

    def simulate(self, num=100, periods="1m", end_offset=0):
        leverage = 1.0
        fee_ratio = 0.000  # trading fee percent
        fixed_unit=True
        ################Simulation#######################
        self.initialize_status()

        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time() - end_offset, num=num, periods=periods, converter=True)

        all = np.c_[time_stamp, open_price, high_price, low_price, close_price]
        long_price = self.get_long_price(high_price)
        short_price = self.get_short_price(low_price)

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(len(long_price))
        print(len(short_price))

        result = np.zeros([len(all), 10])
        for t in range(50, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)
            # current hour's operation price initialization
            hi_t = long_price[t]
            lo_t = short_price[t]
            open_t = all[t][1]
            high_t = all[t][2]
            low_t = all[t][3]
            close_t = all[t][4]

            (value_t, isLong, isShort) = self.run_once(open_t, close_t, hi_t, lo_t,fixed_unit)
            self.append_fake_position()

            result[t][0] = isLong
            result[t][1] = isShort
            result[t][2] = int(self.atr)
            result[t][3] = int(self.status["entry_price"][0])
            result[t][4] = int(self.status["entry_price"][1])
            result[t][5] = int(self.status["entry_price"][2])
            result[t][6] = int(self.status["entry_price"][3])
            result[t][7] = int(self.status["entry_price"][4])
            result[t][8] = self.one_unit_btc
            result[t][9] = int(value_t)
            print("value_t: %s" % value_t)
            value = value_t
            # self.clear_all_positions()

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, long_price, short_price, result]

        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                                     "16", "17"})

        print("============================")

        cwd = os.getcwd()
        data.to_csv(
            cwd + "_jpy.csv",
            index=True)

        return value


if __name__ == '__main__':
    # directly

    btc_charts = historical_fx.charts()

    (time_stamp, open_price, high_price, low_price, close_price) = btc_charts.get_price_array_till_finaltime()

    hilo = HILO()
    # simulate the past 24 hours
    # hilo.simulate(num=24 * 7 * 1 + 20, periods="1H", end_offset=3600 * 24 * 7 * 0)

    sum = 0.
    counter_sum = 0
    length = 20
    for i in range(length):
        value = hilo.simulate(num=1 * 24 * 7 * 1 + 50, periods="1H", end_offset=3600 * 24 * 7 * (i + 0))
        sum = sum + value
    # hilo.simulate(num=60*24*50+61, periods="1m", end_offset=0)
    # a=hilo.publish_current_limit_price(periods="1H")

    print(sum / length)
    print(counter_sum / length)

    # hilo.publish_current_hilo_price()
