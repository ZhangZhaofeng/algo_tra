from tradingapis.bitflyer_api import pybitflyer
import keysecret as ks
import time
import datetime
import predict
import configIO
import sys
import technical_fx_bidirc
import math

from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib
import data2csv

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
    switch_in_hour = False
    order_exist = False
    switch_in_hour = True # if true, will be waiting for inhour position change
    order_id = ''
    init_trade_amount = 0.01

    def __init__(self):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))

    def trade_oco1(self, buy, sell, amount):
        self.maintance_time()
        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 575
        try_t = 0
        while try_t < 20:
            parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'BUY',
                       'size': str(amount), 'trigger_price': str(buy)},
                      {'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                       'size': str(amount), 'trigger_price': str(sell)},
                      ]
            order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                  parameters=parameters)
            data2csv.data2csv(
                [time.strftime('%b:%d:%H:%M'), 'order', 'OCO_STOP', 'amount', '%f' % float(amount), 'buy', '%f' % float(buy), 'sell', '%f' % float(sell)])

            if 'parent_order_acceptance_id' in order:
                return (order)
            else:
                try_t += 1
                print(order)
                print('Failed, try again')
                time.sleep(20)

    def trade_oco3(self, po, limitprice, switch):
        self.maintance_time()
        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 575
        try_t = 0
        while try_t < 20:
            if po == 'sell':
                parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                           'size': str(switch), 'trigger_price': str(limitprice-1500)},
                          {'product_code': product, 'condition_type': 'STOP_LIMIT', 'side': 'SELL',
                           'size': str(switch), 'price': str(limitprice+150)},
                          ]
                order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'OCO_SELL_LIMIT_STOP', 'amount', '%f' % float(switch),
                    'stopprofit',
                    '%f' % float(limitprice), 'stoploss', '%f' % float(limitprice)])


            elif po == 'buy':
                parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'BUY',
                           'size': str(switch), 'trigger_price': str(limitprice+1500)},
                          {'product_code': product, 'condition_type': 'LIMIT', 'side': 'BUY',
                           'size': str(switch), 'price': str(limitprice-150)},
                          ]
                order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'OCO_BUY_LIMIT_STOP(inhour)', 'amount', '%f' % float(switch),
                    'stopprofit',
                    '%f' % float(limitprice), 'stoploss', '%f' % float(limitprice)])

            if 'parent_order_acceptance_id' in order:
                return (order)
            else:
                try_t += 1
                print(order)
                print('Failed, try again')
                time.sleep(20)

    def trade_market(self, type, amount):
        self.maintance_time()
        self.maintance_time()
        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 575
        try_t = 0
        while try_t < 20:
            if type == 'BUY' or type == 'buy':
                parameters = [{'product_code': product, 'condition_type': 'MARKET', 'side': 'BUY',
                            'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_MARKET', 'amount', '%f' % float(amount)])
            elif type == "SELL" or type == "sell":
                parameters = [{'product_code': product, 'condition_type': 'MARKET', 'side': 'SELL',
                           'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_MARKET', 'amount', '%f' % float(amount)])
            else:
                print("error!")
            if 'parent_order_acceptance_id' in order:
                return (order)
            else:
                try_t += 1
                print(order)
                print('Failed, try again')
                time.sleep(20)

    def trade_stop(self, type, price, amount):
        self.maintance_time()
        self.maintance_time()
        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 575
        try_t = 0
        while try_t < 20:
            if type == 'BUY' or type == 'buy':
                parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'BUY',
                            'trigger_price': str(price-500), 'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_STOP', 'amount', '%f' % float(amount)])
            elif type == "SELL" or type == "sell":
                parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                           'trigger_price': str(price+500), 'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_STOP', 'amount', '%f' % float(amount)])
            else:
                print("error!")
            if 'parent_order_acceptance_id' in order:
                return (order)
            else:
                try_t += 1
                print(order)
                print('Failed, try again')
                time.sleep(20)


    # deal with maintance time
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

    # judge if the time stamp in this hour
    def bf_timejudge(self, timestring):
        cur_time = time.gmtime()
        #time.sleep(10)
        #cur_time2 = time.gmtime()
        a = time.mktime(timestring)
        b = time.mktime(cur_time)
        tdelta = b - a
        return(tdelta)

    # get current price
    def get_current_price(self, numbers):
        trade_history = self.bitflyer_api.executions(product_code = 'FX_BTC_JPY', count = 100)
        total_size = 0.0
        cur_price = 0.0
        for i in trade_history:
            total_size += i['size']

        for i in trade_history:
            cur_price += i['size']/total_size * i['price']

        return(math.floor(cur_price))


    def get_hilo(self):
        hilos = technical_fx_bidirc.HILO()
        result = hilos.publish_current_hilo_price()

        # result = prediction.publish_current_limit_price(periods="1H")
        buy = float(result[0])
        sell = float(result[1])
        close = float(result[2])  # the close price of last hour
        return ([sell, buy, close])


    def get_checkin_price(self):
        p = self.bitflyer_api.getpositions(product_code='FX_BTC_JPY')
        position0 = 0.0
        checkin_price = 0.0
        time_diff = 0
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

            for i in p:
                opentime = i['open_date']
                time_diff = self.bf_timejudge(opentime)
                break

        elif isinstance(p, dict) or len(p) == 0:
            predict.print_and_write('Position not exist')
        checkin_price = math.floor(checkin_price)
        return([checkin_price, position0, time_diff])



    def trade_hour_init(self, checkins, cur_price, hilo): # if we have a new position in this hour
        self.switch_in_hour = False
        if hilo[2] >= hilo[1] : # if close > hi and position is negative
            #TODO
            trade_mount = '%.2f' % (self.init_trade_amount - checkins[1])
            if trade_mount > 0.0:
                order = self.trade_market('buy', trade_mount)
            # buy self.init + checkins[1]

        elif hilo[2] <= hilo[0] : # if close < lo and position is positive
            # TODO
            # sell self.init + checkins[1]
            trade_mount = '%.2f' % (self.init_trade_amount + checkins[1])
            if trade_mount > 0.0:
                order = self.trade_market('sell', trade_mount)

        elif cur_price > hilo[0] and cur_price < hilo[1]:
            # TODO
            if checkins[1] < 0.0:
                # TODO
                trade_mount = '%.2f' % (abs(checkins[1]))
                order = self.trade_market('buy', trade_mount)
                time.sleep(3)
            elif checkins[1] > 0.0:
                # TODO
                # sell back
                trade_mount = '%.2f' % (abs(checkins[1]))
                order = self.trade_market('sell', trade_mount)
                time.sleep(3)
            # set an oco
            order = self.trade_oco1(hilo[0], hilo[1], self.init_trade_amount)
            self.order_exist == True
        return(order)

        # check the position

    # detect order in hour
    # record the inital state of position
    # if position changed
    # detect the profit
    # following profit ever 1 min, if profit is starting to reduce , quite (need a trial order)
    def trade_in_hour(self, initposition, starttime):
        trial_loss_cut = 1500 # if the dynamic loss touches 2000, quit position.
        time.sleep(60)
        self.switch_in_hour = False
        tdelta = self.bf_timejudge(starttime)
        while tdelta < 3600:
            checkins = self.get_checkin_price()
            new_position = float('%.2f' % (math.floor(checkins[1])))
            if initposition != 0 and new_position * initposition < 0:
                self.switch_in_hour = True
            elif initposition == 0.0 and new_position != 0.0:
                self.switch_in_hour = True
            if self.switch_in_hour:
                predict.print_and_write('switch in hour')
                self.trial_order(checkins, trial_loss_cut, starttime)
            else:
                predict.print_and_write('no switch happened in hour')
                time.sleep(60)
            tdelta = self.bf_timejudge(starttime)


    def trial_order(self, checkins, trial_loss_cut, starttime):
        # Trial order keep loss less than 2000
        profit = 0
        pre_profit = -trial_loss_cut
        tdelta = self.bf_timejudge(starttime)
        while tdelta < 3600:
            cur_price = self.get_current_price(100)
            if checkins[1] > 0:
                profit = cur_price - checkins[0]
            elif checkins[1] < 0:
                profit = checkins[0] - cur_price

            if profit < pre_profit:
                # TODO quit
                if checkins[1] > 0.0:
                    trade_mount = abs('%.2f' % (checkins[1]))
                    order = self.trade_market('sell', trade_mount)
                    predict.print_and_write(order)
                elif checkins[1] < 0.0:
                    trade_mount = abs('%.2f' % (checkins[1]))
                    order = self.trade_market('buy', trade_mount)
                    predict.print_and_write(order)
                predict.print_and_write('quit position')
                self.order_exist == False
                tdelta = self.bf_timejudge(starttime)
                if tdelta < 3600:
                    time.sleep(3600-tdelta)
                return

            elif profit >= pre_profit and profit > 0:
                pre_profit = profit - trial_loss_cut
            time.sleep(60)
            tdelta = self.bf_timejudge(starttime)

    def update_order(self, checkins, hilo):
        order = ''
        if checkins[1] < 0.0:
            # TODO
            # buy double
            trade_mount = '%.2f' % (self.init_trade_amount - checkins[1])
            if trade_mount > 0.0:
                order = self.trade_stop('buy', hilo[1],  trade_mount)
                self.order_exist == True
        elif checkins[1] > 0.0:
            # TODO
            # sell double
            trade_mount = '%.2f' % (self.init_trade_amount + checkins[1])
            if trade_mount > 0.0:
                order = self.trade_stop('sell', hilo[0], trade_mount)
                self.order_exist == True
        return order


    def judge_condition(self): # judge position at hour start.
        starttime = time.gmtime()
        if self.order_exist == True:
            remain_test = self.cancel_order(self.order_id) + 1
            predict.print_and_write('cancel order, remain %f'%(remain_test -1))
            self.order_exist == False

        checkins = self.get_checkin_price()
        cur_price = self.get_current_price(100)
        hilo = self.get_hilo()

        # if keep a position and transfor in this hour. ckeck position again:
        if (checkins[1] != 0.0 and self.switch_in_hour) or checkins[1] == 0.0:
            if checkins[1] == 0.0:
                predict.print_and_write('No position exist, trade none position')
            else:
                predict.print_and_write('Trade with position and init position')
            self.order_id = self.trade_hour_init(checkins, cur_price, hilo)
            # we should verify the order is dealing or not here
            time.sleep(60) # in 200s , we should obvious the position change.
            checkins = self.get_checkin_price()
            self.order_id = self.update_order(checkins, hilo)

        elif checkins[1] != 0.0 and not self.switch_in_hour:
            self.order_id = self.update_order(checkins, hilo)

        self.trade_in_hour(checkins[1], starttime)


if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)
    autoTrading = AutoTrading()
    if argc >= 2:
        autoTrading.switch_in_hour = bool(sys.argv[1])

    #tdelta = autoTrading.bf_timejudge('2018-05-21T14:35:44.713')
    while 1:
        autoTrading.judge_condition()
