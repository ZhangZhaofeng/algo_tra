
from tradingapis.bitflyer_api import pybitflyer
from tradingapis.bitbank_api import public_api, private_api
from tradingapis.zaif_api.impl import ZaifPublicApi, ZaifTradeApi
from tradingapis.zaif_api.api_error import *
from tradingapis.quoine_api import client
import keysecret as ks
import time
import copy
import predict




class AutoTrading:
    currency_jpy = 0 # jpy btc
    currency_btc = 0
    holdflag = False
    order_places = {
            'exist': False,
            'type': '',
            'id': 0,
            'remain' : 0.0
        }
    tradeamount = 1000



    def __init__(self, holdflag = False, order_places = {'exist': False, 'type': '','id': 0,'remain' : 0.0}, tradeamount = 1000):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))
        self.holdflag = holdflag
        self.order_places = order_places
        self.tradeamount = tradeamount

    def trade_bitflyer_constoplimit(self, type, buysellprice, amount):
        product= 'BTC_JPY'
        slide = 100
        print('trade bitflyer')
        if type == 'BUY' or type == 'buy':
            # order = self.quoinex_api.create_market_buy(product_id=5, quantity=str(amount), price_range=str(buysellprice))
            parameters =  [{ 'product_code' : product, 'condition_type' : 'STOP_LIMIT', 'side': 'BUY',
                            'price': str(buysellprice+slide), 'size': str(amount), 'trigger_price': str(buysellprice)}]

            #order = self.bitflyer_api.sendchildorder(product_code="BTC_JPY",
            #                                         child_order_type="MARKET",
            #                                         side="BUY",
            #                                         size=amount,
            #                                         minute_to_expire=10000,
            #                                         time_in_force="GTC"
            #                                         )

            order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', parameters=parameters)
        elif type == "SELL" or type == "sell":
            parameters = [{'product_code': product, 'condition_type': 'STOP_LIMIT', 'side': 'SELL',
                          'price': str(buysellprice-slide), 'size': str(amount), 'trigger_price': str(buysellprice)}]

            order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', parameters=parameters)
        else:
            print("error!")
        return (order)

    def get_orders(self, status = ''):
        #order = self.quoinex_api.get_orders()
        #order = self.quoinex_api.get_orders(status, limit)
        #ACTIVE CANCELED
        product = 'BTC_JPY'
        if status != '':
            order = self.bitflyer_api.getparentorders(product_code=product, child_order_state=status)
        else:
            order = self.bitflyer_api.getparentorders(product_code=product, count=30)
        return (order)

    def get_orderbyid(self, id):
        product = 'BTC_JPY'
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

    def cancle_order(self, id):
        product = 'BTC_JPY'
        i = 20
        while i>0:
            try:
                statue = self.bitflyer_api.cancelparentorder(product_code=product, parent_order_acceptance_id=id)
                time.sleep(5)
                order = self.get_orderbyid(id)
                child_order = self.bitflyer_api.getchildorders(product_code=product, parent_order_id =order['parent_order_id'])
                if child_order != []:
                    self.bitflyer_api.cancelchildorder(product_code=product, child_order_id=child_order['child_order_id'])
                if order['parent_order_state'] == 'CANCELED':
                    print('Order cancelled')
                    remain_amount = float(order['cancel_size'])
                    return(remain_amount)
                else:
                    return(0)
            except Exception:
                order = self.get_orderbyid(id)
                if order['parent_order_state'] == 'COMPLETED':
                    print('Executed before cancelling')
                    return(0.0)
                time.sleep(5)
                print('Try again cancelling')
                i -= 1

    def onTrick_trade(self, buyprice, sellprice, avg_open):

        buyprice = float(buyprice)
        sellprice = float(sellprice)
        tradeamount = float(self.tradeamount)

        if self.order_places['exist']: # if there is a order detect if it filled or not yet

            placed = self.get_orderbyid(self.order_places['id'])

            if placed['executed_size'] == self.order_places['remain']:
            #if placed['status'] == 'filled':
                #avg_price = float(placed['average_price'])
                self.order_places['exist'] = False
                self.order_places['id'] = 0
                self.order_places['remain'] = .0

                if self.order_places['type'] == 'buy':
                    predict.print_and_write('Buy order filled')
                    self.holdflag = True
                    amount = tradeamount / sellprice
                else:
                    predict.print_and_write('Sell order filled')
                    self.holdflag = False
                    amount = tradeamount / buyprice

            else: # not filled or partly filled
                self.order_places['remain'] = self.cancle_order(self.order_places['id'])
                self.order_places['exist'] = False
                self.order_places['id'] = 0

                if self.order_places['remain'] < 0.001: # little remain treat as buy succeed
                    if self.order_places['type'] == 'buy': #
                        predict.print_and_write('Buy order filled remain %f'%self.order_places['remain'])
                        self.holdflag = True
                        amount = tradeamount / sellprice - self.order_places['remain']
                        if amount < 0.001:
                            amount = 0.001
                    else: # treat as sell succeed
                        predict.print_and_write('Sell order filled remain %f'%self.order_places['remain'])
                        self.holdflag = False
                        amount = tradeamount / buyprice - self.order_places['remain']
                        if amount < 0.001:
                            amount = 0.001

                else: # partly filled and large remain treat as buy failed
                    if self.order_places['type'] == 'buy': #
                        predict.print_and_write('Buy order not filled buy again')
                        self.holdflag = False
                        amount = self.order_places['remain'] # continue buy
                        if amount < 0.001:
                            amount = 0.001
                        #
                    else: # treat as sell succeed
                        predict.print_and_write('Sell order not filled sell again')
                        self.holdflag = True
                        amount = self.order_places['remain'] # continue sell
                        if amount < 0.001:
                            amount = 0.001

        else:
            if self.holdflag:
                amount = tradeamount / sellprice
            else:
                amount = tradeamount / buyprice

        if self.holdflag:
            side = 'sell'
        else:
            side = 'buy'


        amount = float(str('%.3f'%amount))
        if amount < 0.001:
            print('less than min amount')
            return(-1) # less than min amount stop trading

        try_times = 20
        while try_times > 0:
            try:
                if side == 'sell':
                    new_order = self.trade_bitflyer_constoplimit(side, sellprice, amount)
                    predict.print_and_write('Order placed sell %f @ %f'%(amount, sellprice))
                else:
                    new_order = self.trade_bitflyer_constoplimit(side, buyprice, amount)
                    predict.print_and_write('Order placed buy %f @ %f' % (amount, buyprice))
                self.order_places['exist'] = True
                self.order_places['id'] = new_order['parent_order_acceptance_id']
                self.order_places['remain'] = amount
                self.order_places['type'] = side
                return(self.order_places['id'])
            except Exception:
                print('Error! Try again')
                time.sleep(5)
                try_times -= 1



        return(-2) # try too many times stop trading




    def get_profit(self):
        balances = self.bitflyer_api.getbalance(product_code="BTC_JPY")
        jpy_avai = 0.0
        btc_avai = 0.0
        for balance in balances:
            if balance['currency_code'] == 'JPY':
                jpy_avai = float(balance['available'])
            elif balance['currency_code'] == 'BTC':
                btc_avai = float(balance['available'])
        return ([jpy_avai, btc_avai])


if __name__ == '__main__':
    autoTrading = AutoTrading(holdflag=False, order_places={'exist':False,'type':'','id':0,'remain':0.0}, tradeamount=1000)
    prediction = predict.Predict()
    profits = autoTrading.get_profit()
    init_jpy = profits[0]
    init_btc = profits[1]
    predict.print_and_write('Profit jpy: %s btc: %s'%(init_jpy, init_btc))

    while 1:
        result = prediction.publish_current_limit_price(periods="1H")
        predict.print_and_write('sell: %.0f , buy : %.0f' % (result[1], result[0]))
        sell = float(result[1])
        buy = float(result[0])
        #adjust_result = autoTrading.bitf2qix(buy, sell)
        #avg_open = autoTrading.get_open()
        #oid = autoTrading.onTrick_trade(adjust_result[0], adjust_result[1], avg_open) # buy ,sell
        oid = autoTrading.onTrick_trade(buy, sell, 0)  # buy ,sell
        #order = autoTrading.cancle_order(235147969)
        #order = autoTrading.get_orderbyid(235147969)
        if oid == -1 or oid == -2:
            print(oid)
            break
        print('wait 60 min')
        time.sleep(60*60)
        profits = autoTrading.get_profit()
        cur_jpy = profits[0]
        cur_btc = profits[1]
        predict.print_and_write('Profit jpy: %s btc: %s' % (cur_jpy, cur_btc))
