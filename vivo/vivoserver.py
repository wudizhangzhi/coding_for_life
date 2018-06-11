from vivo import get_balance
from flask import Flask
import socket
import json
import time
import requests
import traceback
from flask import request

app = Flask(__name__)
"""
mount -o remount,rw /system # allow to write
"""


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/vivo', methods=['POST', 'GET'])
def vivo():
    response = []
    imei = request.args.get('imei', '')
    model = request.args.get('model', '')
    if request.method == 'POST':
        accounts = request.form.getlist('accounts')
        for account in accounts:
            print(account)
            username, password = account.split('----')
            ret = get_balance(username=username, password=password, _imei=imei, _model=model)
            response.append({username: ret})
    else:
        username = request.args.get('username', '')
        password = request.args.get('password', '')
        ret = get_balance(username=username, password=password, _imei=imei, _model=model)
        response.append({username: ret})
    return json.dumps(response)


def main():
    try:
        print('--------------------------------')
        print('''
            请访问http://127.0.0.1/vivo
            [GET]: 参数:
                    username:用户名
                    password:密码
                    imei:imei
                    model:型号名字
            [POST]: 参数:
                    accounts: [
                                'username----password',
                                'username----password',
                                'username----password',
                                'username----password',
                                ]
            返回格式:
                [
                  {
                    "14791757268": {
                      "balance": 500,
                      "respCode": "200",
                      "result": true,
                      "userT icketBalance": 55500,
                      "respMsg": "success"
                    }
                  }
                ]
        ''')
        print('--------------------------------')
        app.run(host='0.0.0.0', port=80)
    except Exception as e:
        print(e)
        a = input('回车结束')


if __name__ == "__main__":
    main()

    # id = '1022947'
    # imei = '328532726131986'
    # get_device(id, imei)

    # keep_fetch_device_save()
