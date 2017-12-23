# coding=utf8
import sys

sys.path.append("..")
import os
from Queue import Queue
from lxml import etree

import requests
from lxml import etree
import json
from user_agent import generate_user_agent
from base.base import *
from base.yundama import recognize_by_http

RULE = {
    # 'startlogin': {'type': BY_CLASS, 'name': ''},
    'username': {'type': BY_ID, 'name': 'ctl00_MainContent_txtCardNo'},
    'password': {'type': BY_ID, 'name': 'ctl00_MainContent_txtUCardPassword'},
    'captcha_img': {'type': BY_ID, 'name': 'ctl00_MainContent_imgExtCode'},
    'captcha': {'type': BY_ID, 'name': 'ctl00_MainContent_txtCardNoExtCode'},
    'submit': {'type': BY_ID, 'name': 'ctl00_MainContent_btnSearch'},
    'show_success': {'type': BY_ID, 'name': 'ctl00_MainContent_divUCardSearchResult'},
    # 'show_error': {'type': BY_CLASS, 'name': 'quc-tip-error'},
    'captcha_tuple': (380.0, 515.0, 69, 24),  # x, y, w, h
}


def test():
    url = 'http://www.jcard.cn/Bill/TradeSearch.aspx'
    headers = {
        'User-Agent': generate_user_agent(os=('mac', 'linux')),
        'Host': 'www.jcard.cn',
        'Origin': 'http://www.jcard.cn',
    }
    data = {
        '__VIEWSTATE': '',
        '__VIEWSTATEGENERATOR': '',
        'ctl00$MainContent$txtCardNo': '1704280393550020',
        'ctl00$MainContent$txtUCardPassword': '5171101380166090',
        'ctl00$MainContent$txtCardNoExtCode:': '',
        'ctl00$Header$txtSearchKey:': '',
        'ctl00$MainContent$btnSearch:': '',
    }
    sess = requests.Session()
    sess.headers = headers
    r = sess.get(url, timeout=10)

    root = etree.HTML(r.text)
    inputs_hidden = root.xpath('//input[@type="hidden"]')
    for hidden in inputs_hidden:
        # print(hidden.attrib.get('name'), hidden.attrib.get('value'))
        data[hidden.attrib.get('name')] = hidden.attrib.get('value')

    print(json.dumps(data, indent=4))
    r = sess.post(url, data=data, timeout=10)
    # print(r.text)
    root = etree.HTML(r.text)
    success = root.xpath('//div[@id="ctl00_MainContent_panUCardTrade"]')
    if not success:
        print(r.text)


class MaxIPException(Exception): pass


class Jcard(BasePhantomjs):
    def __init__(self):
        super(Jcard, self).__init__()
        self.separator = self.cf.get('main', 'separator')
        self.url_login = 'http://www.jcard.cn/Bill/TradeSearch.aspx'
        self.rule = RULE
        self.use_proxy = True

    def read_preset_data(self):
        '''
        读取预设的账号密码等数据
        '''
        debug(encode_info(u'开始读取账号列表: %r' % self.inputputfilename))
        if not os.path.exists(self.inputputfilename):
            raise Exception(encode_info(u'文件不存在'))
        lines = bom_read(self.inputputfilename)
        last_username_password = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.separator in line:  # 账号密码
                last_username_password = line
                self.upq.put(last_username_password)
            else:
                raise_error(encode_info(u'账号密码书写格式错误: %r' % line))

        logging.debug(self.preset_data)

    def get_search_result(self, html):
        root = etree.HTML(html)
        status = root.xpath('//span[@id="ctl00_MainContent_lblStatus"]/text()')
        times = root.xpath('//span[@id="ctl00_MainContent_Label2"]/text()')
        parvalue = root.xpath('//span[@id="ctl00_MainContent_lblTotalJPoint"]/text()')
        lock = root.xpath('//span[@id="ctl00_MainContent_lblLockJPoint"]/text()')
        useable = root.xpath('//span[@id="ctl00_MainContent_lblRemainJPoint"]/text()')

        status = status[0] if status else ''
        times = times[0] if times else ''
        parvalue = parvalue[0] if parvalue else ''
        lock = lock[0] if lock else ''
        useable = useable[0] if useable else ''
        return status, times, parvalue, lock, useable

    def _fetch_proxy(self):
        '''
        获取代理ip
        :return: str: ip:port
        '''
        r = requests.get(self.cf.get('proxy', 'url'), timeout=10)
        j = r.json()
        if not j['code'] == 0:
            debug(r.text)
            return None
        else:
            ip_port = ':'.join((j['data'][0]['ip'], str(j['data'][0]['port'])))
            expire_time = j['data'][0].get('expire_time',
                                           (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime(
                                               '%Y-%m-%d %H:%M:%S'))
            return ip_port, expire_time

    def run(self):
        self.read_preset_data()

        while not self.upq.empty():
            username_password = self.upq.get_nowait()
            is_success = False
            try:
                tmp = username_password.split(self.separator)
                username = tmp[0]
                password = tmp[1]
                driver = self.login(username, password)
                if driver:
                    html = driver.page_source
                    if u'alert' in html:
                        root = etree.HTML(html)
                        print(root.xpath('//script[@language="javascript"]/text()'))
                        if u'您的查询次数太频繁' in html:
                            print(u'您的查询次数太频繁')
                        raise MaxIPException()
                    try:
                        driver.quit()
                    except:
                        pass
                    debug(encode_info(u'开始获取结果: {}'.format(username)))
                    result = self.get_search_result(html)
                    line = u'----'.join((username_password,) + result)
                    debug(encode_info(line))
                    self.write_oneline(line)

                    is_success = True
                else:
                    debug(encode_info(u'登录失败: {}'.format(username)))
            except MaxIPException:
                # TODO 更换ip，重试
                # 增加ip计数
                self.error_proxy[self.proxy] += 1
            except Exception as e:
                debug(encode_info(str(e)))

            if not is_success:
                debug(encode_info(u'获取失败: {}'.format(username_password)))
                self.rasie_error_count(username_password, self.upq)
            debug(encode_info(u'---'*20))

        debug(encode_info(u'{:=^20}'.format(u'结束')))

if __name__ == '__main__':
    j = Jcard()
    j.run()
