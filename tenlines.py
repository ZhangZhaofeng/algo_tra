#!/usr/bin/python3
# coding=utf-8

import time
from tradingapis.bitflyer_api import pybitflyer
import my_keysecret as ks
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

        self.my_status = {"position": 0., "rest": 0., "pnl":0.}  # "nth":[entry_cash, entry_price]
        self.each_size = 0.01
        self.atr_ratio = [0.0, 0.2, 0.4, 0.7, 1.0]

        self.curr_dealedprice = 0.0
        self.tenlines = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.update_mystatus_pos()

    def trade_bitflyer_fx(self, type, amount=0.01):
        print("trade bitflyer_fx")
        if type == "BUY" or type == "buy":
            order = self.bitflyer_api.sendchildorder(product_code="FX_BTC_JPY",
                                                     child_order_type="MARKET",
                                                     side="BUY",
                                                     size=amount,
                                                     minute_to_expire=10000,
                                                     time_in_force="GTC"
                                                     )
        elif type == "SELL" or type == "sell":
            order = self.bitflyer_api.sendchildorder(product_code="FX_BTC_JPY",
                                                     child_order_type="MARKET",
                                                     side="SELL",
                                                     size=amount,
                                                     minute_to_expire=10000,
                                                     time_in_force="GTC"
                                                     )
        else:
            print("error!")

        return order

    def get_currorder_dealedprice(self, id):

        last_order = {"child_order_acceptance_id": " ", "average_price": 0.}
        while id != last_order["child_order_acceptance_id"]:
            try:
                last_order = self.get_last_order()
            except Exception:
                continue

        dealed_price = last_order["average_price"]
        print("dealed_price= %s" % dealed_price)
        return dealed_price

    def execute_trade(self, type, amount=0.01):
        print("")
        print("execute_trade:%s" %type)
        i = 0
        try_times_limit = 30

        while i < try_times_limit:
            try:
                i += 1
                order = self.trade_bitflyer_fx(type, amount)
                id = order["child_order_acceptance_id"]
                curr_dealedprice = self.get_currorder_dealedprice(id)
                return curr_dealedprice
            except Exception:
                print("Exception catched while trading, trying again.")
                time.sleep(0.5)
                continue

        raise Exception("Trading times are beyond limit")

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
        trade_history = []
        while True:
            try:
                trade_history = self.bitflyer_api.executions(product_code='FX_BTC_JPY', count=num)
                break
            except:
                continue

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
        return next_hour.timestamp()

    def update_colleral(self):
        coll = self.bitflyer_api.getcollateral()
        self.my_status["rest"] = coll["collateral"]
        print("collateral=%s" % self.my_status["rest"])

    def update_position(self):
        while True:
            try:
               res = self.bitflyer_api.getpositions(product_code="FX_BTC_JPY")
               #print(res)
               if res == []:
                 self.my_status["position"] = 0.0
                 self.my_status["pnl"] = 0.0
               else:
                 pos = 0.0
                 pnl = 0.0
                 for p in res:
                    sign = 1 if p["side"] == 'BUY' else -1
                    size = p["size"]
                    pos += sign * size
                    pnl += p["pnl"]

                 self.my_status["position"] = pos
                 self.my_status["pnl"] = pnl
               break
            except Exception:
                 continue

    def place_stop_order(self, conditional_price, long_short, type, slide=500):
        # need work
        return True

    def update_mystatus_pos(self):
        self.update_colleral()
        self.update_position()
        print(self.my_status)

    def get_last_order(self):
        orders = self.bitflyer_api.getchildorders(product_code="FX_BTC_JPY")
        # print(orders)
        return orders[0]

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
        if self.my_status["position"] > 0.0 and open < hi:
            hi = open - 1000
        elif self.my_status["position"] < 0.0 and open > lo:
            lo = open + 1000
        elif self.my_status["position"] == 0.0 and open > hi:
            hi = open + 1000
        elif self.my_status["position"] == 0.0 and open < lo:
            lo = open - 1000
        else:  # regular case, do nothing
            pass

        return (hi, lo)

    def get_curr_line_no(self, all_pricelines, price):
        for i in range(len(all_pricelines)):
            if all_pricelines[i] > price:
                return i - 5;

        return len(all_pricelines) - 5

    def get_prev_line_no(self):
        if self.my_status["position"] > 0.0:
            line_no = int(self.my_status["position"] / self.each_size)
        elif self.my_status["position"] < 0.0:
            line_no = int(self.my_status["position"] / self.each_size)
        else:
            line_no = 0

        return line_no

    def adjust_tenlines(self, tenlines, open, prev_no, curr_no):
        atr = 0.
        new_tenlines = []

        five_shortlines = tenlines[0:5]
        five_longlines = tenlines[5:10]

        print("prev_no = %s" % prev_no)
        print("curr_no = %s" % curr_no)
        print("open = %s" % open)

        if curr_no != prev_no:
            print("adjusting ten lines")

            if prev_no > 0:
                hi_price = tenlines[5]
                assert (open > hi_price)  # Due to adjust_hilo(), open must be larger than hi_price

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

                five_longlines = [int(hi_price + self.atr_ratio[0] * atr), int(hi_price + self.atr_ratio[1] * atr),
                                  int(hi_price + self.atr_ratio[2] * atr), int(hi_price + self.atr_ratio[3] * atr),
                                  int(hi_price + self.atr_ratio[4] * atr)]

            elif prev_no < 0:
                lo_price = tenlines[4]
                assert (open < lo_price)  # Due to adjust_hilo(), open must be smaller than lo_price

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

                five_shortlines = [int(lo_price - self.atr_ratio[4] * atr), int(lo_price - self.atr_ratio[3] * atr),
                                   int(lo_price - self.atr_ratio[2] * atr),
                                   int(lo_price - self.atr_ratio[1] * atr), int(lo_price - self.atr_ratio[0] * atr)]
            else:  # prev_no==0
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

    def pos_change_watcher(self, tenlines, curr_price):
        position_no = int(self.my_status["position"] / self.each_size)
        curr_line_no = self.get_curr_line_no(tenlines, curr_price)

        return int(curr_line_no - position_no)

    def execute_waiting_for_pos_and_lineNo_alignment(self, orig_pos, delta_line_no):
        self.update_mystatus_pos()
        while abs(orig_pos + delta_line_no * self.each_size - self.my_status["position"])>0.005:
            print("A=%f" %(orig_pos + delta_line_no * self.each_size))
            print("B=%f" %(self.my_status["position"]))

            self.update_mystatus_pos()
            print("Waiting for that pos aligns with line_no ")
        print("pos aligning with line_no is verified")

    def execute_slide_computation(self, dealed_price, type):
        line_no = int(self.my_status["position"] / self.each_size)
        slide = 0.

        if type == "BUY":
            index = int(line_no + 4)
            slide = dealed_price - self.tenlines[index]
        elif type == "SELL":
            index = int(line_no + 5)
            slide = self.tenlines[index] - dealed_price
        else:
            raise Exception["side error"]
        
        print("slide=%s" %slide)
        return slide

    def pos_adjustment(self, delta_line_no):
        if delta_line_no == 0:
            return True

        orig_pos = self.my_status["position"]
        type = "BUY" if delta_line_no > 0 else "SELL"
        real_delta_line_no = 1 if delta_line_no > 0 else -1
        if delta_line_no > 1:
            line_adjust_pattern = "long_all"
        elif delta_line_no == 1:
            line_adjust_pattern = "long_neigbour"
        elif delta_line_no == -1:
            line_adjust_pattern = "short_all"
        elif delta_line_no < -1:
            line_adjust_pattern = "short_neigbour"
        else:
            raise Exception("Unknown error")

        self.curr_dealedprice=self.execute_trade(type, self.each_size)
        self.execute_waiting_for_pos_and_lineNo_alignment(orig_pos, real_delta_line_no)
        slide = self.execute_slide_computation(int(self.curr_dealedprice), type)
        #self.adjust_tenlines_according_to_slide(slide, line_adjust_pattern)
        return True


    def adjust_tenlines_according_to_slide(self, slide, pattern):
        line_no = int(self.my_status["position"] / self.each_size)
        tenlines = self.tenlines
        if pattern == "long_all":
            for i in range(line_no + 4, len(tenlines)):
                if i == line_no + 4:
                    tenlines[i] = self.curr_dealedprice - 1000
                else:
                    tenlines[i] += slide
        elif pattern == "long_neigbour":
            tenlines[line_no + 4] = self.curr_dealedprice - 1000
            for i in range(line_no + 5, len(tenlines)):
                if tenlines[line_no + 5]-slide<tenlines[line_no + 4]:
                    break
                tenlines[i] -= slide
        elif pattern == "short_all":
            for i in range(0, line_no + 5):
                if i == line_no + 5:
                    tenlines[i] = self.curr_dealedprice + 1000
                else:
                    tenlines[i] -= slide
        elif pattern == "short_neigbour":
            tenlines[line_no + 5] = self.curr_dealedprice + 1000
            for i in range(0,line_no + 4):
                if tenlines[line_no + 4]+slide>tenlines[line_no + 5]:
                    break
                tenlines[i] += slide
        else:
            raise Exception("Unknown error")

        self.tenlines = tenlines
        print("pattern:%s" %pattern)
        print("adjust tenlines(slide): %s" %self.tenlines)

    def hilo_run(self):

        print("hilo_run starts")
        while True:
            NEXT_HOUR = self.get_next_hour()
            hilo_price = self.get_hilo_price()  # change once within an hour
            open_price = self.get_current_price()
            hilo_price = self.adjust_hilo(hilo_price, open_price)  # using open price to adjust hilo
            tenlines = self.get_orig_tenlines(hilo_price)

            print(time.strftime('%Y/%m/%d,%H:%M:%S'))
            print("orig tenlines: %s" % tenlines)

            prev_no = self.get_prev_line_no()
            curr_no = self.get_curr_line_no(tenlines, open_price)
            self.tenlines = self.adjust_tenlines(tenlines, open_price, prev_no,
                                                 curr_no)  # adjust tenlines to keep position continuous
            print("initial tenlines: %s" % self.tenlines)

            # within-hour main loop
            while time.time() < NEXT_HOUR:
                delta_line_no = self.pos_change_watcher(self.tenlines, self.get_current_price())
                print("time:%s  current_price: %s" %(time.strftime('%Y/%m/%d,%H:%M:%S'),self.get_current_price()), end="\r")
                if delta_line_no != 0:
                    self.pos_adjustment(delta_line_no)
                time.sleep(0.5)


if __name__ == '__main__':
    tenlines = Tenlines()

#    print(tenlines.get_current_price())

#    tenlines.hilo_run()
    tenlines.update_position()
