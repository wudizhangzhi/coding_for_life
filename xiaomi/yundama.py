# -*- coding: cp936 -*-

from sys import argv
from os.path import dirname, join
from ctypes import *

# ���ؽӿڷ�Ŀ¼ http://www.yundama.com/apidoc/YDM_SDK.html
# ����������ѯ http://www.yundama.com/apidoc/YDM_ErrorCode.html
# ���к������ѯ http://www.yundama.com/apidoc




# 1. http://www.yundama.com/index/reg/developer ע�Ὺ�����˺�
# 2. http://www.yundama.com/developer/myapp ��������
# 3. ʹ����ӵ����ID����Կ���п��������ܷ��ֳ�
import requests

appId = 1  # ����ɣģ������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�
appKey = '22cc5376925e9387a23cf797cb9ba745'  # �����Կ�������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�


# print('����ɣģ�%d\r\n�����Կ��%s' % (appId, appKey))

########################## ��ͨʶ���� YDM_DecodeByPath #########################
def recognize_common(filename, username, password):
    print('\r\n>>>���ڵ�½...')
    lib_path = join(dirname(argv[0]), 'yundamaAPI-x64')
    YDMApi = windll.LoadLibrary(lib_path)
    # ��һ������ʼ���ƴ��룬ֻ�����һ�μ���
    YDMApi.YDM_SetAppInfo(appId, appKey)

    # �ڶ�������½�ƴ����˺ţ�ֻ�����һ�μ���
    uid = YDMApi.YDM_Login(username, password)

    if uid > 0:

        print('>>>���ڻ�ȡ���...')

        # ��ѯ�˺�������Ҫ����
        balance = YDMApi.YDM_GetBalance(username, password)

        print('��½�ɹ����û�����%s��ʣ����֣�%d' % (username, balance))

        print('\r\n>>>������ͨʶ��...')

        # ����������ʼʶ��

        # ����1004��ʾ4λ��ĸ���֣���ͬ�����շѲ�ͬ����׼ȷ��д������Ӱ��ʶ���ʡ��ڴ˲�ѯ�������� http://www.yundama.com/price.html
        codetype = 1000

        # ����30���ֽڴ��ʶ����
        result = c_char_p("                              ")

        timeout = 60  # ʶ��ʱʱ�� ��λ����
        YDMApi.YDM_SetTimeOut(timeout)

        # ��ͨʶ���������ȵ��� YDM_SetAppInfo �� YDM_Login ��ʼ��
        captchaId = YDMApi.YDM_DecodeByPath(filename, codetype, result)
        print('captchaId', captchaId, type(captchaId))
        if captchaId < 0:
            return '', ''
        # print("��ͨʶ����֤��ID��%d��ʶ������%s" % (captchaId, result))
        return str(result)[10: -2], balance
    else:
        print('��½ʧ�ܣ�������룺%d' % uid)
        return False, False


def recognize_by_byte(filename, username, password):
    lib_path = join(dirname(argv[0]), 'yundamaAPI-x64')
    YDMApi = windll.LoadLibrary(lib_path)
    # ����30���ֽڴ��ʶ����
    result = c_char_p("                              ")
    codetype = 1000
    timeout = 60
    lpBuffer = ''
    nNumberOfBytesToRead = ''
    captchaId = YDMApi.YDM_EasyDecodeByBytes(username, password, appId, appKey, filename, codetype, timeout, result)
    print("һ��ʶ����֤��ID��%d��ʶ������%s" % (captchaId, result))
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
# ����ɣģ������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�
appid = 1

# �����Կ�������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�
appkey = '22cc5376925e9387a23cf797cb9ba745'


# ��ʼ��
# username = ''
# password = ''

# print 'uid: %s' % uid


def recognize_by_http(filename, username, password):
    yundama = YDMHttp(username, password, appid, appkey)
    # ��½�ƴ���
    uid = yundama.login()
    # ��ѯ���
    balance = yundama.balance()
    print('balance: %s' % balance)
    # ����1004��ʾ4λ��ĸ���֣���ͬ�����շѲ�ͬ����׼ȷ��д������Ӱ��ʶ���ʡ��ڴ˲�ѯ�������� http://www.yundama.com/price.html
    codetype = 1000
    timeout = 60
    # ��ʼʶ��ͼƬ·������֤������ID����ʱʱ�䣨�룩��ʶ����
    cid, result = yundama.decode(filename, codetype, timeout)
    print('cid: %s, result: %s' % (cid, result))
    return result, balance


if __name__ == '__main__':
    from base import cf
    print(recognize_by_http('tmp/captcha_bd@sjyx8.cn.png', cf.get('captcha', 'username'), cf.get('captcha', 'password')))
