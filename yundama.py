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
import httplib, mimetypes, urlparse, json, time


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
            response = post_url(self.apiurl, fields, files)
            response = json.loads(response)
        except Exception as e:
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

def post_url(url, fields, files=[]):
    urlparts = urlparse.urlsplit(url)
    return post_multipart(urlparts[1], urlparts[2], fields, files)


def post_multipart(host, selector, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('Host', host)
    h.putheader('Content-Type', content_type)
    h.putheader('Content-Length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()


def encode_multipart_formdata(fields, files=[]):
    BOUNDARY = 'WebKitFormBoundaryJKrptX8yPbuAJLBQ'
    CRLF = '\r\n'
    L = []
    for field in fields:
        key = field
        value = fields[key]
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for field in files:
        key = field
        filepath = files[key]
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filepath))
        L.append('Content-Type: %s' % get_content_type(filepath))
        L.append('')
        L.append(open(filepath, 'rb').read())
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


######################################################################
# ����ɣģ������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�
appid = 1

# �����Կ�������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�
appkey = '22cc5376925e9387a23cf797cb9ba745'
# ��ʼ��
username = ''
password = ''
yundama = YDMHttp(username, password, appid, appkey)
# ��½�ƴ���
uid = yundama.login()
print 'uid: %s' % uid


def recognize_by_http(filename, username, password):
    # ��ѯ���
    balance = yundama.balance()
    print 'balance: %s' % balance
    # ����1004��ʾ4λ��ĸ���֣���ͬ�����շѲ�ͬ����׼ȷ��д������Ӱ��ʶ���ʡ��ڴ˲�ѯ�������� http://www.yundama.com/price.html
    codetype = 1000
    timeout = 60
    # ��ʼʶ��ͼƬ·������֤������ID����ʱʱ�䣨�룩��ʶ����
    cid, result = yundama.decode(filename, codetype, timeout)
    print 'cid: %s, result: %s' % (cid, result)
    return result, balance


if __name__ == '__main__':
    print(recognize_by_http('tmp_captcha_gzyz0002.png', '', ''))
