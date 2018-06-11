from flask import Flask
import socket
import json
import time
import requests
import traceback
from models import Device, engine
from sqlalchemy.orm import (sessionmaker, relationship)
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

@app.route('/api/xtools/x008/status', methods=['POST', 'GET'])
def status():
    data = {
    	"userName": "1000000",
    	"overTime": "false",
    	"id": "1000000",
    	"time": int(time.time()) * 1000
    }
    return json.dumps(data)

@app.route('/api/xtools/x008/sysconf', methods=['POST', 'GET'])
def sysconf():
    data = {
    	"sellUrl": "http://api2.apk00888888.com/lishu008AppManager/AuToAddDays.action",
    	"status": "1",
    	"expiryTime": int(time.time()) * 1000,
    	"vip": "true",
    	"promoteUrl": "/DownLoadFileAction.action?id=1000000",
    	"msg": "未过期",
    	"id": "1000000"
    }
    return json.dumps(data)


@app.route('/api/xtools/x008/genid', methods=['POST', 'GET'])
def genid():
    data = {

    }
    # print(request)
    return json.dumps(data)


def get_device(id, imei, **kwargs):
    url = 'http://api.008shenqi.com/api/xtools/x008/device/v1'
    # id = '1022947'
    # imei = '328532726131986'
    data = {
        'id':	id,
        'imei':	imei,
        # 'id':	'1001600',
        # 'imei':	'865166026812118',
    }
    params = {
        'time': int(time.time()),
        'id':	id,
        'imei':	imei,
    }
    headers = {
        'User-Agent': 'okhttp/3.7.0',
        'Host':	'api.008shenqi.com',
        'Content-Type':	'application/x-www-form-urlencoded',
        'Accept-Encoding':	'gzip',
        'Content-Length':	'31',
    }
    r = requests.post(url, params=params, data=data, headers=headers)
    return r.json()


def keep_fetch_device_save():
    id = '1022947'
    imei = '328532726131986'
    count = 0
    # 创建DBSession类型:
    DBSession = sessionmaker(bind=engine)
    # 创建session对象:
    session = DBSession()
    while True:
        try:
            ret = get_device(id, imei)
            model = ret['model']
            getDeviceId = ret['getDeviceId']
            print('model: {}'.format(model))
            # Duplicate removal
            query = session.query(Device).filter(Device.model==model, Device.getDeviceId==getDeviceId).all()
            if query:
                print('已经存在: {}'.format(model))
            else:
                # save
                device_new = Device()
                for key, value in ret.items():
                    setattr(device_new, key, value)
                session.add(device_new)
                session.commit()
                count += 1
                print('保存成功: {}, 一共: {}'.format(device_new, count))
            time.sleep(0.2)
        except Exception as e:
            print(traceback.format_exc())
            print(ret)
            break


def main():
    try:
        print('--------------------------------')
        print('|         Ip地址: {}   |'.format(get_host_ip()))
        print('''

            第一次运行的模拟器上需要的操作步骤:
            1.打开修改hosts的app。
            2.增加或者修改一对：
                IP Address: 上面的Ip地址
                Hostname: api.008shenqi.com
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
