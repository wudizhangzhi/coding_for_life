# encoding: utf-8
import requests
import json
import time
from read_config import cf


class Recognize(object):
    def __init__(self, username=None, password=None):
        self.username = username or cf.get('captcha', 'username')
        self.password = password or cf.get('captcha', 'password')
        self.appid = '1'
        self.appkey = '22cc5376925e9387a23cf797cb9ba745'
        self.codetype = '1000'
        self.timeout = 60
        self.session = requests.Session()

    def balance(self):
        balance = ''
        try:
            data = {'method': 'balance',
                    'username': self.username,
                    'password': self.password,
                    'appid': self.appid,
                    'appkey': self.appkey,
                    }
            r = self.session.post('http://api.yundama.com/api.php?method=balance', data=data, timeout=self.timeout)
            response = json.loads(r.text)
            balance = response['balance']
        except Exception as e:
            print(e)
        return balance

    def upload(self, filename):
        url = 'http://api.yundama.com/api.php'
        # url = 'http://api.yundama.net:5678/api.php'
        f = open(filename, 'rb')
        try:
            files = {'file': f}
            data = {'method': 'upload',
                    'username': self.username,
                    'password': self.password,
                    'appid': self.appid,
                    'appkey': self.appkey,
                    'codetype': str(self.codetype),
                    'timeout': str(self.timeout)}
            r = self.session.post(url, data=data, files=files, timeout=self.timeout)
            print(r.text)
            response = json.loads(r.text)
            if response['ret'] and response['ret'] < 0:
                return False
            else:
                return response['cid']
        except Exception as e:
            print(e)
        finally:
            f.close()
        return False

    def result(self, cid):
        result = ''
        count = 0
        while not result and count < 10:
            try:
                r = self.session.get('http://api.yundama.com/api.php?cid=%s&method=result' % cid, timeout=self.timeout)
                response = json.loads(r.text)
                print(response)
                if response['ret'] == 0:
                    result = response['text']
            except Exception as e:
                print(e)
            time.sleep(1)
            count += 1
        return result

    def run(self, filename):
        balance = self.balance()
        print('balance: %r ' % balance)
        yzm = ''
        cid = self.upload(filename)
        if cid:
            yzm = self.result(cid)
        return yzm


if __name__ == '__main__':
    r = Recognize()
    r.run('tmp_captcha_gzyz0005.png')
