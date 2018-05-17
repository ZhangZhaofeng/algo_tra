from tradingapis.bitflyer_api import pybitflyer
import keysecret as ks
import time
import predict
import configIO
import sys
import technical_fx_bidirc
import math

from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib

# stop version

class SendMail:

    def __init__(self,address,username,passwd):
        self.address = address
        self.username = username
        self.passwd = passwd
        self.s = smtplib.SMTP('smtp.gmail.com', 587)
        self.from_add = 'goozzfgle@gmail.com'
        self.connect_mail_server()

    def connect_mail_server(self):
        try:
            if self.s.ehlo_or_helo_if_needed():
                self.s.ehlo()
            self.s.starttls()
            self.s.ehlo()
            self.s.login(self.username, self.passwd)
            return 0
        except smtplib.SMTPNotSupportedError:
            self.s.login(self.username, self.passwd)
            return 0
        return 1

    def send_email(self, toaddress ,mesage):
        self.connect_mail_server()
        try:
            self.s.sendmail(self.from_add, toaddress, mesage)
            print('Send a mail to %s' % (toaddress))
        except smtplib.SMTPDataError:
            print('Can not send a mail, maybe reach the daily limition')


class AutoTrading:
    cur_hold_position = 0.0
    cur_find_direction = 'none'
    order_exist = False
    order_id = ''

    def __init__(self):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))

    def maintance_time(self):
        while 1:
            cur_oclock = int(time.strftime('%H:')[0:-1])
            cur_min = int(time.strftime('%M:')[0:-1])
            if (cur_oclock == 4 and cur_min >= 0 and cur_min <= 12) or (cur_oclock == 3 and cur_min >= 58):
                predict.print_and_write('Server maintenance')
                time.sleep(60)
                continue
            else:
                return

    def trade_simple(self, type, limitorstop, trigger, limit, amount):
        self.maintance_time()

        product= 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 75
        if limitorstop == 'stop':
            if type == 'BUY' or type == 'buy':
            # order = self.quoinex_api.create_market_buy(product_id=5, quantity=str(amount), price_range=str(buysellprice))
                parameters =  [{'product_code': product, 'condition_type': 'STOP', 'side': 'BUY', 'size': str(amount),
                            'trigger_price': str(trigger)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
            elif type == "SELL" or type == "sell":
                parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'SELL', 'size': str(amount),
                           'trigger_price': str(trigger)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
        elif limitorstop == 'stop_limit':
            if type == 'BUY' or type == 'buy':
                parameters = [{ 'product_code' : product, 'condition_type' : 'STOP_LIMIT', 'side': 'BUY',
                                 'price': str(limit), 'size': str(amount), 'trigger_price': str(trigger)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
            elif type == "SELL" or type == "sell":
                parameters = [{'product_code': product, 'condition_type': 'STOP_LIMIT', 'side': 'SELL',
                                'price': str(limit), 'size': str(amount), 'trigger_price': str(trigger)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
        elif limitorstop == 'limit':
            if type == 'BUY' or type == 'buy':
                parameters = [{ 'product_code' : product, 'condition_type' : 'LIMIT', 'side': 'BUY',
                                 'price': str(limit), 'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
            elif type == "SELL" or type == "sell":
                parameters = [{'product_code': product, 'condition_type': 'LIMIT', 'side': 'SELL',
                                'price': str(limit), 'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
        else:
            print("error!")
        return (order)

    # trade oco while no position
    def trade_oco1(self, buy, sell, amount):
        self.maintance_time()
        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 75
        parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'BUY',
                       'size': str(amount), 'trigger_price': str(buy)},
                      {'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                       'size': str(amount), 'trigger_price': str(sell)},
                      ]
        order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                  parameters=parameters)
        return (order)

    # trade oco with position
    def trade_oco2(self, po, stopprofit, stoploss, amount , switch):
        self.maintance_time()
        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 75

        if po == 'long':
            parameters = [{'product_code': product, 'condition_type': 'LIMIT', 'side': 'SELL',
                       'size': str(amount), 'price': str(stopprofit)},
                      {'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                       'size': str(switch), 'trigger_price': str(stoploss)},
                      ]
            order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                  parameters=parameters)
        elif po == 'short':
            parameters = [{'product_code': product, 'condition_type': 'LIMIT', 'side': 'BUY',
                           'size': str(amount), 'price': str(stopprofit)},
                          {'product_code': product, 'condition_type': 'STOP', 'side': 'BUY',
                           'size': str(switch), 'trigger_price': str(stoploss)},
                          ]
            order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                      parameters=parameters)

        return (order)

    def print_order(self, order):
        predict.print_and_write(order)

    def get_checkin_price(self):
        p = self.bitflyer_api.getpositions(product_code='FX_BTC_JPY')
        position0 = 0.0
        checkin_price = 0.0
        if isinstance(p, list):
            for i in p:
                #predict.print_and_write('check in price: %f' % (i['price']))

                if i['side'] == 'SELL':
                    position0 -= i['size']
                else:
                    position0 += i['size']

            for i in p:
                checkin_price += i['size']/abs(position0) * i['price']
            predict.print_and_write('Check in price: %f, position: %f' % (checkin_price, position0))

        elif isinstance(p, dict) or len(p) == 0:
            predict.print_and_write('Position not exist')

        return([checkin_price, position0])

    def get_current_price(self, numbers):
        trade_history = self.bitflyer_api.executions(product_code = 'FX_BTC_JPY', count = 100)
        total_size = 0.0
        cur_price = 0.0
        for i in trade_history:
            total_size += i['size']

        for i in trade_history:
            cur_price += i['size']/total_size * i['price']

        return(math.round(cur_price))

    # if no position find a position to trade
    def trade_none_position(self, curprice , hi, lo):

        result = self.get_hilo()
        hi = result[1]
        lo = result[0]
        trade_amount = 0.02
        # find a direction to trade
        if curprice > hi:
            self.cur_find_direction = 'short'
        elif curprice < lo:
            self.cur_find_direction = 'long'
        elif curprice < hi and curprice > lo:
            self.cur_find_direction = 'long_short'
        else:
            self.cur_find_direction = 'none'

        # trade this direction
        if self.cur_find_direction == 'short':
            order = self.trade_simple('sell', 'stop', lo, 0, trade_amount)
            self.print_order(order)
            self.order_exist = True
            self.orderid = order['parent_order_acceptance_id']
        elif self.cur_find_direction == 'long':
            order = self.trade_simple('buy', 'stop', hi, 0, trade_amount)
            self.print_order(order)
            self.order_exist = True
            self.orderid = order['parent_order_acceptance_id']
        elif self.cur_find_direction == 'long_short':
            order = self.trade_oco1(hi, lo, trade_amount)
            self.print_order(order)
            self.order_exist = True
            self.orderid = order['parent_order_acceptance_id']

    # if with position give a price to stopprofit and stoploss
    def trade_with_position(self, hi, lo):

        profitcut_factor = 0.015
        checkins = self.get_checkin_price()
        checkin_price = checkins[0]
        self.cur_hold_position = checkins[1]
        trade_amount = self.cur_hold_position
        traed_amount_switch = trade_amount + 0.01


        if self.cur_hold_position < 0.0:
            stoploss = hi
            stopprofit = math.floor(checkin_price * (1 - profitcut_factor))
            if stopprofit  > hi:
                stopprofit = hi
            order = self.trade_oco2('short', stopprofit, stoploss, trade_amount, traed_amount_switch)
            self.print_order(order)
            self.order_exist = True
            self.order_id = order['parent_order_acceptance_id']
        elif self.cur_hold_position > 0.0:
            stoploss = lo
            stopprofit = math.floor(checkin_price * (1 + profitcut_factor))
            if stopprofit  < lo:
                stopprofit = lo
            order = self.trade_oco2('long', stopprofit, stoploss, trade_amount, traed_amount_switch)
            self.print_order(order)
            self.order_exist = True
            self.order_id = order['parent_order_acceptance_id']

    def get_hilo(self):
        hilos = technical_fx_bidirc.HILO()
        result = hilos.publish_current_hilo_price()

        # result = prediction.publish_current_limit_price(periods="1H")
        sell = float(result[1])
        buy = float(result[0])
        close = float(result[2])  # the close price of last hour
        return([sell, buy, close])

    def get_orders(self, status = ''):
        #order = self.quoinex_api.get_orders()
        #order = self.quoinex_api.get_orders(status, limit)
        #ACTIVE CANCELED
        product = 'FX_BTC_JPY'
        if status != '':
            order = self.bitflyer_api.getparentorders(product_code=product, parent_order_state=status)
        else:
            order = self.bitflyer_api.getparentorders(product_code=product, count=30)
        return (order)

    def get_orderbyid(self, id):
        product = 'FX_BTC_JPY'
        i = 20
        while i > 0:
            try:
            #order = self.bitflyer_api.getparentorder(product_code=product, parent_order_acceptance_id=id)
                orders = self.get_orders()
                for i in orders:
                    if i['parent_order_acceptance_id'] == id:
                        return (i)
                print('order not find')
                return({})
            except Exception:
                print('Server is fucked off ,try again')
                time.sleep(20)
                i -= 1
                continue
        print('Try too many times, failed')
        return({})

    def cancel_order(self, id):
        product = 'FX_BTC_JPY'
        i = 20
        while i > 0:
            try:
                statue = self.bitflyer_api.cancelparentorder(product_code=product, parent_order_acceptance_id=id)
                time.sleep(10)
                order = self.get_orderbyid(id)
                if order['parent_order_state'] == 'COMPLETED':
                    predict.print_and_write('Order completed')
                    return (0.0)
                if order['parent_order_state'] == 'CANCELED':
                    predict.print_and_write('Order cancelled')
                    return (float(order['cancel_size']))
                else:
                    i -= 1
                    print('Try again cancelling')
                    continue
            except Exception:
                order = self.get_orderbyid(id)
                if order['parent_order_state'] == 'COMPLETED':
                    print('Executed before cancelling')
                    return(0.0)
                time.sleep(5)
                print('Exception Try again cancelling')
                i -= 1
        predict.print_and_write('Cancel order failed')
        return ([])

    def judge_condition(self):
        if self.order_exist == True:
            remain_test = self.cancel_order(self.order_id) + 1
            print('cancel order, remain %f'%(remain_test -1))

        checkins = self.get_checkin_price()
        # if not position exist trade none position
        if checkins[1] == 0.0:
            predict.print_and_write('No position exist, trade none position')
            cur_price = self.get_current_price(100)
            result = self.get_hilo()
            hi = result[1]
            lo = result[0]
            predict.print_and_write('current price is %f'%(cur_price))
            self.trade_none_position(cur_price, hi ,lo)

        else:
            predict.print_and_write('Position exist, trade with position')
            result = self.get_hilo()
            hi = result[1]
            lo = result[0]
            self.trade_with_position(hi, lo)

if __name__ == '__main__':
    autoTrading = AutoTrading()
    while 1:
        autoTrading.judge_condition()
        time.sleep(10)

    #autoTrading.get_current_price(100)