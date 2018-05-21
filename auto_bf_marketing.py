from tradingapis.bitflyer_api import pybitflyer
import keysecret as ks
import time
import predict
import configIO
import sys
import math
import data2csv



class AutoTrading:
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

    def trade_simple(self, buy, sell, amount = 0.01):
        self.maintance_time()

        product = 'FX_BTC_JPY'
        print('trade bitflyer, buy: %f, sell %f'%(buy, sell))
        expire_time = 75
        order = self.bitflyer_api.sendchildorder(product_code='FX_BTC_JPY',
                                                     child_order_type='LIMIT',
                                                     side="BUY",
                                                     size=amount,
                                                     price= '%.0f'%buy,
                                                     minute_to_expire=75)
        data2csv.data2csv(
                [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_LIMIT', 'amount', '%f' % float(amount), 'limit',
                 '%f' % float(buy)])
        time.sleep(1)
        print(order)
        order = self.bitflyer_api.sendchildorder(product_code='FX_BTC_JPY',
                                                  child_order_type='LIMIT',
                                                  side='SELL',
                                                  size=amount,
                                                  price='%.0f'%sell,
                                                  minute_to_expire=75)
        data2csv.data2csv(
                [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_LIMIT', 'amount', '%f' % float(amount), 'limit',
                 '%f' % float(sell)])
        print(order)

    def get_depth(self):
        depth =self.bitflyer_api.board(product_code = 'FX_BTC_JPY', count = 100)
        return(depth)

    def get_current_price(self, numbers):
        trade_history = self.bitflyer_api.executions(product_code = 'FX_BTC_JPY', count = 100)
        total_size = 0.0
        cur_price = 0.0
        for i in trade_history:
            total_size += i['size']

        for i in trade_history:
            cur_price += i['size']/total_size * i['price']

        return(math.floor(cur_price))

    def judge_market(self):
        #1. judge if bull or bear
        mid_price, sell_depth, buy_depth = self.get_price(self.get_depth(), if123 = True)
        margin1 = mid_price * 0.00004
        bull = False
        bear = False

        buyselllastprice = self.get_last_price(self.get_last_executions())

        lastprice = buyselllastprice[0][0:20]

        if mid_price > max(lastprice[0:]) + margin1 and mid_price > lastprice[1]:
            print('bull')
            bull = True
        elif mid_price < min(lastprice[0:]) - margin1 and mid_price < lastprice[1]:
            print('bear')
            bear = True

        if bull or bear:
            return False
        else:
            return True

    def get_price(self, depth, if123=False):
        asks = depth['asks'][:30]
        bids = depth['bids'][:30]

        sell_price = float(asks[0]['price'])
        buy_price = float(bids[0]['price'])
        sell_price1 = sell_price
        buy_price1 = buy_price
        sell_price2 = float(asks[1]['price'])
        buy_price2 = float(bids[1]['price'])
        sell_price3 = float(asks[2]['price'])
        buy_price3 = float(bids[2]['price'])
        amount_asks = 0.0
        amount_bids = 0.0
        largest_diff = 400
        mini_diff = 200
        float_amount_buy = 0.01
        float_amount_sell = 0.01
        buy_depth = 0.0
        sell_depth = 0.0

        for i in range(0, 30):
            sell_depth += float(asks[i]['size'])
            buy_depth += float(bids[i]['size'])

        len_a = len(asks)
        for i in range(0, len_a):
            amount_asks += float(asks[i]['size'])
            if amount_asks > float_amount_sell:
                sell_price = float(asks[i]['price']) - 3.0
                break

        len_b = len(bids)
        for i in range(0, len_b):
            amount_bids += float(bids[i]['size'])
            if amount_bids > float_amount_buy:
                buy_price = float(bids[i]['price']) + 3.0
                break

        ave_price = (sell_price1 + buy_price1) / 2 * 0.7 + (sell_price2 + buy_price2) / 2 * 0.2 + (
                                                                                                  sell_price3 + buy_price3) / 2 * 0.1
        mid_price = (sell_price1 + buy_price1) / 2
        if sell_price - mid_price > largest_diff:
            sell_price = mid_price + largest_diff
        if mid_price - buy_price > largest_diff:
            buy_price = mid_price - largest_diff

        if sell_price - mid_price < mini_diff:
            sell_price = mid_price + mini_diff
        if mid_price - buy_price > largest_diff:
            buy_price = mid_price - mini_diff

            sell_price = float('%.2f' % sell_price)
            buy_price = float('%.2f' % buy_price)

        if if123:
            return (ave_price, sell_depth, buy_depth)
        else:
            return ([buy_price, sell_price])

if __name__ == '__main__':
    at = AutoTrading()
    depth = at.get_depth()
    results = at.get_price(depth, if123=False)
    sell = results[0]
    buy = results[1]


    at.trade_simple(buy, sell)
    print(results)
