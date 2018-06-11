import os
import random

import requests

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


def get_balance(username, password, _imei=None, _model=None):
    imei = _imei or get_random_Imei()
    # model = "ONEPLUS+A3010"
    model = _model or imei

    username_sec = username[:3] + '****' + username[7:]
    session = requests.Session()
    # login
    url_login = 'https://usrsys.inner.bbk.com/v2/login'

    data = {
        "account": username,
        "pwd": password,
        "verCode": 2,
        "from": "com.vivo.game_game",
        "imei": imei,
        "cs": "0",
        "locale": "zh_CN",
        "model": model,
    }

    r = session.post(url_login, data=data, verify=False)
    account_info = r.json()
    # get cookies
    url = 'https://hf.gamecenter.vivo.com.cn/my/vjewel'
    params = {
        "appVersionName": "2.4.1",
        "elapsedtime": "294228230",
        "origin": "802",
        "adrVerName": "7.1.1",
        "apppkgName": "com.vivo.game",
        "pixel": "3.0",
        "cs": "0",
        "av": "25",
        "u": '',
        "sysAccount": "0",
        "appVersion": 161,
        "imei": imei,
        "nt": "WIFI",
        "picType": "webp",
        "model": model,
        "s": "2|3563994049"
    }
    request_cookies = {
        'vvc_imei': imei,
        'vvc_point_channel': 'gamecenter',
        'vvc_p': username_sec,
        'vvc_openid': account_info['openid'],
        'vvc_an': '7.1.1',
        'vvc_elapsedtime': '313393542',
        'vvc_av': '25',
        'vvc_app_version': '161',
        'vvc_status': '1',
        'vvc_s': '2%7C556824101',
        'vvc_q': username_sec,
        'vvc_model': 'ONEPLUS+A3010',
        'vvc_cs': '0',
        'vvc_r': account_info['authtoken'],
        'vvc_u': '',
        # 'vvc_k':'690dc10d0d887532d53e31a43f9b549a',
        'vvc_pn': 'com.vivo.game',
        'vvc_has': '0'
    }
    session.cookies.update(request_cookies)
    ret = session.get(url, params=params)
    cookies = session.cookies.get_dict()
    sign = cookies.get('vvs_vivos_sign')
    # balance
    url_balance = "https://pay.vivo.com.cn/vcoin/game/blance"
    data = {
        "appVersion": "161",
        "elapsedtime": "294228234",
        "imei": imei,
        "logged": "true",
        "model": model,
        "openid": account_info.get('openid'),
        "sign": sign,
        "token": account_info.get('authtoken'),
        "username": username_sec,
        "uuid": username_sec,
        "cs": "0",
        "av": "25",
        "version": "1.0.0",
    }
    headers = {
        'Host': 'pay.vivo.com.cn',
        'Origin': 'https://hf.gamecenter.vivo.com.cn',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.1; ONEPLUS A3010 Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
        'Referer': ret.url,
    }
    r = session.post(url_balance, data=data, headers=headers, verify=False)
    print(r.text)
    return r.json()


if __name__ == '__main__':
    get_balance('14791757268', 'ss834714')
    # print(get_random_Imei())
