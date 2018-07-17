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
            predict.print_and_write('OCO stopmarket buy: %f, sell %f, amount %f' % (float(buy), float(sell), float(amount)))
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

        product = 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 575
        try_t = 0
        while try_t < 20:
            if type == 'BUY' or type == 'buy':
                order = self.bitflyer_api.sendchildorder(product_code=product, child_order_type='MARKET',
                    side='BUY', size= str(amount))
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_MARKET', 'amount', '%f' % float(amount)])
                predict.print_and_write('Buy market ' +amount)
            elif type == "SELL" or type == "sell":
                order = self.bitflyer_api.sendchildorder(product_code=product, child_order_type='MARKET',
                                                         side='SELL', size=str(amount))
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_MARKET', 'amount', '%f' % float(amount)])
                predict.print_and_write('Sell market ' +amount)
            else:
                print("error!")
            if 'child_order_acceptance_id' in order:
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
                predict.print_and_write('Buy stop market %f at %f' % (float(amount), price - 500))
            elif type == "SELL" or type == "sell":
                parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                           'trigger_price': str(price+500), 'size': str(amount)}]
                order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time,
                                                      parameters=parameters)
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_STOP', 'amount', '%f' % float(amount)])
                predict.print_and_write('Sell stop market %f at %f' % (float(amount), price + 500))
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

    def get_curhour(self):
        cur_hour = datetime.datetime.fromtimestamp(time.time() - time.time() % 3600)
        return(cur_hour.timestamp())

    def judge_order(self, id):
        i = 20
        while i > 0:
            try:
                order = self.get_orderbyid(id)
                if order['parent_order_state'] == 'REJECTED':
                    predict.print_and_write('Order rejected')
                    return True
                else:
                    return False
            except Exception:
                time.sleep(5)
                print(Exception)
                print('Exception Try again')
                i -= 1
        predict.print_and_write('Try many times but no result, return False without confidence')
        return False

    def get_hilo(self):
        i = 0
        while i < 30:
            try:
                hilos = technical_fx_bidirc.HILO()
                result = hilos.publish_current_hilo_price()

        # result = prediction.publish_current_limit_price(periods="1H")
                sell = float(result[1])
                buy = float(result[0])
                close = float(result[2])  # the close price of last hour
                return([sell, buy, close])
            except Exception:
                print(Exception)
                predict.print_and_write('Try to get hilo again')
                time.sleep(10)
                i+=1
                continue

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
                if order['parent_order_state'] == 'CANCELED' or order['parent_order_state'] == 'REJECTED':
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
        predict.print_and_write('Cancel failed,( May be just lag)')
        return (0.0)

    def get_checkin_price(self):
        p = self.bitflyer_api.getpositions(product_code='FX_BTC_JPY')
        position0 = 0.0
        checkin_price = 0.0
        #time_diff = 0
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

            # for i in p:
            #     opentime = i['open_date']
            #     time_diff = self.bf_timejudge(opentime)
            #     break

        elif isinstance(p, dict) or len(p) == 0:
            predict.print_and_write('Position not exist')
        checkin_price = math.floor(checkin_price)
        return([checkin_price, position0])

    def get_current_price(self, numbers):
        trade_history = self.bitflyer_api.executions(product_code = 'FX_BTC_JPY', count = 100)
        total_size = 0.0
        cur_price = 0.0
        for i in trade_history:
            total_size += i['size']

        for i in trade_history:
            cur_price += i['size']/total_size * i['price']

        return(math.floor(cur_price))



    def trade_hour_init(self, checkins, cur_price, hilo): # if we have a new position in this hour
        self.switch_in_hour = False
        if hilo[2] >= hilo[1] : # if close > hi and position is negative
            #TODO
            trade_mount = self.init_trade_amount - checkins[1]
            if trade_mount > 0.0:
                amount_str = '%.2f' % (trade_mount)
                self.trade_market('buy', amount_str)
                predict.print_and_write('Switch to long')
            amount_stop = '%.2f' % (self.init_trade_amount*2)
            order = self.trade_stop('sell', hilo[0], amount_stop)
            self.order_exist = True
            # buy self.init + checkins[1]

        elif hilo[2] <= hilo[0] : # if close < lo and position is positive
            # TODO
            # sell self.init + checkins[1]
            trade_mount = self.init_trade_amount + checkins[1]
            if trade_mount > 0.0:
                amount_str = '%.2f' % (trade_mount)
                self.trade_market('sell', amount_str)
                predict.print_and_write('Switch to short')
            amount_stop = '%.2f' % (self.init_trade_amount * 2)
            order = self.trade_stop('buy', hilo[1], amount_stop)
            self.order_exist = True


        elif cur_price > hilo[0] and cur_price < hilo[1]:
            predict.print_and_write('Switch to middle')
            # TODO
            if checkins[1] < 0.0:
                # TODO
                trade_mount = '%.2f' % (abs(checkins[1]))
                self.trade_market('buy', trade_mount)
                predict.print_and_write('Buy short back')
                time.sleep(3)
            elif checkins[1] > 0.0:
                # TODO
                # sell back
                trade_mount = '%.2f' % (abs(checkins[1]))
                self.trade_market('sell', trade_mount)
                predict.print_and_write('Sell long back')
                time.sleep(3)
            # set an oco
            order = self.trade_oco1(hilo[0], hilo[1], self.init_trade_amount)
            self.order_exist = True
        return(order)

        # check the position

    # detect order in hour
    # record the inital state of position
    # if position changed
    # detect the profit
    # following profit ever 1 min, if profit is starting to reduce , quite (need a trial order)
    def trade_in_hour(self, initposition, starttime):
        trial_loss_cut = 1500 # if the dynamic loss touches 2000, quit position.
        time.sleep(1)
        self.switch_in_hour = False
        tdelta = self.bf_timejudge(starttime)
        while tdelta < 3600:
            checkins = self.get_checkin_price()
            new_position = float('%.2f' % (checkins[1]))
            if initposition != 0 and new_position * initposition < 0:
                self.switch_in_hour = True
            elif initposition == 0.0 and new_position != 0.0:
                self.switch_in_hour = True
            if self.switch_in_hour:
                predict.print_and_write('switch in hour')
                self.trial_order(checkins, trial_loss_cut, starttime)
                self.switch_in_hour = False
            else:
                print('.')
                time.sleep(60)
            tdelta = self.bf_timejudge(starttime)


    def trial_order(self, checkins, trial_loss_cut, starttime):
        # Trial order keep loss less than 2000
        profit = 0
        pre_profit = -trial_loss_cut
        tdelta = self.bf_timejudge(starttime)
        predict.print_and_write('Use a trial order')
        predict.print_and_write('Current position: %f, price: %f' % (checkins[1], checkins[0]))
        while tdelta < 3600:
            cur_price = self.get_current_price(100)
            if checkins[1] > 0:
                profit = cur_price - checkins[0]
            elif checkins[1] < 0:
                profit = checkins[0] - cur_price

            if profit < pre_profit:
                # TODO quit
                if checkins[1] > 0.0:
                    trade_mount = '%.2f' % abs(checkins[1])
                    order = self.trade_market('sell', trade_mount)
                    predict.print_and_write(order)
                elif checkins[1] < 0.0:
                    trade_mount = '%.2f' % abs(checkins[1])
                    order = self.trade_market('buy', trade_mount)
                    predict.print_and_write(order)
                predict.print_and_write('Quit position')
                self.order_exist = False
                tdelta = self.bf_timejudge(starttime)
                if tdelta < 3600:
                    time.sleep(3600-tdelta)
                return

            elif profit >= pre_profit and profit > 0:
                temp_pre_profit = profit - trial_loss_cut
                if temp_pre_profit > pre_profit:
                    pre_profit = temp_pre_profit
            predict.print_and_write('Profit: %f' % profit)
            time.sleep(60)
            tdelta = self.bf_timejudge(starttime)

    def update_order(self, checkins, hilo):
        order = ''
        if checkins[1] < 0.0:
            # TODO
            # buy double
            trade_mount = self.init_trade_amount - checkins[1]
            if trade_mount > 0.0:
                amount_str = '%.2f' % (trade_mount)
                order = self.trade_stop('buy', hilo[1],  amount_str)
                predict.print_and_write('Update a buy stop order')
                self.order_exist = True
        elif checkins[1] > 0.0:
            # TODO
            # sell double
            trade_mount = self.init_trade_amount + checkins[1]
            if trade_mount > 0.0:
                amount_str = '%.2f' % (trade_mount)
                order = self.trade_stop('sell', hilo[0], amount_str)
                predict.print_and_write('Update a sell stop order')
                self.order_exist = True
        return order


    def judge_condition(self): # judge position at hour start.
        starttime = time.gmtime(self.get_curhour())
        if self.order_exist == True:
            remain_test = self.cancel_order(self.order_id) + 1
            predict.print_and_write('cancel order, remain %f'%(remain_test -1))
            self.order_exist = False

        checkins = self.get_checkin_price()
        cur_price = self.get_current_price(100)
        predict.print_and_write('Current price: %f' % (cur_price))
        hilo = self.get_hilo()

        # if keep a position and transfor in this hour. ckeck position again:
        if (checkins[1] != 0.0 and self.switch_in_hour) or checkins[1] == 0.0:
            if checkins[1] == 0.0:
                predict.print_and_write('No position exist, trade none position')
            else:
                predict.print_and_write('Trade with position %f and init position'%checkins[1])
            order = self.trade_hour_init(checkins, cur_price, hilo)
            #self.order_id = order['parent_order_acceptance_id']

            # we should verify the order is dealing or not here
            time.sleep(10) # in 200s , we should obvious the position change.
            checkins = self.get_checkin_price()
            #order = self.update_order(checkins, hilo)
            self.order_id = order['parent_order_acceptance_id']

        elif checkins[1] != 0.0 and not self.switch_in_hour:
            predict.print_and_write('Update order')
            order = self.update_order(checkins, hilo)
            self.order_id = order['parent_order_acceptance_id']

        self.trade_in_hour(checkins[1], starttime)

    def get_collateral(self):
        try:
            result = self.bitflyer_api.getcollateral(product_code = 'FX_BTC_JPY')
            data2csv.data2csv(result)
            predict.print_and_write(result)
        except Exception:
            predict.print_and_write(Exception)

def sendamail(title ,str):
    address = '@'  # change the reciver e-mail address to yours
    username = 'goozzfgle@gmail.com'
    paswd = ''

    mail_str = '%s %s' % (str, formatdate(None, True, None))
    sender = SendMail(address, username, paswd)
    msg = MIMEText(mail_str)
    msg['Subject'] = title
    msg['From'] = username
    msg['To'] = address
    msg['Date'] = formatdate()
    sender.send_email(address, msg.as_string())

if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)
    autoTrading = AutoTrading()
    if argc >= 2:
        autoTrading.switch_in_hour = bool(sys.argv[1])

    #tdelta = autoTrading.bf_timejudge('2018-05-21T14:35:44.713')
    try_times = 20
    #tdelta = autoTrading.bf_timejudge('2018-05-21T14:35:44.713')
    while try_times > 0:
        try:
            while 1:
                autoTrading.judge_condition()
                autoTrading.get_collateral()
        except Exception:
            print(Exception)
            sendamail('Exception', 'exception happend')
            predict.print_and_write('Exception happened, try again')
            predict.print_and_write('Last try times: %d'%try_times)
            try_times -= 1
