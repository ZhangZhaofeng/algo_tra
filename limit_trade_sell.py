#!/usr/bin/python3
# coding=utf-8

import tenlines
import time

if __name__ == '__main__':
    tenlines=tenlines.Tenlines()
    tenlines.execute_trade("SELL", 0.01)
    time.sleep(2)
    tenlines.update_mystatus_pos()