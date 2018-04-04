
import technical_test
import talib
from datetime import  datetime
from talib import MA_Type
from talib.abstract import *

class Sigmatrend(technical_test.GMMA):

    def get_bollinger(self, num=1000, periods="1H"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            num=num, periods=periods, converter=False)
        (upper, middle, lower) = talib.BBANDS(close_price.T[0], timeperiod=20, nbdevup=0.5, nbdevdn=0.5 ,matype=MA_Type.SMA)

        ma = talib.EMA(close_price.T[0], 60)
        time = datetime.fromtimestamp(time_stamp[-1]).strftime('%H:%M:%S')
        #(upper, middle, lower) = BBANDS(ma[-40:], 20, 0.5, 0.5)
        return(time,upper[-10:],middle[-10:],lower[-10:])
        #return([upper[-40:],middle[-40:],lower[-40:],close_price[-40:],ma[-40:]])



if __name__ == '__main__':
    ST = Sigmatrend()
    result = ST.get_bollinger()
    print(result)