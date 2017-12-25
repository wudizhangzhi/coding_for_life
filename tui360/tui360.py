# coding=utf8
import sys
sys.path.append("..")
import os
from lxml import etree

import requests
from base.base import *
from base.yundama import recognize_by_http
# from user_agent import generate_user_agent


RULE = {
    # 'startlogin': {'type': BY_CLASS, 'name': ''},
    'username': {'type': '', 'name': 'account'},
    'password': {'type': '', 'name': 'password'},
    'captcha_img': {'type': BY_CLASS, 'name': 'quc-captcha-img'},
    'captcha': {'type': BY_CLASS, 'name': 'quc-input-captcha'},
    'submit': {'type': BY_CLASS, 'name': 'quc-submit'},
    # 'show_success': {'type': '', 'name': ''},
    'show_error': {'type': BY_CLASS, 'name': 'quc-tip-error'},
    'captcha_tuple': (1026.0, 288.0, 88, 88),  # x, y, w, h
}


class Tui360(BasePhantomjs):
    def __init__(self):
        super(Tui360, self).__init__()
        self.rule = RULE
        self.url_login = 'http://tui.360.cn/'
        # self.url_search = 'http://tui.360.cn/usercheck'
        self.url_search = 'http://tui.360.cn/usercheck/search'

    def search(self, cookies, iptChannel, iptUser):
        '''
        搜索账号是否
        :param username: 账号
        :param password: 密码
        :param iptChannel: 渠道号
        :param iptUser: 用户名/邮箱/手机
        :return: tuple: (qid, 注册时间, 是否绑定渠道, 绑定渠道号, 绑定游戏)
        '''
        debug(encode_info(u'开始查询: {channel} {user}'.format(channel=iptChannel, user=iptUser)))
        sess = requests.Session()
        sess.cookies.update(dict([(i['name'], i['value']) for i in cookies]))
        sess.headers = {
            # 'User-Agent': generate_user_agent(os=('linux', 'mac')),
            'User-Agent': choice(AGENTS_ALL),
            'Host': 'tui.360.cn',
            'Referer': 'http://tui.360.cn/usercheck/search',
        }
        # 获取余额
        data = {
            'data[channel]': iptChannel,
            'data[user]': iptUser,
        }
        res = sess.post(self.url_search, data=data, timeout=10)
        res.encoding = 'utf8'
        root = etree.HTML(res.text)
        tds = root.xpath('//tbody[@id="orderList"]/tr/td')
        assert len(tds) == 5, u'表格结果数量不一致'
        return (td.text for td in tds)

    def search_by_account(self, username_password):
        queue = self.preset_data.get(username_password, None)
        if queue.empty():
            debug(encode_info(u'{up} 没有预设渠道号'.format(up=username_password)))
            return False
        tmp = username_password.split(':')
        username = tmp[0].strip()
        password = tmp[1].strip()
        driver = self.login(username, password)
        if driver:
            # 登录成功后用cookie获取数据
            debug(encode_info(u'登录成功: {}'.format(username)))
            cookies = driver.get_cookies()
            driver.quit()
            # TODO 取一组数据, 是否多线程, 写入同一个文件，多线程有问题
            while not queue.empty():
                iptchannel_iptuser = queue.get_nowait()
                try:
                    tmp = iptchannel_iptuser.split('----')
                    iptchannel = tmp[0]
                    iptuser = tmp[1]
                    result = self.search(cookies, iptchannel, iptuser)
                    result = list(result)
                    debug(encode_info(u'{} {} {} {} {} \n'.format(*result)))
                    line = u'{cu} QID: {} 注册时间: {}  是否已绑定到渠道:{} 绑定渠道号:{} 绑定游戏:{}'.format(cu=iptchannel_iptuser, *result)
                    self.write_oneline(line)
                except Exception as e:
                    debug(encode_info(str(e)))
                    self.raise_error_count(iptchannel_iptuser, queue=queue)
            return True
        else:
            return False

    def run(self):
        # 读取预设
        self.read_preset_data()
        while not self.upq.empty():
            username_password = self.upq.get_nowait()
            self.write_oneline(username_password)
            search_success = True
            try:
                # 搜索某一个账号密码下的数据
                search_success = self.search_by_account(username_password)
            except CaptchaException as e:
                self.raise_error_count(username_password, reset=True)
            except Exception as e:
                debug(encode_info(str(e)))
                search_success = False

            if not search_success:
                self.raise_error_count(username_password, self.upq)

        debug(encode_info(u'{:=^20}'.format(u'结束')))


if __name__ == '__main__':
    t = Tui360()
    # t.test()
    t.run()
