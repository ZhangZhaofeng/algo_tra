

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



    def __init__(self):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))
        self.zaif_api = ZaifTradeApi(key=str(ks.zaif_api), secret=str(ks.zaif_secret))
        self.quoinex_api = client.Quoinex(api_token_id=str(ks.quoinex_api), api_secret=(ks.quoinex_secret))
        self.bitbank_api = private_api.bitbankcc_private(api_key=str(ks.bitbank_api), api_secret=str(ks.bitbank_secret))

    def trade_quoine_condmarket(self, type, buysellprice ,amount):
        print("trade_quoine")

        if type == 'BUY' or type == 'buy':
            #order = self.quoinex_api.create_market_buy(product_id=5, quantity=str(amount), price_range=str(buysellprice))
            order = self.quoinex_api.create_order(order_type='stop', product_id=5, side='buy', quantity=str(amount), price=str(buysellprice))
        elif type == "SELL" or type == "sell":
            order = self.quoinex_api.create_order(order_type='stop', product_id=5, side='sell', quantity=str(amount), price=str(buysellprice))
        else:
            print("error!")
        return(order)

    #def get_balance(self):

    def get_orders(self):
        order = self.quoinex_api.get_orders()
        #order = self.quoinex_api.get_orders(status='live')
        return (order['models'])

    def get_orderbyid(self, id):
        order = self.quoinex_api.get_order(id)
        return (order)

    def cancle_order(self, id):
        try:
            checkid = self.quoinex_api.cancel_order(id)
            remain_amount = float(checkid['quantity']) - float(checkid['filled_quantity'])
            return(remain_amount)
        except Exception:
            time.sleep(5)
            order = self.get_orderbyid(id)
            if order['status'] == 'filled':
                print('Filled before cancelling')
                return(0.0)

    def onTrick_trade(self, buyprice, sellprice, tradeamount = 1000.0):

        buyprice = float(buyprice)
        sellprice = float(sellprice)
        tradeamount = float(tradeamount)

        if self.order_places['exist']: # if there is a order detect if it filled or not yet

            placed = self.get_orderbyid(self.order_places['id'])
            if placed['status'] == 'filled':

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

                if self.order_places['remain'] < 0.005: # little remain treat as buy succeed
                    if self.order_places['type'] == 'buy': #
                        predict.print_and_write('Buy order filled')
                        self.holdflag = True
                        amount = tradeamount / sellprice - self.order_places['remain']
                        if amount < 0.001:
                            amount = 0.001
                    else: # treat as sell succeed
                        predict.print_and_write('Sell order filled')
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
                    new_order = self.trade_quoine_condmarket(side, sellprice, amount)
                    predict.print_and_write('Order placed sell %f @ %f'%(amount, sellprice))
                else:
                    new_order = self.trade_quoine_condmarket(side, buyprice, amount)
                    predict.print_and_write('Order placed buy %f @ %f' % (amount, buyprice))
                self.order_places['exist'] = True
                self.order_places['id'] = new_order['id']
                self.order_places['remain'] = amount
                self.order_places['type'] = side
                return(self.order_places['id'])
            except Exception:
                print('Error! Try again')
                continue
                try_times -= 1

        return(-2) # try too many times stop trading

    #def get_property(self):

    #def get_profit(self):

    #def judge_if_ordered(self):

if __name__ == '__main__':
    autoTrading = AutoTrading()
    prediction = predict.Predict()
    while 1:
        result = prediction.get_curr_cond_market_price()
        curtime = str(result[2][-1])
        predict.print_and_write('%s sell: %.0f , buy : %.0f' % (curtime, result[0][-1], result[1][-1]))
        oid = autoTrading.onTrick_trade(result[1][-1], result[0][-1])
        if oid == -1 or oid == -2:
            break
            print(oid)
        print('wait 15 min')
        time.sleep(60*15)
