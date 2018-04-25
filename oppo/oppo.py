#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/22 下午7:36
# @Author  : wudizhangzhi
import datetime
import json
import random

import requests
from hashlib import md5
import os

TAC_LIST = ['35651900', '35666503', '91054200',
            '35537803', '44831527', '86489400',
            '35084240', '13004008', '35103090',
            '35332802']


def luhn_residue(digits):
    return sum(sum(divmod(int(d) * (1 + i % 2), 10))
               for i, d in enumerate(digits[::-1])) % 10


def get_random_Imei(N=None, filename=None):
    if not N:
        N = 15
    return getImei(N, get_random_tac(filename))


def getImei(N, tac=None):
    '''
    IMEI就是移动设备国际身份码，我们知道正常的手机串码IMEI码是15位数字，
    由TAC（6位，型号核准号码）、FAC（2位，最后装配号）、SNR（6位，厂商自行分配的串号）和SP（1位，校验位）。
    tac数据库: https://www.kaggle.com/sedthh/typeallocationtable/data
    :param N:
    :return:
    '''
    part = ''.join(str(random.randrange(0, 9)) for _ in range(N - 1))
    if tac:
        part = tac + part[len(tac):]
    res = luhn_residue('{}{}'.format(part, 0))
    return '{}{}'.format(part, -res % 10)


def get_random_tac(filename=None):
    if not filename:
        filename = 'tac.csv'
    if not os.path.exists(filename):
        return random.choice(TAC_LIST)
    with open(filename, 'r') as f:
        lines = f.readlines()
        line = random.choice(lines)
        return line.split(',')[0]


def get_android_id():
    # 固定 adb shell settings get secure android_id 随机64位数字的16进制
    result = ''
    for _ in range(64):
        result += random.choice(['0', '1'])
    return hex(int(result, base=2))[2:]


class Oppo(object):
    def __init__(self):
        self.session = requests.session()

    def login(self, username, password):
        encoding = 'UTF-8'
        passWord_md5 = md5(password.encode(encoding)).hexdigest()
        appKey = 'usercenter'
        appSecret = '9effeac61b7ad92a9bef3da596f2158b'
        isVerifyCode = "2"
        imei = '008796748083554'
        sign = signMD5(appKey + username + passWord_md5, appSecret, encoding)
        user_agent = 'Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; MuMu Build/V417IR) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
        ext_system = 'MUMU/4.4.4/0/2/3012/3.3.0/1'
        # # TODO checkinnerupgrade
        # url_check = 'http://i2.store.nearme.com.cn/MobileAPI/CheckInnerUpgrade.ashx'
        # data = '<request version="1"><product_code>3012</product_code><version_code>330</version_code><screen_size>1280#720</screen_size><platform>19</platform><system_type>0</system_type><rom_version>4.4.4</rom_version><model>MuMu</model><brand>Android</brand><rom_type>2</rom_type><language>zhCN</language><checkMd5>e122d99ddac44b3f24d27720f4700d3e</checkMd5><upgrade_module_vers>200</upgrade_module_vers></request>'
        # headers = {
        #     'Ext-System': 'MUMU/4.4.4/0/2/3012/3.3.0/1',
        #     'Ext-User': '-1/{}/0'.format(imei),
        #     'User-Agent': 'MuMu',
        #     'Content-Type': 'text/plain; charset=ISO-8859-1',
        #     'Host': 'i2.store.nearme.com.cn'
        # }
        # ret = session.post(url_check, data=data, headers=headers)
        # print(ret.text)
        #
        # # http://cm.poll.keke.cn
        # url = 'http://cm.poll.keke.cn'
        # data = b'\n\x1b\x08\x01\x10g\x1a\x13com.oppo.usercenter \x10\x126\n\x0f' + imei.encode('utf8') + b'\x12\x04MuMu\x18\x00"\x13' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode('utf8') + b':\x04WIFIX\x03'
        # ret = session.post(url, data=data)
        # print(ret.content)

        # login
        data = {
            "appKey": appKey,
            "isVerifyCode": isVerifyCode,
            "loginName": username,
            "passWord": passWord_md5,
            'sign': sign,
            "verifyCode": "",
        }
        url = 'http://i.auth.nearme.com.cn/loging'
        headers = {
            'Ext-USER': imei,
            'Ext-App': '{}/330/com.oppo.usercenter'.format(appSecret),
            'Ext-System': 'MuMu/4.4.4/2/Netease/4.4.4/0/330/',
            'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.4; MuMu Build/V417IR)',
            'Host': 'i.auth.nearme.com.cn',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept-Encoding': '',
            'Connection': 'Keep-Alive',
        }
        ret = self.session.post(url, data=json.dumps(data), headers=headers)
        print(ret.text)
        ret_j = ret.json()
        token = ret_j['token']
        return token

    def pay(self, token, cardname, cardpwd, amount):
        """
        支付
        :param token: 
        :param cardname: 卡号
        :param cardpwd: 密码
        :param amount: 金额
        :return: 
        """
        # ticket
        url_ticket = 'https://ticket.keke.cn/tksv/post/pass'
        data = b':GR0\nF' + token.encode('utf8') + b'\x12\x042031\x1a\x13com.oppo.usercenter"\x03ext*\x032.0H2'
        print(data)
        headers = {
            'Host': 'ticket.keke.cn',
            'Accept-Encoding': 'gzip',
        }
        ret = self.session.post(url_ticket, verify=False, data=data, headers=headers)
        print(ret.content)


def signMD5(avalue, akey, encoding=None):
    if not encoding:
        encoding = 'UTF-8'
    k_ipad = bytearray()
    k_opad = bytearray()

    keyb = akey.encode(encoding)
    value = avalue.encode(encoding)
    keyb_length = len(keyb)
    for i in keyb:
        k_ipad.append(i ^ 54)
        k_opad.append(i ^ 92)
    k_ipad.extend([54] * keyb_length)
    k_opad.extend([92] * keyb_length)
    m = md5()
    m.update(k_ipad)
    m.update(value)
    dg = m.digest()
    m = md5()
    m.update(k_opad)
    for i in range(16):
        m.update(bytes([dg[i]]))
    return m.hexdigest()


def toHex(input):
    if not input:
        return None
    bi = bytearray(input)
    output = ''
    for b in bi:
        current = b & 0X000000ff
        if current < 16:
            output += '0'
        output += int(current, base=16)
    return str(output)


if __name__ == '__main__':
    oppo = Oppo()
    token = oppo.login('17085024908', 'Qq112233')
    oppo.pay(token, '', '')
    # sign = signMD5("usercenter170850249083ce25a66d5b3a8cd661024fea6c79388", "9effeac61b7ad92a9bef3da596f2158b", "UTF-8")
    # print(sign)
    # print(sign == '91905ac6c4af8e68064537da201029aa')
