# !/usr/bin/python3
# coding=utf-8

import time
from tradingapis.bitflyer_api import pybitflyer
import my_keysecret as ks
import time
import datetime as dt
import predict
import sys
import one_hour_sim_hilo_close as ohshc
import math
import apis
import data2csv

from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib


class Hilo:
    def __init__(self):
        print("hilo Algo 1Hour Starts")
        self.hilo = ohshc.HILO()
        # print(mytrade.get_asset_quoinex())

        print("Initializing Bitflyer API ")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))

        self.my_status = {"position": 0., "rest": 0., "pnl": 0.}  # "nth":[entry_cash, entry_price]
        self.each_size = 0.01

        self.latest_dealedprice = 0.0
        self.profit_hi = 0.0
        self.profit_lo = 9990000

        self.last_open = 0.0
        self.last_close = 0.0
        self.flag = 0
        self.Go = True

        self.within_candle_process = False

        self.update_mystatus_pos()
        self.update_latest_dealedprice()

    def logger(self,data):
        data2csv.data2csv(data)

    def update_latest_dealedprice(self):
        if abs(self.my_status["position"])>0.005:
            order=self.get_last_order()
            if len(order)>0:
                print("latest_dealedprice updated")
                self.latest_dealedprice=order["average_price"]
                
    # deal with maintenance time
    def maintenance_time(self):
        while 1:
            cur_oclock = int(time.strftime('%H:')[0:-1])
            cur_min = int(time.strftime('%M:')[0:-1])
            if (cur_oclock == 4 and cur_min >= 0 and cur_min <= 12) or (cur_oclock == 3 and cur_min >= 58):
                predict.print_and_write('Server maintenance')
                time.sleep(60)
                continue
            else:
                return

    def trade_bitflyer_fx(self, type, amount=0.01):
        self.maintenance_time()
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
        print("execute_trade:%s" % type)
        i = 0
        try_times_limit = 30
        amount=round(amount,2)
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
    def get_hilo_price(self, num=100, periods="1H"):
        return self.hilo.publish_current_hilo_price(num=num, periods=periods)

    def get_current_bid_ask(self):
        while 1:
            try:
                [bid, ask] = apis.get_bid_ask_bitflyer('FX_BTC_JPY')
                break
            except Exception:
                continue

        return (round(bid, 0), round(ask, 0))

    def get_unchecked_price(self, num=3, product_code='FX_BTC_JPY'):
        trade_history = []
        while True:
            try:
                trade_history = self.bitflyer_api.executions(product_code=product_code, count=num)
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

    def get_current_price(self,num=3, product_code='FX_BTC_JPY'):
        price=self.get_unchecked_price(num, product_code)
        while price<1.0:
            print("Getting price again")
            price = self.get_unchecked_price(num, product_code)
            time.sleep(0.5)
        return price

    def get_kairi(self):
        fx = self.get_current_price(product_code='FX_BTC_JPY')
        btc = self.get_current_price(product_code='BTC_JPY')
        if btc == 0.:
            kairi = 100
        else:
            kairi = fx / btc * 100 - 100

        return kairi

    # can be called at any time within current hour
    def get_next_hour(self):
        next_hour = dt.datetime.fromtimestamp(time.time() - time.time() % 3600 + 3605)
        return next_hour.timestamp()

    # can be called at any time within current min
    def get_next_min(self):
        next_min = dt.datetime.fromtimestamp(time.time() - time.time() % 60 + 60)
        return next_min.timestamp()

    def get_next_15min(self):
        next_15min = dt.datetime.fromtimestamp(time.time() - time.time() % 240 + 241)
        return next_15min.timestamp()

    def update_colleral(self):
        coll = self.bitflyer_api.getcollateral()
        self.my_status["rest"] = coll["collateral"]
        print("collateral=%s" % self.my_status["rest"])

    def update_position(self):
        while True:
            try:
                res = self.bitflyer_api.getpositions(product_code="FX_BTC_JPY")
                # print(res)
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

    def get_last_open_close(self, periods="1H"):
        while 1:
            try:
                (open,close)= self.hilo.get_last_open_close(periods=periods)
                return open,close
            except Exception:
                continue

    def get_last_open(self, periods="1H"):
        (last_open, last_close) = self.get_last_open_close(periods=periods)
        return last_open

    def get_last_close(self, periods="1H"):
        (last_open, last_close) = self.get_last_open_close(periods=periods)
        return last_close

    def waitfor_position_match(self, orig_size, trade_size):
        self.update_mystatus_pos()
        counter = 0
        while abs(self.my_status["position"] - orig_size - trade_size) > 0.0005:
            self.update_mystatus_pos()
            time.sleep(0.5)
            counter += 1
            if counter > 1000:
                raise Exception["waitfor_position_match error"]

    def execute_slide_computation(self, dealed_price, order_price, type):
        slide = 0.
        if type == "buy":
            slide = dealed_price - order_price
        elif type == "sell":
            slide = order_price - dealed_price
        else:
            raise Exception["Type error!"]
        print("")
        print("slide=%s" % slide)
        return slide

    def mdfy_position(self, hilo, close_price):
        (hi_price, lo_price) = hilo
        trade_volume = self.each_size * 1
        orig_pos = self.my_status["position"]
        if self.my_status["position"] > 0.0005:  # current long position
            if close_price < hi_price:
                self.latest_dealedprice = self.execute_trade("sell", trade_volume)
                self.waitfor_position_match(orig_pos, -trade_volume)
                slide = self.execute_slide_computation(self.latest_dealedprice, close_price, "sell")
                self.trade_log.append([self.latest_dealedprice, slide, -trade_volume, "F l->n"])
                print("Fake long -> none")

        elif self.my_status["position"] < -0.0005:  # current short position
            if close_price > lo_price:
                self.latest_dealedprice = self.execute_trade("buy", trade_volume)
                self.waitfor_position_match(orig_pos, trade_volume)
                slide = self.execute_slide_computation(self.latest_dealedprice, close_price, "buy")
                self.trade_log.append([self.latest_dealedprice, slide, trade_volume, "F s->n"])
                print("Fake short -> none")

    def hilo_watcher(self, hilo_price, current_price, close_cur, overshoot=2500):
        orig_pos = self.my_status["position"]
        target_diff = [4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000, 20000]
        buffer = 3000
        (hi_price, lo_price) = hilo_price
        # print("open=%s" % current_price)
        if self.my_status["position"] > 0.0005:  # current long position
            print("CP:%s lo= %s pro_hi= %s" % (current_price, lo_price, self.profit_hi), end="\r")
            if current_price < max([lo_price- overshoot, self.profit_hi]) :
                if current_price < lo_price - overshoot:
                    if self.change_pos_within_one_hour:
                        return False


                    trade_volume = self.each_size * 1
                    note = "L->NN"

                    self.latest_dealedprice = self.execute_trade("sell", trade_volume)
                    self.waitfor_position_match(orig_pos, -trade_volume)
                    slide1 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=current_price,
                                                           type="sell")
                    slide2 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=lo_price - overshoot,
                                                           type="sell")
                    self.trade_log.append([self.latest_dealedprice, slide1,slide2, -trade_volume, note])
                    self.profit_hi = 0.0
                    self.change_pos_within_one_hour=1
                    self.flag = 0
                    return False
                elif current_price < self.latest_dealedprice-1500 and self.flag == 1:
                    print("Price volatility too large -> pro_hi reset")
                    self.profit_hi = 0.0
                    self.flag = 0
                    return False
                else:
                    trade_volume = self.each_size * 1
                    note = "L->N"
                    self.latest_dealedprice = self.execute_trade("sell", trade_volume)
                    self.waitfor_position_match(orig_pos, -trade_volume)
                    slide1 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=current_price,
                                                           type="sell")
                    slide2 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=self.profit_hi,
                                                           type="sell")
                    self.trade_log.append([self.latest_dealedprice, slide1,slide2, -trade_volume, note])
                    self.profit_hi = 0.0
                    self.flag = 0
                    return False



            elif current_price - self.latest_dealedprice > target_diff[0] and self.flag == 0:
                self.profit_hi = self.latest_dealedprice + target_diff[0] - 1500
                self.flag = 1
            elif current_price - self.latest_dealedprice > target_diff[1] and self.flag == 1:
                self.profit_hi = self.latest_dealedprice + target_diff[1] - buffer
                self.flag = 2
            elif current_price - self.latest_dealedprice > target_diff[2] and self.flag == 2:
                self.profit_hi = self.latest_dealedprice + target_diff[2] - buffer
                self.flag = 3
            elif current_price - self.latest_dealedprice > target_diff[3] and self.flag == 3:
                self.profit_hi = self.latest_dealedprice + target_diff[3] - buffer
                self.flag = 4
            elif current_price - self.latest_dealedprice > target_diff[4] and self.flag == 4:
                self.profit_hi = self.latest_dealedprice + target_diff[4] - buffer
                self.flag = 5
            elif current_price - self.latest_dealedprice > target_diff[5] and self.flag == 5:
                self.profit_hi = self.latest_dealedprice + target_diff[5] - buffer
                self.flag = 6
            elif current_price - self.latest_dealedprice > target_diff[6] and self.flag == 6:
                self.profit_hi = self.latest_dealedprice + target_diff[6] - buffer
                self.flag = 7
            elif current_price - self.latest_dealedprice > target_diff[7] and self.flag == 7:
                self.profit_hi = self.latest_dealedprice + target_diff[7] - buffer
                self.flag = 8
            elif current_price - self.latest_dealedprice > target_diff[8] and self.flag == 8:
                self.profit_hi = self.latest_dealedprice + target_diff[8] - buffer
                self.flag = 9
            else:
                pass
        elif self.my_status["position"] < -0.0005:  # current short position
            print("CP:%s hi:%s pro_lo=%s" % (current_price, hi_price, self.profit_lo), end="\r")
            if current_price > min([hi_price+ overshoot, self.profit_lo]) :
                if current_price > hi_price + overshoot:
                    if self.change_pos_within_one_hour:
                        return False

                    trade_volume = self.each_size * 1
                    note = "S->NN"
                    self.latest_dealedprice = self.execute_trade("buy", trade_volume)
                    self.waitfor_position_match(orig_pos, trade_volume)
                    slide1 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=current_price,
                                                           type="buy")
                    slide2 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=hi_price + overshoot,
                                                           type="buy")
                    self.trade_log.append([self.latest_dealedprice, slide1, slide2, trade_volume, note])
                    self.profit_lo = 9990000
                    self.change_pos_within_one_hour = 1
                    self.flag = 0
                    return False
                elif current_price>self.profit_lo+1500 and self.flag == 1:
                    print("Price volatility too large -> pro_lo reset")
                    self.profit_lo = 9990000
                    self.flag = 0
                    return False
                else:
                    trade_volume = self.each_size * 1
                    note = "S->N"
                    self.latest_dealedprice = self.execute_trade("buy", trade_volume)
                    self.waitfor_position_match(orig_pos, trade_volume)
                    slide1 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=current_price,
                                                           type="buy")
                    slide2 = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                           order_price=self.profit_lo,
                                                           type="buy")
                    self.trade_log.append([self.latest_dealedprice, slide1, slide2, trade_volume, note])
                    self.profit_lo = 9990000
                    self.flag = 0
                    return False



            elif self.latest_dealedprice - current_price > target_diff[0] and self.flag == 0:
                self.profit_lo = self.latest_dealedprice - target_diff[0] + 1500
                self.flag = 1
            elif self.latest_dealedprice - current_price > target_diff[1] and self.flag == 1:
                self.profit_lo = self.latest_dealedprice - target_diff[1] + buffer
                self.flag = 2
            elif self.latest_dealedprice - current_price > target_diff[2] and self.flag == 2:
                self.profit_lo = self.latest_dealedprice - target_diff[2] + buffer
                self.flag = 3
            elif self.latest_dealedprice - current_price > target_diff[3] and self.flag == 3:
                self.profit_lo = self.latest_dealedprice - target_diff[3] + buffer
                self.flag = 4
            elif self.latest_dealedprice - current_price > target_diff[4] and self.flag == 4:
                self.profit_lo = self.latest_dealedprice - target_diff[4] + buffer
                self.flag = 5
            elif self.latest_dealedprice - current_price > target_diff[5] and self.flag == 5:
                self.profit_lo = self.latest_dealedprice - target_diff[5] + buffer
                self.flag = 6
            elif self.latest_dealedprice - current_price > target_diff[6] and self.flag == 6:
                self.profit_lo = self.latest_dealedprice - target_diff[6] + buffer
                self.flag = 7
            elif self.latest_dealedprice - current_price > target_diff[7] and self.flag == 7:
                self.profit_lo = self.latest_dealedprice - target_diff[7] + buffer
                self.flag = 8
            elif self.latest_dealedprice - current_price > target_diff[8] and self.flag == 8:
                self.profit_lo = self.latest_dealedprice - target_diff[8] + buffer
                self.flag = 9
            else:
                pass
        elif abs(self.my_status["position"]) < 0.0005:  # "Null"
            print("CP:%s hi:%s lo:%s" % (current_price, hi_price, lo_price), end="\r")
            if close_cur < hi_price and current_price > hi_price + overshoot:
                trade_volume = self.each_size * 1
                self.latest_dealedprice = self.execute_trade("buy", trade_volume)
                self.waitfor_position_match(orig_pos, trade_volume)
                slide = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                       order_price=current_price,
                                                       type="buy")
                self.trade_log.append([self.latest_dealedprice, slide, trade_volume, "N->L"])
                return False

            elif close_cur > lo_price and current_price < lo_price - overshoot:
                trade_volume = self.each_size * 1
                self.latest_dealedprice = self.execute_trade("sell", trade_volume)
                self.waitfor_position_match(orig_pos, -trade_volume)
                slide = self.execute_slide_computation(dealed_price=self.latest_dealedprice,
                                                       order_price=current_price,
                                                       type="sell")
                self.trade_log.append([self.latest_dealedprice, slide, -trade_volume, "N->S"])
                return False

            else:
                pass

        return False

    def candle_finish_process(self, hilo_price, close_price):
        print("")
        print("candle_finish_process")

        if not self.change_pos_within_one_hour:
            self.change_pos_within_one_hour=0
            self.hilo_watcher(hilo_price, close_price, close_price ,overshoot=0.)
        else:
            self.mdfy_position(hilo_price, close_price)

        self.update_mystatus_pos()
        self.log.append(close_price[0])
        self.log.append(self.my_status["position"])
        self.log.append(self.my_status["rest"] + self.my_status["pnl"])
        self.log.append(hilo_price)
        self.log.extend(self.trade_log)
        self.logger(self.log)

    def candle_within_process(self, hilo_price, current_price, close):
        return self.hilo_watcher(hilo_price, current_price, close)

    def hilo_run_1h(self):
        print("hilo_run_1h starts")
        hilo_price = self.get_hilo_price(num=100, periods="1H")
        close_price = self.get_last_close()
        while True:
            NEXT_HOUR = self.get_next_hour()
            self.log = []
            self.trade_log = []
            self.within_candle_process = False
            self.change_pos_within_one_hour = 0
            print("############################################")
            print("hilo_run_1h: %s" % time.strftime('%Y/%m/%d,%H:%M:%S'))
            print("############################################")
            self.log.append(time.strftime('%Y/%m/%d,%H:%M:%S'))

            if self.get_kairi() > 10. and abs(self.my_status["position"]) < 0.0005:
                self.Go = False

            # within-min main loop
            while self.Go:
                current_price = self.get_current_price()
                if not self.within_candle_process:
                    self.within_candle_process = self.candle_within_process(hilo_price,
                                                                            current_price,close_price)  # buy/sell at most once in one candle

                if time.time() > NEXT_HOUR:
                    hilo_price = self.get_hilo_price(num=100, periods="1H")
                    close_price = self.get_last_close()
                    self.candle_finish_process(hilo_price, close_price)
                    break
                time.sleep(0.5)
            time.sleep(0.5)



if __name__ == '__main__':
    hilo = Hilo()
    while 1: 
        try:
            hilo.hilo_run_1h()
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
            raise Exception
            continue
        
    # kairi=hilo.get_kairi()
    # print(kairi)
