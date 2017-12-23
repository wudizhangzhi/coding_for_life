# encoding: utf-8
import os
import re
from Queue import Queue
from threading import Thread

from lxml import etree
from random import choice

import logging

import sys

import time

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 引入配置对象DesiredCapabilities
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from read_config import cf
from agents import AGENTS_ALL

# from yundama import recognize_by_http

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='log.log',
                    filemode='w')


def debug(info):
    logging.debug(info)
    print(info)


def encode_info(content):
    try:
        if 'utf' in sys.stdout.encoding.lower():
            return content.encode('utf-8')
        else:
            return content.encode('gbk')
    except Exception as e:
        logging.error(e)
        return content.encode('utf-8')


def raise_error(e):
    try:
        logging.error(e)
    except:
        pass
    raise FuckException(e)


def bom_read(filename):
    import io
    import chardet
    import codecs
    try:
        bytes = min(32, os.path.getsize(filename))
        raw = open(filename, 'rb').read(bytes)

        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            result = chardet.detect(raw)
            encoding = result['encoding']
        with io.open(filename, 'r', encoding=encoding) as infile:
            data = infile.readlines()
    except:
        with open(filename, 'r') as f:
            data = f.readlines()
    return data


class FuckException(Exception):
    pass


class LoginErrorException(Exception):
    pass


############################
def recognize_captcha_by_yourself(captcha_filename=None):
    debug(encode_info(u'开始人工识别验证码'))
    img = Image.open(captcha_filename)
    img.show()
    chaptcha_code = raw_input(encode_info(u'请输入验证码: '))
    if not chaptcha_code:
        raise_error(encode_info(u'请输入正确的验证码!'))
    return chaptcha_code


class ChangePayPass(object):
    def __init__(self):
        self.separator = '----'
        self.interval_time = 2
        self.captcha_mode = 2
        self.captcha_username = cf.get('captcha', 'username')
        self.captcha_password = cf.get('captcha', 'password')
        self.tmp_path = 'tmp'
        if not os.path.exists(self.tmp_path):
            os.mkdir(self.tmp_path)
        self.screenshot_filename = 'tmp/tmp_screenshot_%s.png'
        self.captcha_filename = 'tmp/tmp_captcha_%s.png'
        self.empty_data_list = []  # 没有数据的账号列表
        self.failure_list = []  # 超过最大错误计数失败的账号列表
        self.error_dict = {}  # 错误计数
        self.max_error_count = 3

        self.queue = Queue()
        self.change_pay_password_result = {}
        self.favourate_star = u'张杰'  # 支付密码修改问题

        self.balance_list = []  # 用于保存余额列表
        self.DEBUG = True
        self.THREAD_NUM = 4  # 线程数量  #
        self.threading_pool = []

    def settings(self):
        captcha_mode = raw_input(encode_info(u'请输入识别验证码的模式(0:超人打码 ;1:人工识别; 2:云打码 默认2): ')) or 2
        self.captcha_mode = int(captcha_mode)
        if self.captcha_mode in [0, 2]:
            DEFAULT = {0: {'username': '',
                           'password': ''},
                       2: {'username': cf.get('captcha', 'username'),
                           'password': cf.get('captcha', 'password'),
                           }
                       }
            try:
                default_username = DEFAULT[self.captcha_mode]['username']
                default_password = DEFAULT[self.captcha_mode]['password']
            except:
                default_username = ''
                default_password = ''
            self.captcha_username = raw_input(encode_info(u'请输入打码的账号(默认: %r):' % default_username)) or default_username
            self.captcha_password = raw_input(encode_info(u'请输入打码的密码:')) or default_password
            if not (self.captcha_username and self.captcha_password):
                raise FuckException(encode_info(u'请输入用户名密码!!'))

        interval_time = raw_input(encode_info(u'请输入间隔时间(默认2s): ')) or 2
        self.interval_time = int(interval_time)
        WELCOME = u'''
                            导入账号列表的文件格式:
                                账号1{separator}密码1{separator}支付密码1
                                账号2{separator}密码2{separator}支付密码2
                                账号3{separator}密码3{separator}支付密码3
                            '''.format(separator=self.separator)
        print(encode_info(WELCOME))
        self.preset_filename = raw_input(encode_info(u'请输入导入账号列表的文件名称(默认: data.txt): ')) or u'data.txt'

    def read_preset_data_change_paypassword(self):
        debug(encode_info(u'开始读取账号列表: %r' % self.preset_filename))
        if not os.path.exists(self.preset_filename):
            raise FuckException(encode_info(u'文件不存在'))
        lines = bom_read(self.preset_filename)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tmp = line.split(self.separator)
            if len(tmp) != 3:
                raise_error(encode_info(u'账号密码书写格式错误: %r' % tmp))
            username = tmp[0].strip()
            password = tmp[1].strip()
            paypassword = tmp[2].strip()
            # self.queue.append((username, password))
            self.queue.put((username, password, paypassword))

        logging.debug(self.queue)

    def record_account_error(self, username):
        count = self.error_dict.get(username, 0)
        count += 1
        self.error_dict[username] = count

    def hanlder_error_change_paypassword(self, e, queue):
        try:
            logging.error(e)
            print(e)
        except Exception as e:
            pass
        username = queue[0]
        # 获取错误计数
        count = self.error_dict.get(username, 0)
        if count > self.max_error_count:
            self.failure_list.append(queue)
            self.write_reset_paypassword_result('----'.join((username, u'失败')))
        else:
            # 增加计数
            self.record_account_error(username)
            # 加回队列
            debug(encode_info(u'放回队尾: %r' % queue))
            self.queue.put(queue)

    def login(self, username, password):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
        dcap["phantomjs.page.settings.userAgent"] = (choice(AGENTS_ALL))
        # 不载入图片，爬页面速度会快很多
        # dcap["phantomjs.page.settings.loadImages"] = False
        try:
            phantomjs_driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phantomjs.exe')
            if not os.path.exists(phantomjs_driver_path):
                phantomjs_driver_path = 'phantomjs'
        except Exception as e:
            phantomjs_driver_path = 'phantomjs'
            debug(e)

        driver = webdriver.PhantomJS(
            phantomjs_driver_path,
            service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'],
            desired_capabilities=dcap,
        )
        # 隐式等待5秒，可以自己调节
        driver.implicitly_wait(5)
        try:
            driver.set_page_load_timeout(60)
            # driver.maximize_window()
            driver.set_window_size(1366, 942)
            driver.get('https://pay.360.cn/index')

            # 点击登录按钮
            debug(encode_info(u'点击登录按钮'))
            btn_login = driver.find_element_by_class_name('u-login')
            btn_login.click()

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "quc-input-account"))
            )

            # 填写用户名密码
            debug(encode_info(u'键入用户名: %r' % username))
            input_username = driver.find_element_by_class_name('quc-input-account')
            input_username.clear()
            input_username.send_keys(username)
            time.sleep(self.interval_time)

            debug(encode_info(u'键入密码: %r' % password))
            input_password = driver.find_element_by_class_name('quc-input-password')
            input_password.clear()
            input_password.click()
            time.sleep(self.interval_time)
            input_password.send_keys(password)
            # 验证码
            captcha = driver.find_element_by_class_name('quc-captcha-img')
            debug(encode_info(u'验证码是否显示: %r' % captcha.is_displayed()))

            captcha_src = captcha.get_attribute('src')
            debug('captcha_src: %r' % captcha_src)

            if captcha_src:
                debug(encode_info(u'需要验证码!: %r' % captcha_src))
                # 获取二维码坐标
                location = captcha.location
                size = captcha.size
                # 截取二维码
                x = int(location.get('x', 673))
                y = int(location.get('y', 483))
                w = int(size.get('width', 88))
                h = int(size.get('height', 35))
                box = (x, y, x + w, y + h)
                _screenshot_filename = self.screenshot_filename % username
                _captcha_filename = self.captcha_filename % username
                # _screenshot_filename = 'tmp_screenshot.png'
                # _captcha_filename = 'tmp_captcha.png'
                debug(encode_info(u'截图, 保存为 %r' % _screenshot_filename))
                captcha.screenshot(_screenshot_filename)
                screenshot = Image.open(_screenshot_filename)
                debug(encode_info(u'从截图中裁剪出验证码, 保存为 %r' % _captcha_filename))
                img_crop = screenshot.crop(box)
                img_crop.save(_captcha_filename)
                img_crop.close()
                screenshot.close()

                time.sleep(self.interval_time)
                debug(encode_info(u'开始验证码识别'))
                if self.captcha_mode == 0:
                    # yzm = chaorendama()
                    yzm = ''

                elif self.captcha_mode == 2:
                    from yundama_http import Recognize
                    # yzm = recognize_by_http(_captcha_filename, self.captcha_username, self.captcha_password)
                    r = Recognize()
                    yzm = r.run(_captcha_filename)

                else:
                    yzm = recognize_captcha_by_yourself(_captcha_filename)

                debug(encode_info(u'验证码解码为: %r' % yzm))
                if not yzm.strip():
                    self.error_dict[username] = 0
                    debug(encode_info(u'解码验证码失败'))
                    raise_error(encode_info(u'解码验证码失败'))
                debug(encode_info(u'填入验证码'))
                input_captcha = driver.find_element_by_class_name('quc-input-captcha')
                input_captcha.send_keys(yzm)
                # 删除图片
                try:
                    os.remove(_captcha_filename)
                    os.remove(_screenshot_filename)
                    debug(encode_info(u'删除图片'))
                except Exception as e:
                    print(e)

            # 登录
            input_submit = driver.find_element_by_class_name('quc-button-sign-in')
            input_submit.click()

            time.sleep(self.interval_time)

            # 判断是否成功
            error_tips = driver.find_elements_by_class_name('quc-tip-error')
            if len(error_tips) > 0:
                error = error_tips[0].text
                debug(error)
                raise LoginErrorException(error)

            # 登录成功会显示的
            display_name = driver.find_elements_by_class_name('display_name')
            if len(display_name) > 0:
                debug(encode_info(u'登录成功'))
            else:
                driver.quit()
                driver = None
        except Exception as e:
            debug(encode_info(u'登录错误: %r' % e))
            driver.quit()
            driver = None
            if isinstance(e, LoginErrorException):
                if u'密码错误' in e.message:
                    self.write_reset_paypassword_result('----'.join((username, u'密码错误')))
                elif u'无效的登录' in e.message:
                    self.write_reset_paypassword_result('----'.join((username, u'无效的登录')))
                    # raise_error(u'密码错误')
                else:
                    raise_error(encode_info(u'登录错误: %r' % e))
        return driver

    def run_change_paypassword(self):
        while not self.queue.empty():
            username, password, paypassword = self.queue.get_nowait()
            debug(encode_info(u'==== 开始  用户名: %r, 密码: %r, 支付密码: %r ====' % (username, password, paypassword)))
            try:
                self.change_pay_password(username, password, paypassword)
            except Exception as e:
                self.hanlder_error_change_paypassword(e, [username, password, paypassword])
            debug(encode_info(u'==== 结束  用户名: %r, 密码: %r, 支付密码: %r ====' % (username, password, paypassword)))

    def change_pay_password(self, username, password, pay_password):
        driver = self.login(username, password)
        is_success = True
        if driver is None:
            # raise_error(encode_info(u'登录失败'))
            return
        try:
            debug(encode_info(u'开始获取余额: %r' % username))
            # 获得cookie信息
            cookies = driver.get_cookies()
            self.retrieve_balance(cookies, username)
            # 判断是否修改过密码
            driver.get('https://pay.360.cn/account/security')
            result = self.is_change_paypass_success(driver.page_source)
            if result:
                self.change_pay_password_result[username] = u'已设置支付密码'
                self.write_reset_paypassword_result('----'.join((username, u'已设置支付密码')))
                debug(encode_info(u'已经修改过密码'))
            else:

                debug(encode_info(u'开始修改密码'))
                # 开始修改密码
                driver.get('https://pay.360.cn/account/index')
                try:
                    input_password = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "loginpass"))
                    )
                except Exception as e:
                    self.change_pay_password_result[username] = u'已设置支付密码'
                    self.write_reset_paypassword_result('----'.join((username, u'已设置支付密码')))
                    raise e
                input_password.click()
                input_password.send_keys(password)
                time.sleep(self.interval_time)

                input_pay_password = driver.find_element_by_name('paypass')
                input_pay_password.click()
                input_pay_password.send_keys(pay_password)
                time.sleep(self.interval_time)

                input_pay_password_again = driver.find_element_by_name('re_pay_passwd')
                input_pay_password_again.click()
                input_pay_password_again.send_keys(pay_password)
                time.sleep(self.interval_time)

                input_answer = driver.find_element_by_name('answer')
                input_answer.click()
                input_answer.send_keys(self.favourate_star)

                time.sleep(self.interval_time)

                input_submit = driver.find_element_by_class_name('u-btn-large')
                input_submit.click()

                time.sleep(self.interval_time)

                # 查看是否成功
                driver.get('https://pay.360.cn/account/security')
                result = self.is_change_paypass_success(driver.page_source)
                if not result:
                    raise_error(encode_info(u'修改失败'))

                # 修改密码结果字典更新
                self.change_pay_password_result[username] = password
                self.write_reset_paypassword_result('----'.join((username, password)))


        except Exception as e:
            debug(e)
            is_success = False
        finally:
            driver.quit()
        if not is_success:
            # raise_error(encode_info(u'修改失败'))
            raise_error('update payment password failed')
        else:
            return True

    @staticmethod
    def write_balance_txt(line):
        debug(encode_info(u'添加到余额txt: balance.txt'))
        with open('balance.txt', 'a') as f:
            f.write(line + '\n')
        debug(encode_info(u'余额txt: balance.txt 保存完成'))

    @staticmethod
    def is_change_paypass_success(html):
        match = re.findall(r"hasPaymentPwd: '(\w+)'", html)
        debug(encode_info(u'匹配: %r' % match))
        if match and match[0] in ['Y', u'Y']:
            debug(encode_info(u'修改成功'))
            return True
        else:
            debug(encode_info(u'修改失败'))
            return False

    def write_reset_paypassword_result(self, line):
        debug(encode_info(u'开始写结果: %s' % line))
        with open('result.txt', 'a') as f:
            f.write(encode_info(line + '\n'))
        debug(encode_info(u'写结果结束'))

    def write_failure_list(self):
        with open('failure.txt', 'w') as f:
            for line in self.failure_list:
                f.write('----'.join(line) + '\n')
        debug(encode_info(u'保存失败账号列表成功: failure.txt'))

    def retrieve_balance(self, cookies, username):
        sess = requests.Session()
        sess.cookies.update(dict([(i['name'], i['value']) for i in cookies]))
        sess.headers = choice(AGENTS_ALL)
        # 获取余额
        res = sess.get('https://pay.360.cn/account/index', timeout=10)
        root = etree.HTML(res.text)
        em = root.xpath('//em[@class="s-cl-g"]')

        if em:
            balance = em[0].text
        else:
            # 获取第一条的余额
            debug(encode_info(u'没有数据！%r' % username))
            self.empty_data_list.append(username)
            return
        debug(encode_info(u'账号余额: %r' % balance))
        self.write_balance_txt('----'.join((username, balance)))

        self.balance_list.append((username, balance))

    def run_change_paypassword_several_thread(self):
        for i in xrange(self.THREAD_NUM):
            t = Thread(target=self.run_change_paypassword, name='thread_%s' % i)
            self.threading_pool.append(t)

        for t in self.threading_pool:
            debug(encode_info(u'线程启动: %r' % t.getName()))
            t.start()

        [t.join() for t in self.threading_pool]

    def run(self):
        try:
            start = time.time()
            self.settings()

            self.read_preset_data_change_paypassword()

            # self.run_change_paypassword_several_thread()
            self.run_change_paypassword()

            if self.failure_list:
                debug(encode_info(u'失败的账号列表:r' % self.failure_list))
                self.write_failure_list()

            # self.write_reset_paypassword_result()

            debug(encode_info(u'完成! 用时: %0.4f' % (time.time() - start)))
            os.rmdir(self.tmp_path)
        except Exception as e:
            debug(e)

        raw_input(encode_info(u'按回车键结束'))


if __name__ == '__main__':
    p = ChangePayPass()
    p.run()
    # p.test()
    # p.login('gzyz0005', 'a123456')
