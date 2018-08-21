from tradingapis.bitflyer_api import pybitflyer
import keysecret as ks
import time
import datetime
import predict
import configIO
import sys
import technical_fx_hilo
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

    def send_email(self, toaddress ,mesage):
        self.connect_mail_server()
        try:
            self.s.sendmail(self.from_add, toaddress, mesage)
            print('Send a mail to %s' % (toaddress))
        except smtplib.SMTPDataError:
            print('Can not send a mail, maybe reach the daily limition')


class AutoTrading:

    order_id = ''
    ovrshoot = 1500
    init_trade_amount = 0.01
    last_profit = 0

    def __init__(self):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))

    def trade_market(self, type, amount, wprice = 10000):
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
                predict.print_and_write('Buy market ' +str(amount))
            elif type == "SELL" or type == "sell":
                order = self.bitflyer_api.sendchildorder(product_code=product, child_order_type='MARKET',
                                                         side='SELL', size=str(amount))
                data2csv.data2csv(
                    [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_MARKET', 'amount', '%f' % float(amount)])
                predict.print_and_write('Sell market ' +str(amount))
            else:
                print("error!")
            if 'child_order_acceptance_id' in order:
                time.sleep(10)
                execute_price = self.get_execute_order()
                if execute_price != 0:
                    if type == "SELL" or type == "sell":
                        slides = float(wprice) - float(execute_price)
                        predict.print_and_write('SELL : Wish price: %f, deal price: %f, slide : %f'%(wprice, execute_price, slides))
                    elif type == "BUY" or type == "buy":
                        slides = float(execute_price) - float(wprice)
                        predict.print_and_write('BUY : Wish price: %f, deal price: %f, slide : %f'%(wprice, execute_price, slides))
                return order
            else:
                try_t += 1
                print(order)
                print('Failed, try again')
                time.sleep(10)


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

    def get_execute_order(self):
        try:
            result = self.bitflyer_api.getexecutions(product_code = 'FX_BTC_JPY',count = 1)
            #print(result['price'])
            return(float(result[0]['price']))
        except Exception:
            return (0)

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
        cur_hour = datetime.datetime.fromtimestamp(time.time() - time.time() % 3600 +5)
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
                hilos = technical_fx_hilo.HILO()
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
            #predict.print_and_write('Check in price: %f, position: %f' % (checkin_price, position0))

            # for i in p:
            #     opentime = i['open_date']
            #     time_diff = self.bf_timejudge(opentime)
            #     break

        elif isinstance(p, dict) or len(p) == 0:
            predict.print_and_write('Position not exist')
        checkin_price = math.floor(checkin_price)
        return([checkin_price, position0])

    def get_current_price(self, number):
        d = 200
        while d > 0:
            try:
                trade_history = self.bitflyer_api.executions(product_code = 'FX_BTC_JPY', count = number)
                total_size = 0.0
                cur_price = 0.0
                for i in trade_history:
                    total_size += i['size']

                for i in trade_history:
                    cur_price += i['size']/total_size * i['price']

                if cur_price < 1000:
                    continue
                print("CP:%s " % (cur_price), end='\r')
                return(math.floor(cur_price))
            except Exception:
                print('Get price error ,try again')
                time.sleep(10)
                d -= 1
                continue
        print('Try too many times, failed')
        return 0.0

    def detect_and_trade(self, direction, line, amount):
        price = self.get_current_price(30)
        if direction == 'buy':
            if price > line and price != 0 :
                predict.print_and_write(price)
                order = self.trade_market('buy', amount, int(price))
                predict.print_and_write(order)
                return(True)
        elif direction == 'sell':
            if price < line and price != 0 :
                predict.print_and_write(price)
                order = self.trade_market('sell', amount, int(price))
                predict.print_and_write(order)
                return(True)
        return(False)



    def judge_overshoot(self, hilo, starttime):
        tdelta = self.bf_timejudge(starttime)
        ready = False
        overshoot_s = False
        overshoot_l = False
        while tdelta < 3600:
            cur_price = self.get_current_price(50)
            if ready:
                print('Ready to trade: price: %f' % cur_price, end='\r')
            else:
                print('Price: %f' % cur_price, end='\r')
            # hilo0 lo hilo1 hi
            if cur_price > hilo[0] and cur_price < hilo[1]:
                ready = True
            elif cur_price < hilo[0] - self.ovrshoot and ready:
                overshoot_s = True
            elif cur_price > hilo[1] + self.ovrshoot and ready:
                overshoot_l = True
            time.sleep(0.8)
            tdelta = self.bf_timejudge(starttime)
            if overshoot_l:
                predict.print_and_write('Detected a long trade:')
                return 'long'
            elif overshoot_s:
                predict.print_and_write('Detected a short trade:')
                return 'short'
        return 'none'

        # check the position

    # detect order in hour
    # record the inital state of position
    # if position changed
    # detect the profit
    # following profit ever 1 min, if profit is starting to reduce , quite (need a trial order)
    def trade_in_hour(self, starttime, hilo):
        self.get_collateral()
        checkins = self.get_checkin_price()
        checkin_price = checkins[0]
        position0 =  abs(float('%.2f' % (checkins[1])))
        predict.print_and_write('Check in price: %f, position: %f' % (checkin_price, position0))

        tdelta = self.bf_timejudge(starttime)
        trial_loss_cut = 2000
        #switch_line = math.floor((hilo[1] + hilo[0]) /2)

        while tdelta < 3600:

            if position0 != 0.0:
        # if we have a positive position, detect a change to quit and switch
                predict.print_and_write('')
                if tdelta < 3600:
                    self.trial_order(checkins, trial_loss_cut, starttime)

            elif position0 == 0.0:
            # if we have a positive position, detect a change to quit and switch
                predict.print_and_write('Detecting a chance')
                result = self.judge_overshoot(hilo, starttime)
                if result == 'long':
                    order = self.trade_market('buy', self.init_trade_amount, int(hilo[1] + self.ovrshoot))
                    predict.print_and_write(order)
                    suggest_position = float(self.init_trade_amount)
                    checkins = self.judge_position(suggest_position)
                    self.trial_order(checkins, trial_loss_cut, starttime)

                elif result == 'short':
                    order = self.trade_market('sell', self.init_trade_amount, int(hilo[0] - self.ovrshoot))
                    predict.print_and_write(order)
                    suggest_position = -float(self.init_trade_amount)
                    checkins = self.judge_position(suggest_position)
                    self.trial_order(checkins, trial_loss_cut, starttime)

            time.sleep(10)
            tdelta = self.bf_timejudge(starttime)
            checkins = self.get_checkin_price()
            checkin_price = checkins[0]
            position0 = abs(float('%.2f' % (checkins[1])))


    def trial_order(self, checkins, trial_loss_cut, starttime):
        # Trial order keep loss less than trial_loss_cut
        profit = 0
        max_profit = 0
        pre_profit = -trial_loss_cut
        tdelta = self.bf_timejudge(starttime)
        predict.print_and_write('Use a trial order')
        #predict.print_and_write('Current position: %f, price: %f' % (checkins[1], checkins[0]))
        while 1: #tdelta<3600
            cur_price = self.get_current_price(50)
            if checkins[1] > 0:
                profit = cur_price - checkins[0]
            elif checkins[1] < 0:
                profit = checkins[0] - cur_price
            if profit > max_profit:
                max_profit = profit
                if max_profit > trial_loss_cut * 2:
                    trial_loss_cut = max_profit /2
                if trial_loss_cut > 10000:
                    trial_loss_cut = 10000


            tdelta2 = self.bf_timejudge(starttime)
            dt = tdelta2 - tdelta

            if profit < pre_profit:
                # quit
                if checkins[1] > 0.0:
                    trade_mount = '%.2f' % abs(checkins[1])
                    order = self.trade_market('sell', trade_mount, int(cur_price))
                    predict.print_and_write(order)
                elif checkins[1] < 0.0:
                    trade_mount = '%.2f' % abs(checkins[1])
                    order = self.trade_market('buy', trade_mount, int(cur_price))
                    predict.print_and_write(order)

                predict.print_and_write('Quit position ,profit: %.2f, time: %d'%(profit, dt))

                return

            elif profit >= pre_profit and profit > 0:
                temp_pre_profit = profit - trial_loss_cut
                if temp_pre_profit > pre_profit:
                    pre_profit = temp_pre_profit
            print('T: %d, Profit: %5.0f, Max Profit: %5.0f, Losscut Profit: %5.0f' %(dt, profit, max_profit, pre_profit), end='\r')
            time.sleep(0.8)
            #tdelta = self.bf_timejudge(starttime)

    # judge if it is order succeed
    def judge_position(self, suggest_position):
        t = 0
        while t < 100000:
            checkins = self.get_checkin_price()
            if abs(suggest_position - checkins[1]) < 0.01:
                predict.print_and_write('Suggest is same as real')
                return(checkins)
            t += 1
            predict.print_and_write(
                'Position is unusual, suggest: %f, real: %f , check again' % (suggest_position, checkins[1]))
            time.sleep(5)  # in 5s , we should obvious the position change.
            if (t % 100) == 0 and t > 99 :
                predict.print_and_write('Recorrect position')
                if suggest_position - checkins[1] > 0:
                    self.trade_market('buy', '%.2f'%(suggest_position - checkins[1]))
                elif suggest_position - checkins[1] < 0:
                    self.trade_market('sell', '%.2f'%(checkins[1] -suggest_position ))
        predict.print_and_write('Something is wrong, trade but not succeed')
        return(checkins)


    def judge_condition(self): # judge position at hour start.
        time.sleep(1)
        starttime = time.gmtime(self.get_curhour())
        cur_price = self.get_current_price(100)
        predict.print_and_write('##################################################')
        predict.print_and_write('Start a new hour: Current price: %f' % (cur_price))
        hilo = self.get_hilo()

        self.trade_in_hour(starttime, hilo)


    def get_collateral(self):
        try:
            result = self.bitflyer_api.getcollateral(product_code = 'FX_BTC_JPY')
            data2csv.data2csv(result)
            predict.print_and_write(result)
        except Exception:
            predict.print_and_write(Exception)

def sendamail(title ,str):
    address = 'phoenixflame11@rakuten.jp'  # change the reciver e-mail address to yours
    username = 'goozzfgle@gmail.com'
    paswd = 'googlebaidu1'

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
    while 1:
        autoTrading.judge_condition()
        #autoTrading.get_collateral()

    #tdelta = autoTrading.bf_timejudge('2018-05-21T14:35:44.713')
    # while try_times > 0:
    #     try:
    #         while 1:
    #             autoTrading.judge_condition()
    #             autoTrading.get_collateral()
    #     except Exception:
    #         print(Exception)
    #         sendamail('Exception', 'exception happend')
    #         predict.print_and_write('Exception happened, try again')
    #         predict.print_and_write('Last try times: %d'%try_times)
    #         try_times -= 1
