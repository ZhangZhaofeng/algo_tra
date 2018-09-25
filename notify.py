import requests,time


def notify_it(text):
    line_token = 't3o50bEkOsaNWgta9mFbOKaXtsL8xh7O54xzvMDVHuD'
    t = 5
    while t > 0:
        try:
            url = "https://notify-api.line.me/api/notify"
            data = {"message": text}
            headers = {"Authorization": "Bearer " + line_token}
            requests.post(url, data=data, headers=headers)
            return
        except Exception:
            print('Exception, try again')
            t -= 1
            time.sleep(0.2)
            continue

if __name__ == '__main__':
    wprice = 45255.434
    amount = 0.03
    notify_it('SELL : Price: %f, amount : %f'%(wprice, float(amount)))
