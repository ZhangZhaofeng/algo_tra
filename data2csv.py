# !/usr/bin/python3
# coding=utf-8

import pandas as pd
import numpy as np
import time

def data2csv(datas, csvname = 'log_hilo_1h.csv'):

    # datas is a array
    all = [datas]
    data = pd.DataFrame(all)
    data.to_csv(csvname, mode='a', header=False)

if __name__ == '__main__':
    amount = 0.13
    trigger = 100000
    datas = [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_STOP',  '%f'%(amount), '%f'%(trigger)]
    data2 = [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_STOP', '%f' % (amount), '%f' % (trigger+300), [97000.0, 23, 0.2]]
    data2csv(datas)
    data2csv(data2)
    data2csv(data2)
    data2csv(data2)
    data2csv(data2)

