#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/22 下午7:36
# @Author  : wudizhangzhi
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


def login(username, password):
    encoding = 'UTF-8'
    passWord_md5 = md5(password.encode(encoding)).hexdigest()
    appKey = 'usercenter'
    appSecret = '9effeac61b7ad92a9bef3da596f2158b'
    isVerifyCode = 2
    sign = signMD5(appKey + username + passWord_md5, appSecret, encoding)
    data = {"appKey": appKey,
            "isVerifyCode": isVerifyCode,
            "loginName": username,
            "passWord": passWord_md5,
            "verifyCode": "",
            'sign': sign}
    print(data)
    session = requests.session()
    url = 'http://i.auth.nearme.com.cn/loging'
    headers = {
        'Ext-USER': '008796748083554',
        'Ext-App': '{}/330/com.oppo.usercenter'.format(appSecret),
        'Ext-System': 'MuMu/4.4.4/2/Netease/4.4.4/0/330/',
        'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.4; MuMu Build/V417IR)',
        'Host': 'i.auth.nearme.com.cn',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Encoding': '',
    }
    print(headers)
    ret = session.post(url, data=data, headers=headers)
    print(ret.text)


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
    login('17085024908', 'Qq112233')
    # sign = signMD5("usercenter170850249083ce25a66d5b3a8cd661024fea6c79388", "9effeac61b7ad92a9bef3da596f2158b", "UTF-8")
    # print(sign)
    # print(sign == '91905ac6c4af8e68064537da201029aa')
