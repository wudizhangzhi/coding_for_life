# -*- coding: cp936 -*-

from sys import argv
from os.path import dirname, join
from ctypes import *

# 下载接口放目录 http://www.yundama.com/apidoc/YDM_SDK.html
# 错误代码请查询 http://www.yundama.com/apidoc/YDM_ErrorCode.html
# 所有函数请查询 http://www.yundama.com/apidoc




# 1. http://www.yundama.com/index/reg/developer 注册开发者账号
# 2. http://www.yundama.com/developer/myapp 添加新软件
# 3. 使用添加的软件ID和密钥进行开发，享受丰厚分成
import requests

appId = 1  # 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
appKey = '22cc5376925e9387a23cf797cb9ba745'  # 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！


# print('软件ＩＤ：%d\r\n软件密钥：%s' % (appId, appKey))

########################## 普通识别函数 YDM_DecodeByPath #########################
def recognize_common(filename, username, password):
    print('\r\n>>>正在登陆...')
    lib_path = join(dirname(argv[0]), 'yundamaAPI-x64')
    YDMApi = windll.LoadLibrary(lib_path)
    # 第一步：初始化云打码，只需调用一次即可
    YDMApi.YDM_SetAppInfo(appId, appKey)

    # 第二步：登陆云打码账号，只需调用一次即可
    uid = YDMApi.YDM_Login(username, password)

    if uid > 0:

        print('>>>正在获取余额...')

        # 查询账号余额，按需要调用
        balance = YDMApi.YDM_GetBalance(username, password)

        print('登陆成功，用户名：%s，剩余题分：%d' % (username, balance))

        print('\r\n>>>正在普通识别...')

        # 第三步：开始识别

        # 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
        codetype = 1000

        # 分配30个字节存放识别结果
        result = c_char_p("                              ")

        timeout = 60  # 识别超时时间 单位：秒
        YDMApi.YDM_SetTimeOut(timeout)

        # 普通识别函数，需先调用 YDM_SetAppInfo 和 YDM_Login 初始化
        captchaId = YDMApi.YDM_DecodeByPath(filename, codetype, result)
        print('captchaId', captchaId, type(captchaId))
        if captchaId < 0:
            return '', ''
        # print("普通识别：验证码ID：%d，识别结果：%s" % (captchaId, result))
        return str(result)[10: -2], balance
    else:
        print('登陆失败，错误代码：%d' % uid)
        return False, False


def recognize_by_byte(filename, username, password):
    lib_path = join(dirname(argv[0]), 'yundamaAPI-x64')
    YDMApi = windll.LoadLibrary(lib_path)
    # 分配30个字节存放识别结果
    result = c_char_p("                              ")
    codetype = 1000
    timeout = 60
    lpBuffer = ''
    nNumberOfBytesToRead = ''
    captchaId = YDMApi.YDM_EasyDecodeByBytes(username, password, appId, appKey, filename, codetype, timeout, result)
    print("一键识别：验证码ID：%d，识别结果：%s" % (captchaId, result))
    if captchaId < 0:
        return '', ''
    return str(result)[10: -2], None


################################################################################
# import httplib, mimetypes, urlparse, json, time
import time

class YDMHttp:
    # apiurl = 'http://api.yundama.com/api.php'
    apiurl = 'http://api.yundama.net:5678/api.php'

    username = ''
    password = ''
    appid = ''
    appkey = ''

    def __init__(self, username, password, appid, appkey):
        self.username = username
        self.password = password
        self.appid = str(appid)
        self.appkey = appkey

    def request(self, fields, files=[]):
        try:
            # response = post_url(self.apiurl, fields, files)
            # print('response', response)
            # response = json.loads(response)
            if files:
                f = open(files['file'], 'rb')
                files['file'] = f
            # _files = files if files else None
            response = requests.post(self.apiurl, data=fields, files=files if files else None, timeout=10)
            response = response.json()
        except Exception as e:
            print(e)
            response = None
        return response

    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['balance']
        else:
            return -9001

    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['uid']
        else:
            return -9001

    def upload(self, filename, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        file = {'file': filename}
        response = self.request(data, file)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    def result(self, cid):
        data = {'method': 'result', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'cid': str(cid)}
        response = self.request(data)
        return response and response['text'] or ''

    def decode(self, filename, codetype, timeout):
        cid = self.upload(filename, codetype, timeout)
        if (cid > 0):
            for i in range(0, timeout):
                result = self.result(cid)
                if (result != ''):
                    return cid, result
                else:
                    time.sleep(1)
            return -3003, ''
        else:
            return cid, ''


######################################################################
# 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
appid = 1

# 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！
appkey = '22cc5376925e9387a23cf797cb9ba745'


# 初始化
# username = ''
# password = ''

# print 'uid: %s' % uid


def recognize_by_http(filename, username, password):
    yundama = YDMHttp(username, password, appid, appkey)
    # 登陆云打码
    uid = yundama.login()
    # 查询余额
    balance = yundama.balance()
    print('balance: %s' % balance)
    # 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
    codetype = 1000
    timeout = 60
    # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
    cid, result = yundama.decode(filename, codetype, timeout)
    print('cid: %s, result: %s' % (cid, result))
    return result, balance


if __name__ == '__main__':
    from base import cf
    print(recognize_by_http('tmp/captcha_bd@sjyx8.cn.png', cf.get('captcha', 'username'), cf.get('captcha', 'password')))
