#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 下午8:28
# @Author  : wudizhangzhi
import json
import logging
import os

import requests
from user_agent import generate_user_agent
from lxml import etree
import re
import time
from hashlib import md5
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='log.log',
                    filemode='w')

RULE = {
    'url_login': 'https://account.xiaomi.com/pass/serviceLogin',
    # 'startlogin': {'type': 'id', 'name': 'login'},
    # 'login_frame': {'type': 'id', 'name': 'login_frame'},
    # 'switch_plogin': {'type': 'id', 'name': 'switcher_plogin'},
    'username': {'type': 'id', 'name': 'username'},
    'password': {'type': 'id', 'name': 'pwd'},

    'submit': {'type': 'id', 'name': 'login-button'},
    # 'show_success': {'type': 'id', 'name': 'loginNickName'},
    # 'show_error': {'type': 'id', 'name': 'error_tips'},
    #### 验证码部分 ####
    # 'captcha_tuple': (380.0, 515.0, 69, 24),  # x, y, w, h
    # 'captcha_img': {'type': 'id', 'name': 'ctl00_MainContent_imgExtCode'},
    # 'captcha': {'type': 'id', 'name': 'newVcodeArea'},
    # 'slideblock': {'type': 'id', 'name': 'slideBlock'},
    # 'slidebkg': {'type': 'id', 'name': 'slideBkg'},
    # 'tcaptcha_drag_button': {'type': 'id', 'name': 'tcaptcha_drag_button'},
    # 'tcaptcha-imgarea': {'type': 'class', 'name': 'tcaptcha-imgarea'},  # 验证码背景图的div
}


class Xiaomi(object):
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': generate_user_agent(os=['mac', 'linux']),
            'Host': 'account.xiaomi.com',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session.headers = self.headers
        # selenium settings
        self.rule = RULE
        self.interval_time = 1

    def _login(self, username, password):
        _sign = '2&V1_passport&wqS4omyjALxMm//3wLXcVcITjEc='
        url = 'https://account.xiaomi.com/pass/serviceLogin'
        ret = self.session.get(url, timeout=10, verify=False)
        # match = re.search(r'"_sign":"([^\"]+)"', ret.text)
        # if match:
        #     _sign = match.group()[0]
        login_url = "https://account.xiaomi.com/pass/serviceLoginAuth2"
        data = {
            '_json': 'true',
            'callback': 'https://account.xiaomi.com',
            'sid': 'passport',
            'qs': '%3Fsid%3Dpassport',
            '_sign': _sign,
            'serviceParam': '{"checkSafePhone":false}',
            'user': username,
            'hash': md5(password.encode('utf8')).hexdigest().upper(),
        }
        print(data)
        headers = {
            'Origin': 'https://account.xiaomi.com',
            'Referer': 'https://account.xiaomi.com/pass/serviceLogin',
            'Content-type': 'application/x-www-form-urlencoded',
        }
        params = {'_dc': int(time.time() * 1000)}
        ret = self.session.post(login_url, headers=headers, params=params, data=data, timeout=10)
        ret_text = ret.text
        # cookies = self.session.cookies.get_dict()
        ret_text = ret_text.replace('&&&START&&&', '')
        ret_json = json.loads(ret_text)
        userid = ret_json['userId']
        cookies = self.session.cookies.get_dict()
        print(cookies)
        print(userid)
        return userid

    def _search_balance(self, username, password):
        # userid = self.login(username, password)
        # print('userId: %s' % userid)
        # TODO
        from cookie_save import USERID, COOKIE_SAVED
        userid = USERID
        url = 'https://mibi.wali.com/record/account'
        params = {'userId': userid}
        headers = {
            'Host': 'mibi.wali.com',
            'Referer': 'https://mibi.wali.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
        }
        ret = self.session.get(url, cookies=COOKIE_SAVED, params=params, headers=headers, timeout=10)
        print(ret.text)

    def init_driver(self, proxy=None):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
        dcap["phantomjs.page.settings.userAgent"] = (generate_user_agent(os=('linux', 'mac')))
        # dcap["phantomjs.page.settings.userAgent"] = (choice(AGENTS_ALL))
        # 不载入图片，爬页面速度会快很多
        # dcap["phantomjs.page.settings.loadImages"] = False
        try:
            phantomjs_driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phantomjs.exe')
            if not os.path.exists(phantomjs_driver_path):
                phantomjs_driver_path = 'phantomjs'
        except Exception as e:
            phantomjs_driver_path = 'phantomjs'
            logging.debug(e)
        if proxy:
            logging.debug(u'使用代理IP: {}'.format(proxy))
            service_args = [
                '--proxy={proxy}'.format(proxy=proxy),
                '--proxy-type=http',
            ]
        else:
            service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=any']
        driver = webdriver.PhantomJS(
            phantomjs_driver_path,
            service_args=service_args,
            desired_capabilities=dcap,
        )

        # 隐式等待5秒，可以自己调节
        driver.implicitly_wait(5)
        return driver

    @staticmethod
    def get_by(key):
        '''
        return by type
        :param key: 
        :return: 
        '''
        if key == 'class':
            return By.CLASS_NAME
        elif key == 'id':
            return By.ID
        else:
            return By.NAME

    def login(self, username, password, proxy=None):
        logging.debug('开始登陆: {}'.format(username))
        driver = self.init_driver(proxy=proxy)

        driver.set_page_load_timeout(60)
        driver.set_window_size(1366, 942)
        driver.get(self.rule['url_login'])

        logging.debug(u'获取登录界面')
        if 'startlogin' in self.rule:
            btn_login = driver.find_element(self.get_by(self.rule['startlogin']['type']),
                                            self.rule['startlogin']['name'])
            btn_login.click()
        if 'login_frame' in self.rule:
            logging.debug(u'进入iframe')
            # 转到登录用iframe
            driver.switch_to.frame(driver.find_element(self.get_by(self.rule['login_frame']['type']),
                                                       self.rule['login_frame']['name']))
            time.sleep(self.interval_time)
        if 'switch_plogin' in self.rule:
            # 等待元素出现
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (self.get_by(self.rule['switch_plogin']['type']), self.rule['switch_plogin']['name']))
            )
            logging.debug(u'点击使用账号密码登录按钮')
            element.click()

        # TODO 是否等在元素出现
        logging.debug(u'键入用户名: %r' % username)
        input_username = driver.find_element(self.get_by(self.rule['username']['type']),
                                             self.rule['username']['name'])
        input_username.clear()
        input_username.send_keys(username)
        time.sleep(self.interval_time)

        logging.debug(u'键入密码: %r' % password)
        input_password = driver.find_element(self.get_by(self.rule['password']['type']),
                                             self.rule['password']['name'])
        input_password.click()
        input_password.clear()
        # input_password.send_keys(Keys.HOME)
        input_password.send_keys(password)
        # for k in list(password):
        #     input_password.send_keys(k)
        #     time.sleep(0.2)
        time.sleep(self.interval_time)
        logging.debug(u'点击登录')
        # 登录
        input_submit = driver.find_element(self.get_by(self.rule['submit']['type']),
                                           self.rule['submit']['name'])
        input_submit.click()

        time.sleep(self.interval_time)
        return driver

    def search_mibi(self, driver):
        driver.get('https://mibi.wali.com/')
        btn_login = driver.find_element_by_xpath('//*[@id="main_nav"]/div/nav[2]/a[1]')
        btn_login.click()
        time.sleep(self.interval_time)

        btn_account = driver.find_element_by_xpath('//*[@id="sub_nav"]/nav/a[3]')
        btn_account.click()
        time.sleep(self.interval_time)

        balance = driver.find_element_by_xpath('//*[@id="main_wrapper"]/div[2]/span[2]/em')
        gift = driver.find_element_by_xpath('//*[@id="main_wrapper"]/div[2]/span[3]/a')
        print(balance.text)
        print(gift.text)


if __name__ == '__main__':
    xm = Xiaomi()
    driver = xm.login('', '')
    xm.search_mibi(driver)
