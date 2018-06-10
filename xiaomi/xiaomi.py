#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 下午8:28
# @Author  : wudizhangzhi
import datetime
import json
import logging
import os
import shutil

import requests
from PIL import Image
# from user_agent import generate_user_agent
import re
import time
from hashlib import md5
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    'startlogin': {'type': 'path', 'name': '//*[@id="main_nav"]/div/nav[2]/a[1]'},
    # 'login_frame': {'type': 'id', 'name': 'login_frame'},
    # 'switch_plogin': {'type': 'id', 'name': 'switcher_plogin'},
    'username': {'type': 'id', 'name': 'username'},
    'password': {'type': 'id', 'name': 'pwd'},

    'submit': {'type': 'id', 'name': 'login-button'},
    # 'show_success': {'type': 'id', 'name': 'loginNickName'},
    # 'show_error': {'type': 'id', 'name': 'error_tips'},
    #### 验证码部分 ####
    # 'captcha_tuple': (380.0, 515.0, 69, 24),  # x, y, w, h
    'captcha_img': {'type': 'id', 'name': 'captcha-img'},
    'captcha': {'type': 'id', 'name': 'captcha-code'},
    # 短信验证码
    'sms': {'type': 'id', 'name': 'verify-mod-send_ticket_tip'},
    'sms_code': {'type': 'path', 'name': '//*[@id="verify-mod-SMS"]/div[1]/div[1]/label/input'},
    'sms_code_fetch': {'type': 'path', 'name': '//*[@id="verify-mod-SMS"]/div[1]/div[1]/span/a'},
    'sms_submit': {'type': 'path', 'name': '//*[@id="verify-mod-SMS"]/div[3]/a'},
    # 'slideblock': {'type': 'id', 'name': 'slideBlock'},
    # 'slidebkg': {'type': 'id', 'name': 'slideBkg'},
    # 'tcaptcha_drag_button': {'type': 'id', 'name': 'tcaptcha_drag_button'},
    # 'tcaptcha-imgarea': {'type': 'class', 'name': 'tcaptcha-imgarea'},  # 验证码背景图的div
}


class Xiaomi(object):
    def __init__(self):
        self.session = requests.Session()
        # self.headers = {
        #     'User-Agent': generate_user_agent(os=['mac', 'linux']),
        #     'Host': 'account.xiaomi.com',
        #     'Upgrade-Insecure-Requests': '1',
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        #     'Accept-Encoding': 'gzip, deflate, br',
        #     'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        # }
        # self.session.headers = self.headers
        # selenium settings
        self.rule = RULE
        self.interval_time = 0.5
        self.proxy = None
        self.add_to_white = False
        # init folder
        if os.path.exists('qrcode'):
            shutil.rmtree('qrcode')
        os.mkdir('qrcode')

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
        # dcap["phantomjs.page.settings.userAgent"] = (generate_user_agent(os=('linux', 'mac')))
        dcap[
            "phantomjs.page.settings.userAgent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
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
        # driver.get(self.rule['url_login'])
        driver.get('https://mibi.wali.com/')

        logging.debug(u'获取登录界面')
        if 'startlogin' in self.rule:
            btn_login = driver.find_element_by_xpath(self.rule['startlogin']['name'])
            btn_login.click()
            time.sleep(self.interval_time)
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

    def need_qrcode(self, driver):
        if 'captcha_img' in self.rule:
            try:
                captcha_img = driver.find_element(self.get_by(self.rule['captcha_img']['type']),
                                                  self.rule['captcha_img']['name'])
                if captcha_img:
                    return True
            except NoSuchElementException:
                pass
        return False

    def need_sms_code(self, driver):
        if 'sms' in self.rule:
            try:
                sms = driver.find_element(self.rule['sms']['type'], self.rule['sms']['name'])
                if sms:
                    return True
            except NoSuchElementException:
                pass
        return False

    def check_qrcode(self, driver, username):
        # 如果有验证码
        captcha_img = driver.find_element_by_xpath('//*[@id="captcha-img"]')
        # 获取二维码坐标
        location = captcha_img.location
        size = captcha_img.size
        # 截取二维码
        x = int(location.get('x', 673))
        y = int(location.get('y', 483))
        w = int(size.get('width', 88))
        h = int(size.get('height', 35))
        box = (x, y, x + w, y + h)

        _screenshot_filename = 'qrcode/screen_%s.png' % username
        _captcha_filename = 'qrcode/captcha_%s.png' % username
        logging.debug(u'截图, 保存为 %r' % _screenshot_filename)
        captcha_img.screenshot(_screenshot_filename)
        screenshot = Image.open(_screenshot_filename)
        logging.debug(u'从截图中裁剪出验证码, 保存为 %r' % _captcha_filename)
        img_crop = screenshot.crop(box)
        img_crop.save(_captcha_filename)
        screenshot.close()
        img_crop.close()
        # 识别验证码
        time.sleep(self.interval_time)
        return driver

    def enter_qrcode(self, code, driver):
        captcha = driver.find_element(self.get_by(self.rule['captcha']['type']), self.rule['captcha']['name'])
        captcha.send_keys(code)
        time.sleep(0.3)
        # 登录
        input_submit = driver.find_element(self.get_by(self.rule['submit']['type']),
                                           self.rule['submit']['name'])
        input_submit.click()
        time.sleep(self.interval_time)
        return driver

    def sms_check(self, driver):
        btn_sms_code_fetch = driver.find_element_by_xpath(self.rule['sms_code_fetch']['name'])
        btn_sms_code_fetch.click()

    def enter_sms_code(self, code, driver):
        sms_code = driver.find_element_by_xpath(self.rule['sms_code']['name'])
        sms_code.send_keys(code)
        btn_sms_submit = driver.find_element_by_xpath(self.rule['sms_submit']['name'])
        btn_sms_submit.click()
        time.sleep(self.interval_time)

    def search_mibi(self, driver):
        # driver.get('https://mibi.wali.com/')
        # btn_login = driver.find_element_by_xpath('//*[@id="main_nav"]/div/nav[2]/a[1]')
        # btn_login.click()
        # time.sleep(self.interval_time)
        btn_account = driver.find_element_by_xpath('//*[@id="sub_nav"]/nav/a[3]')
        btn_account.click()
        time.sleep(self.interval_time)
        # driver.save_screenshot('output_%s.png' % int(time.time()))
        balance = driver.find_element_by_xpath('//*[@id="main_wrapper"]/div[2]/span[2]/em')
        gift = driver.find_element_by_xpath('//*[@id="main_wrapper"]/div[2]/span[3]/a')
        return balance.text, gift.text

    def _add_to_while(self, white_url, ip):
        try:
            r = requests.get(white_url + ip, timeout=10)
            if r.json()['code'] == 0:
                logging.debug('保存白名单成功: {}'.format(ip))
            else:
                logging.debug(r.text)
        except Exception as e:
            print(e)

    def _get_proxy_balance(self, balance_url):
        try:
            r = requests.get(balance_url, timeout=10)
            if r.json()['code'] == 0:
                logging.debug('账户余额: {}'.format(r.json()['data']['balance']))
            else:
                logging.debug(r.text)
        except Exception as e:
            print(e)

    def _fetch_proxy(self, ip_url, white_url, balance_url=None):
        '''
        获取代理ip
        :return: str: ip:port
        '''
        r = requests.get(ip_url.strip(), timeout=10)
        j = r.json()
        if not j['code'] == 0:
            logging.debug(r.text)
            if j['code'] == 113:
                match = re.findall(r'(\d+\.\d+\.\d+\.\d+)', j['msg'])
                if match:
                    self._add_to_while(white_url.strip(), match[0].strip())
                    if not self.add_to_white:
                        time.sleep(3)
                        return self._fetch_proxy(ip_url, white_url.strip(), balance_url)
        else:
            ip_port = ':'.join((j['data'][0]['ip'], str(j['data'][0]['port'])))
            expire_time = j['data'][0].get('expire_time',
                                           (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime(
                                               '%Y-%m-%d %H:%M:%S'))
            # self._get_proxy_balance(balance_url)
            return ip_port, expire_time


if __name__ == '__main__':
    xm = Xiaomi()
    print(xm._fetch_proxy(
        'http://webapi.http.zhimacangku.com/getip?num=1&type=2&pro=&city=0&yys=0&port=1&time=1&ts=1&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions=',
        'http://web.http.cnapi.cc/index/index/save_white?neek=33481&appkey=d212e2fefa6c9648b33f38051fcd9bd5&white=',
        'http://web.http.cnapi.cc/index/index/get_my_balance?neek=33481&appkey=d212e2fefa6c9648b33f38051fcd9bd5'))
