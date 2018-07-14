#!/usr/bin/python3
# coding=utf-8

import time
from tradingapis.bitflyer_api import pybitflyer
import keysecret as ks
import time
import datetime as dt
import predict
import sys
import technical_fx_bidirc as tfb
import math
import apis

from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib


class Tenlines:
    def __init__(self):
        print("Tenlines Algo Starts")
        self.hilo = tfb.HILO()
        # print(mytrade.get_asset_quoinex())

        print("Initializing Bitflyer API ")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))

        self.my_status = {"position": 0.04, "rest": 100000.}  # "nth":[entry_cash, entry_price]
        self.each_size = 0.01
        self.atr_ratio = [0.0, 0.2, 0.4, 0.7, 1.0]

    # print latest (hi, lo) prices
    def get_hilo_price(self):
        return self.hilo.publish_current_hilo_price()

    def get_current_bid_ask(self):
        while 1:
            try:
                [bid, ask] = apis.get_bid_ask_bitflyer('FX_BTC_JPY')
                break
            except Exception:
                continue

        return (round(bid, 0), round(ask, 0))

    def get_current_price(self, num=5):
        trade_history = self.bitflyer_api.executions(product_code='FX_BTC_JPY', count=num)
        total_size = 0.0
        cur_price = 0.0
        for i in trade_history:
            total_size += i['size']

        for i in trade_history:
            cur_price += i['size'] / total_size * i['price']

        return (math.floor(cur_price))

    # can be called at any time within current hour
    def get_next_hour(self):
        next_hour = dt.datetime.fromtimestamp(time.time() - time.time() % 3600 + 3680)

        print(next_hour.strftime('%Y/%m/%d,%H:%M:%S'))
        return next_hour.timestamp()

    def get_require_colleral_and_type(self):
        # need work
        # print(self.bitflyer_api.getcollateral())
        # print(self.bitflyer_api.getpositions(product_code='FX_BTC_JPY'))
        #
        # print(self.bitflyer_api.getparentorder(parent_order_id="JCP20180704-142433-465111", product_code="FX_BTC_JPY"))
        print(self.bitflyer_api.getparentorders(child_order_state='ACTIVE', product_code="FX_BTC_JPY", count=1))
        # print(self.bitflyer_api.getchildorders(product_code='FX_BTC_JPY',child_order_state="ACTIVE" ))
        # print(self.bitflyer_api.gettradingcommission(product_code='FX_BTC_JPY'))
        # self.bitflyer_api.cancelallchildorders(product_code='FX_BTC_JPY')

        if 1:
            require_colleral = 0.0
            type = "none"
        elif 0:
            require_colleral = 5000.
            type = "long"
        elif 0:
            require_colleral = 5000.
            type = "short"
        return (require_colleral, type)

    def place_stop_order(self, conditional_price, long_short, type, slide=500):
        # need work
        return True

    def check_position(self):
        # need work
        if 1:
            return "long"
        elif 0:
            return "short"
        else:
            return "none"

    def check_order(self, long_short):
        # need work
        (require_colleral, type) = self.get_require_colleral_and_type()
        if require_colleral > 0.0 and long_short == type:
            return True
        else:
            return False

    def verify_order(self, long_short):
        counter = 0
        while 1:
            if self.check_order(long_short):
                return True
            elif counter > 20:
                return False
            else:
                time.sleep(5)
                counter += 1

    def verify_order_or_position(self, long_short):
        # Wait until the placed order is verified successfully
        if not self.verify_order(long_short):
            if self.check_position() != long_short:
                print("Order verification fails. Trying again")
            else:
                print("Order is filled immediately")
        else:
            print("Order is verified")

    def adjust_hilo(self, hilo, open):
        (hi, lo) = hilo
        if self.my_status["position"] >0.0 and open < hi:
            hi = open - 1000
        elif self.my_status["position"] <0.0 and open > lo:
            lo = open + 1000
        elif self.my_status["position"] == 0.0 and open > hi:
            hi = open + 1000
        elif self.my_status["position"] == 0.0 and open < lo:
            lo = open - 1000
        else: #regular case, do nothing
            pass

        return (hi, lo)

    def get_beyond_priceline_no(self, all_pricelines, price):
        for i in range(len(all_pricelines)):
            if all_pricelines[i] > price:
                return i - 5;

        return len(all_pricelines) - 5

    def get_prev_line_no(self):
        if self.my_status["position"] > 0.0:
            line_no = self.my_status["position"] / self.each_size
        elif self.my_status["position"] < 0.0:
            line_no = self.my_status["position"] / self.each_size
        else:
            line_no = 0

        return line_no

    def adjust_tenlines(self, tenlines, open ,prev_no, curr_no):
        atr = 0.
        new_tenlines=[]

        five_shortlines=tenlines[0:5]
        five_longlines=tenlines[5:10]

        print("prev_no = %s" % prev_no)
        print("curr_no = %s" % curr_no)
        print("open = %s" %open)

        if curr_no != prev_no:
            print("adjusting ten lines")


            if prev_no > 0:
                hi_price = tenlines[5]
                assert (open > hi_price)  #Due to adjust_hilo(), open must be larger than hi_price

                if prev_no == 1:
                    atr = (open - hi_price) / 0.1
                elif prev_no == 2:
                    atr = (open - hi_price) / 0.3
                elif prev_no == 3:
                    atr = (open - hi_price) / 0.55
                elif prev_no == 4:
                    atr = (open - hi_price) / 0.85
                elif prev_no == 5:
                    atr = (open - hi_price) - 800
                else:
                    raise Exception("Wrong prev_no")

                five_longlines = [int(hi_price+self.atr_ratio[0]*atr), int(hi_price + self.atr_ratio[1] * atr), int(hi_price + self.atr_ratio[2] * atr), int(hi_price + self.atr_ratio[3] * atr),
                                  int(hi_price + self.atr_ratio[4]*atr)]

            elif prev_no < 0:
                lo_price = tenlines[4]
                assert (open < lo_price) #Due to adjust_hilo(), open must be smaller than lo_price

                if prev_no == -1:
                    atr = (lo_price - open) / 0.1
                elif prev_no == -2:
                    atr = (lo_price - open) / 0.3
                elif prev_no == -3:
                    atr = (lo_price - open) / 0.55
                elif prev_no == -4:
                    atr = (lo_price - open) / 0.85
                elif prev_no == -5:
                    atr = (lo_price - open) - 800
                else:
                    raise Exception("Wrong prev_no")

                five_shortlines = [int(lo_price - self.atr_ratio[4]*atr), int(lo_price - self.atr_ratio[3] * atr), int(lo_price - self.atr_ratio[2] * atr),
                                   int(lo_price - self.atr_ratio[1] * atr), int(lo_price-self.atr_ratio[0]*atr)]
            else: # prev_no==0
                raise Exception("Impossible case!")

            new_tenlines.extend(five_shortlines)
            new_tenlines.extend(five_longlines)

            return new_tenlines

        else:
            print("using current ten lines")
            return tenlines

    def get_orig_tenlines(self, hilo, atr=20000):
        (hi, lo) = hilo
        five_longlines = []
        five_shortlines = []
        tenlines = []
        for i in range(len(self.atr_ratio)):
            five_longlines.append(int(hi + self.atr_ratio[i] * atr))
            five_shortlines.append(int(lo - self.atr_ratio[i] * atr))

        five_shortlines.reverse()
        tenlines.extend(five_shortlines)
        tenlines.extend(five_longlines)

        return tenlines

    def hilo_run(self):
        while True:
            NEXT_HOUR = self.get_next_hour()
            hilo_price = self.get_hilo_price()  # change once within an hour
            open_price = self.get_current_price()
            hilo_price = self.adjust_hilo(hilo_price, open_price) #using open price to adjust hilo
            tenlines=self.get_orig_tenlines(hilo_price)
            print(tenlines)

            prev_no=self.get_prev_line_no()
            curr_no =self.get_beyond_priceline_no(tenlines,open_price)
            tenlines=self.adjust_tenlines(tenlines,open_price,prev_no,curr_no) #adjust tenlines to keep position continuous
            print(tenlines)

            #within-hour main loop
            while time.time()<NEXT_HOUR:

            
                time.sleep(1)


if __name__ == '__main__':
    tenlines = Tenlines()
    print(tenlines.get_next_hour())
    # print(tenlines.get_hilo_price())
    print(tenlines.get_current_bid_ask())
    # print(tenlines.get_require_colleral_and_type())
    print(tenlines.get_current_price())

    tenlines.hilo_run()
