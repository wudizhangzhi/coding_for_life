# encoding: utf-8

import os
import sys
import logging

import datetime
import requests
import time

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='log.log',
                    filemode='w')


def debug(info):
    logging.debug(info)
    print(info)


from xlsxwriter import Workbook

from agents import AGENTS_ALL
from random import choice
import json
from PIL import Image
from lxml import etree

try:
    from decaptcha import dcVerCode
except Exception as e:
    debug(e)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 引入配置对象DesiredCapabilities
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from Queue import Queue
from threading import Thread


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
    logging.error(e)
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


class FuckException(Exception): pass


class Pay360:
    def __init__(self):
        self.agent = choice(AGENTS_ALL)
        self.sess = requests.Session()
        headers = {
            'User-Agent': self.agent,
        }
        self.sess.headers = headers
        # urls
        self.url = 'https://pay.360.cn/index'
        self.url_login = 'https://login.360.cn/'
        self.url_billquery = 'https://pay.360.cn/account/billQuery?trans=3&startdate=20171014&enddate=20171014&curr_page=1&per_page=5&qid=2958788410'

        # settings
        self.screenshot_filename = 'tmp_screenshot_%s.png'
        self.captcha_filename = 'tmp_captcha_%s.png'
        self.dirname = 'datas_excel'
        if not os.path.exists(self.dirname):
            os.mkdir(self.dirname)

        self.empty_data_list = []  # 没有数据的账号列表
        self.failure_list = []  # 超过最大错误计数失败的账号列表
        self.error_dict = {}  # 错误计数
        self.max_error_count = 3

        # 需要设置的信息
        self.captcha_username = None
        self.captcha_password = None
        self.preset_filename = 'data.txt'
        self.interval_time = 2  # 间隔时间
        self.captcha_mode = 0  # 验证码识别模式。0：超人打码， 1：人工识别
        self.date_before = 0  # 获取多少天前的数据
        # self.queue = []  # 队列。用于存储待爬取的账户
        self.queue = Queue()
        self.balance_list = []  # 用于保存余额列表
        self.DEBUG = True
        self.THREAD_NUM = 4  # 线程数量  #
        self.threading_pool = []

        self.favourate_star = u'张杰'  # 支付密码修改问题
        self.change_pay_password_result = {}

    def record_account_error(self, username):
        count = self.error_dict.get(username, 0)
        count += 1
        self.error_dict[username] = count

    def chaorendama(self, captcha_filename=None):
        # 二维码调用接口解码
        debug(encode_info(u'开始登录超人打码: %r' % self.captcha_username))
        client = dcVerCode(self.captcha_username, self.captcha_password, "0")
        # 查询帐号余额
        debug(encode_info(u'超人打码余额: %r' % client.getUserInfo()))
        yzm, imageId = client.recYZM(self.captcha_filename)
        debug(encode_info(u'返回验证码: %r' % yzm))
        if not yzm:
            raise_error(encode_info(u'验证码解码失败!'))
        return yzm

    def recognize_captcha_by_yourself(self, captcha_filename=None):
        debug(encode_info(u'开始人工识别验证码'))
        img = Image.open(captcha_filename or self.captcha_filename)
        img.show()
        chaptcha_code = raw_input(encode_info(u'请输入验证码: '))
        if not chaptcha_code:
            raise_error(encode_info(u'请输入正确的验证码!'))
        return chaptcha_code

    @staticmethod
    def yundama(username, password, captcha_filename=None):  # 云打码
        from yundama import recognize_by_http
        captcha_filename = captcha_filename
        debug(encode_info(u'验证码地址: %r' % captcha_filename))
        debug(encode_info(u'验证码是否存在: %r' % os.path.exists(captcha_filename)))

        # result, balanse = recognize_common(captcha_filename, self.captcha_username,
        #                                    self.captcha_password)
        result, balanse = recognize_by_http(captcha_filename, username,
                                            password)
        debug(encode_info(u'余额: %r' % balanse))
        return result

    def hanlder_error(self, e, username, password):
        logging.error(e)
        print(e)
        # 获取错误计数
        count = self.error_dict.get(username, 0)
        if count > self.max_error_count:
            self.failure_list.append((username, password))
        else:
            # 增加计数
            self.record_account_error(username)
            # 加回队列
            debug(encode_info(u'放回队尾: %r, %r' % (username, password)))
            # self.queue.append((username, password))
            self.queue.put((username, password))

    def run_phangomjs(self, username, password):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
        dcap["phantomjs.page.settings.userAgent"] = (choice(AGENTS_ALL))
        # 不载入图片，爬页面速度会快很多
        # dcap["phantomjs.page.settings.loadImages"] = False
        try:
            phantomjs_driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phantomjs.exe')
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
            driver.get(self.url)

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
                debug(encode_info(u'截图, 保存为 %r' % _screenshot_filename))
                captcha.screenshot(_screenshot_filename)
                screenshot = Image.open(_screenshot_filename)
                debug(encode_info(u'从截图中裁剪出验证码, 保存为 %r' % _captcha_filename))
                img_crop = screenshot.crop(box)
                img_crop.save(_captcha_filename)
                screenshot.close()
                img_crop.close()

                if self.captcha_mode == 0:
                    yzm = self.chaorendama()

                elif self.captcha_mode == 2:
                    yzm = self.yundama()

                else:
                    yzm = self.recognize_captcha_by_yourself()

                debug(encode_info(u'验证码解码为: %r' % yzm))
                if not yzm:
                    raise_error(encode_info(u'解码验证码失败'))
                debug(encode_info(u'填入验证码'))
                input_captcha = driver.find_element_by_class_name('quc-input-captcha')
                input_captcha.send_keys(yzm)

            # 登录
            input_submit = driver.find_element_by_class_name('quc-button-sign-in')
            input_submit.click()

            time.sleep(self.interval_time)

            # 判断是否成功
            error_tips = driver.find_elements_by_class_name('quc-tip-error')
            if len(error_tips) > 0:
                error = error_tips[0].text
                debug(error)
                raise FuckException(error)

            # 登录成功会显示的
            display_name = driver.find_elements_by_class_name('display_name')
            if len(display_name) > 0:
                debug(encode_info(u'登录成功'))
            else:
                raise_error(encode_info(u'登录失败'))

            # 获得cookie信息
            cookies = driver.get_cookies()
            logging.debug(cookies)
            self.crawl_info(cookies, username)

        except Exception as e:
            self.hanlder_error(str(e), username, password)
        finally:
            if not self.DEBUG:
                # 删除全屏截图
                if os.path.exists(self.screenshot_filename):
                    os.remove(self.screenshot_filename)
                    os.remove(self.captcha_filename)
                    debug(encode_info(u'删除缓存图片'))
            else:
                driver.save_screenshot('test.png')
            driver.close()
            if driver:
                driver.quit()

    def crawl_info(self, cookies, username=None, current_page=1):
        '''
        invoking api via cookies from driver
        :param cookies: 
        :return: 
        '''
        debug(encode_info(u'开始爬取: %r' % username))
        results = []
        now = datetime.datetime.now()
        startdate = (now - datetime.timedelta(days=self.date_before)).strftime('%Y%m%d')
        enddate = now.today().strftime('%Y%m%d')
        # filename = '_'.join((str(username), now.strftime('%Y_%m_%d_%H_%M_%S.xlsx')))
        filename = '%s.xlsx' % username

        sess = requests.Session()
        sess.cookies.update(dict([(i['name'], i['value']) for i in cookies]))
        sess.headers = choice(AGENTS_ALL)
        res = sess.get('https://pay.360.cn/quser/getUserInfo?qid=', timeout=10)
        j = json.loads(res.text)
        qid = j['userinfo']['qid']
        debug('qid: %r' % qid)
        time.sleep(self.interval_time / 2.0)

        def get_records(page):
            debug(encode_info(u'开始爬取页数: %r' % page))
            params = {
                'trans': 3,
                'startdate': startdate,
                'enddate': enddate,
                'curr_page': page,
                'per_page': 30,
                'qid': qid,
            }
            res = sess.get(
                'https://pay.360.cn/account/billQuery', params=params, timeout=10)

            # res.encoding = 'utf-8'
            j = json.loads(res.text)
            logging.debug(json.dumps(j, indent=4))
            return j

        j = get_records(current_page)
        pages = j['pages'] or 1
        records = j['record']
        results.extend(records)

        # 获取余额
        res = sess.get('https://pay.360.cn/account/index', timeout=10)
        root = etree.HTML(res.text)
        em = root.xpath('//em[@class="s-cl-g"]')

        if em:
            balance = em[0].text
        elif records:
            balance = records[0]['balance']
        else:
            # 获取第一条的余额
            debug(encode_info(u'没有数据！%r' % username))
            self.empty_data_list.append(username)
            return
        debug(encode_info(u'账号余额: %r' % balance))
        self.write_balance_txt('----'.join((username, balance)))

        self.balance_list.append((username, balance))

        # 如果pages != page 继续下一页
        while pages != current_page:
            current_page += 1

            j = get_records(current_page)
            pages = j['pages'] or 1
            records = j['record']
            if not records:
                break
            results.extend(records)

        # 写数据到excel
        title = '%s - %s: username:%s' % (startdate, enddate, username)
        self.write_excel(title, filename, results)

    def write_excel(self, title, filename, datas):
        filepath = os.path.join(self.dirname, filename)
        debug(encode_info(u"开始生成 excel: %r" % filepath))
        workbook = Workbook(filepath)
        try:
            worksheet = workbook.add_worksheet('sheet1')

            title_format = workbook.add_format({'valign': 'vcenter', 'align': 'center',
                                                'locked': True, 'bold': True, 'font_size': '20', })

            top_format = workbook.add_format({'text_wrap': 1, 'valign': 'vcenter',
                                              'locked': True, 'bold': True, 'bg_color': '#D7D7D7',
                                              'font_size': '12', 'border': True})

            body_format = workbook.add_format({'text_wrap': 1, 'valign': 'vcenter',
                                               'font_size': '12', 'align': 'left',
                                               'border': True})

            body_format_t = workbook.add_format({'text_wrap': 1, 'valign': 'vcenter',
                                                 'font_size': '12', 'align': 'left',
                                                 'border': True, 'bg_color': '#e7e7e7'})

            worksheet.merge_range(0, 0, 2, 6, title, title_format)
            width = 4
            worksheet.freeze_panes(6, 1)

            worksheet.set_column(0, 0, width * 1.5)
            worksheet.set_column(1, 1, width * 5)
            worksheet.set_column(2, 2, width * 4)
            worksheet.set_column(3, 3, width * 15)
            worksheet.set_column(4, 4, width * 7)
            worksheet.set_column(5, 5, width * 5)
            worksheet.set_column(6, 6, width * 5)

            worksheet.write(3, 0, u'No.', top_format)
            worksheet.write(3, 1, u'交易时间', top_format)
            worksheet.write(3, 2, u'类型', top_format)
            worksheet.write(3, 3, u'相关单号', top_format)
            worksheet.write(3, 4, u'充值方式/商品名称', top_format)
            worksheet.write(3, 5, u'收入/支出', top_format)
            worksheet.write(3, 6, u'余额', top_format)

            set_row = 3
            index = 0
            for data in datas:
                set_row += 1
                index += 1
                if index % 2 == 0:
                    tmp_body_format = body_format
                else:
                    tmp_body_format = body_format_t

                trans_name = data['trans_name']
                desc = data['desc']
                if isinstance(trans_name, str):
                    trans_name = trans_name.decode('unicode_escape')
                if isinstance(desc, str):
                    desc = desc.decode('unicode_escape')
                flow = data['flow']
                flow_out = True if flow.lower() == 'out' else False
                payment = ''.join(('-' if flow_out else '', data['trans_amt']))

                worksheet.write(set_row, 2, trans_name, tmp_body_format)
                worksheet.write(set_row, 0, index, tmp_body_format)
                worksheet.write(set_row, 1, data['trans_time'], tmp_body_format)
                worksheet.write(set_row, 3, data['trans_id'], tmp_body_format)
                worksheet.write(set_row, 4, desc, tmp_body_format)
                worksheet.write(set_row, 5, payment, tmp_body_format)
                worksheet.write(set_row, 6, data['balance'], tmp_body_format)
        except Exception as e:
            debug(e)
        finally:
            workbook.close()
        debug(encode_info(u"保存excel: %r" % filepath))

    def setting(self, is_change_paypassword=False):
        captcha_mode = raw_input(encode_info(u'请输入识别验证码的模式(0:超人打码 ;1:人工识别; 2:云打码 默认2): ')) or 2
        self.captcha_mode = int(captcha_mode)
        if self.captcha_mode in [0, 2]:
            DEFAULT = {
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

        if not is_change_paypassword:
            date_before = raw_input(encode_info(u'请输入从多少天前开始的数据(默认0，即当天): ')) or 0
            self.date_before = int(date_before)
        if is_change_paypassword:
            WELCOME = u'''
                        导入账号列表的文件格式:
                            账号1:密码1:支付密码1
                            账号2:密码2:支付密码2
                            账号3:密码3:支付密码3
                        '''
        else:
            WELCOME = u'''
                    导入账号列表的文件格式:
                        账号1:密码1
                        账号2:密码2
                        账号3:密码3
            '''
        print(encode_info(WELCOME))
        self.preset_filename = raw_input(encode_info(u'请输入导入账号列表的文件名称(默认: data.txt): ')) or u'data.txt'

    def read_preset_data(self):
        debug(encode_info(u'开始读取账号列表: %r' % self.preset_filename))
        if not os.path.exists(self.preset_filename):
            raise FuckException(encode_info(u'文件不存在'))
        lines = bom_read(self.preset_filename)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tmp = line.split(':')
            if len(tmp) != 2:
                raise_error(encode_info(u'账号密码书写格式错误: %r' % tmp))
            username = tmp[0].strip()
            password = tmp[1].strip()
            # self.queue.append((username, password))
            self.queue.put((username, password))

        logging.debug(self.queue)

    def write_balance_txt(self, line):
        debug(encode_info(u'添加到余额txt: balance.txt'))
        with open('balance.txt', 'a') as f:
            f.write(line + '\n')
        debug(encode_info(u'余额txt: balance.txt 保存完成'))

    def writer_failure_list(self):
        with open('failure.txt', 'w') as f:
            for line in self.failure_list:
                f.write('----'.join(line) + '\n')
        debug(encode_info(u'保存失败账号列表成功: failure.txt'))

    def run(self):
        # while len(self.queue) > 0:
        while not self.queue.empty():
            # username, password = self.queue.pop(0)
            username, password = self.queue.get_nowait()
            debug(encode_info(u'==== 开始  用户名: %r, 密码: %r ====' % (username, password)))
            try:
                self.run_phangomjs(username, password)
            except Exception as e:
                self.hanlder_error(str(e), username, password)
            debug(encode_info(u'==== 结束  用户名: %r, 密码: %r ====' % (username, password)))

    def run_severval_thread(self):  # 多线程版本
        for i in xrange(self.THREAD_NUM):
            t = Thread(target=self.run, name='thread_%s' % i)
            self.threading_pool.append(t)

        for t in self.threading_pool:
            debug(encode_info(u'线程启动: %r' % t.getName()))
            t.start()

        [t.join() for t in self.threading_pool]

    def main(self):
        try:
            start = time.time()
            # 设置
            self.setting()

            # 读取账号文件, 并将账号信息存入queue队列
            self.read_preset_data()

            # 开始逐一爬取
            # self.run()
            # 多线程爬取
            self.run_severval_thread()

            # # 生成余额txt
            # self.write_balance_txt()

            if self.empty_data_list:
                debug(encode_info(u'没有数据的账号有: %r' % self.empty_data_list))

            if self.failure_list:
                debug(encode_info(u'失败的账号列表:r' % self.failure_list))
                self.writer_failure_list()

            debug(encode_info(u'完成! 用时: %0.4f' % (time.time() - start)))
        except Exception as e:
            debug(e)

        raw_input(encode_info(u'按回车键结束'))

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
            driver.get(self.url)

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

                if self.captcha_mode == 0:
                    yzm = self.chaorendama()

                elif self.captcha_mode == 2:
                    yzm = Pay360.yundama(_captcha_filename)

                else:
                    yzm = self.recognize_captcha_by_yourself(_captcha_filename)

                debug(encode_info(u'验证码解码为: %r' % yzm))
                if not yzm.strip():
                    self.error_dict[username] = 0
                    raise_error(encode_info(u'解码验证码失败'))
                debug(encode_info(u'填入验证码'))
                input_captcha = driver.find_element_by_class_name('quc-input-captcha')
                input_captcha.send_keys(yzm)
                # 删除图片
                try:
                    # os.remove(_captcha_filename)
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
                raise FuckException(error)

            # 登录成功会显示的
            display_name = driver.find_elements_by_class_name('display_name')
            if len(display_name) > 0:
                debug(encode_info(u'登录成功'))
            else:
                # raise_error(encode_info(u'登录失败'))
                driver.quit()
                driver = None
        except Exception as e:
            # self.hanlder_error(str(e), username, password)
            driver.quit()
            driver = None
        return driver

    def read_preset_data_change_paypassword(self):
        debug(encode_info(u'开始读取账号列表: %r' % self.preset_filename))
        if not os.path.exists(self.preset_filename):
            raise FuckException(encode_info(u'文件不存在'))
        lines = bom_read(self.preset_filename)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tmp = line.split(':')
            if len(tmp) != 3:
                raise_error(encode_info(u'账号密码书写格式错误: %r' % tmp))
            username = tmp[0].strip()
            password = tmp[1].strip()
            paypassword = tmp[2].strip()
            # self.queue.append((username, password))
            self.queue.put((username, password, paypassword))

        logging.debug(self.queue)

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

    def change_pay_password(self, username, password, pay_password):
        driver = self.login(username, password)
        is_success = True
        if driver is None:
            raise_error('login failed')
        try:
            # 开始修改密码
            # a_myaccount = driver.find_element_by_link_text('/account/index')
            # a_myaccount.click()
            driver.get('https://pay.360.cn/account/index')
            try:
                input_password = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "loginpass"))
                )
            except Exception as e:
                self.change_pay_password_result[username] = u'已设置支付密码'
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
            # 查看是否成功
            driver.get('https://pay.360.cn/account/security')
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "u-safe-box"))
            )
            time.sleep(self.interval_time)
            debug(encode_info(u'修改成功'))
            # 修改密码结果字典更新
            self.change_pay_password_result[username] = password
            # 获得cookie信息
            cookies = driver.get_cookies()
            self.retrieve_balance(cookies, username)

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
        else:
            # 增加计数
            self.record_account_error(username)
            # 加回队列
            debug(encode_info(u'放回队尾: %r' % queue))
            # self.queue.append((username, password))
            self.queue.put(queue)

    def run_change_paypassword(self):
        while not self.queue.empty():
            # username, password = self.queue.pop(0)
            username, password, paypassword = self.queue.get_nowait()
            debug(encode_info(u'==== 开始  用户名: %r, 密码: %r, 支付密码: %r ====' % (username, password, paypassword)))
            try:
                self.change_pay_password(username, password, paypassword)
            except Exception as e:
                self.hanlder_error_change_paypassword(e, [username, password, paypassword])
            debug(encode_info(u'==== 结束  用户名: %r, 密码: %r, 支付密码: %r ====' % (username, password, paypassword)))

    def run_change_paypassword_several_thread(self):
        # for i in xrange(self.THREAD_NUM):
        #     t = Thread(target=self.run_change_paypassword, name='thread_%s' % i)
        #     self.threading_pool.append(t)
        #
        # for t in self.threading_pool:
        #     debug(encode_info(u'线程启动: %r' % t.getName()))
        #     t.start()

        # [t.join() for t in self.threading_pool]
        self.run_change_paypassword()

    def write_reset_paypassword_result(self):
        debug(encode_info(u'开始写结果: %r' % self.change_pay_password_result))
        with open('result.txt', 'w') as f:
            for k, v in self.change_pay_password_result.iteritems():
                f.write(encode_info('----'.join((k, v)) + '\n'))
        debug(encode_info(u'写结果结束'))

    def main_change_paypassword(self):
        try:
            start = time.time()
            self.setting(is_change_paypassword=True)

            self.read_preset_data_change_paypassword()

            self.run_change_paypassword_several_thread()

            if self.failure_list:
                debug(encode_info(u'失败的账号列表:r' % self.failure_list))
                self.writer_failure_list()

            self.write_reset_paypassword_result()

            debug(encode_info(u'完成! 用时: %0.4f' % (time.time() - start)))
        except Exception as e:
            debug(e)

        raw_input(encode_info(u'按回车键结束'))


if __name__ == '__main__':
    p = Pay360()
    # p.main()  # 拉取信息
    # p.main_change_paypassword()  # 修改支付密码
    # p.setting(is_change_paypassword=True)
    # p.read_preset_data_change_paypassword()
    # print(Pay360.yundama('tmp_captcha_gzyz0005.png'))
    # p.run_change_paypassword()
    # p.login('gzyz0005', 'a123456')
    # p.change_pay_password('IEM14HJs84', 'a147258', 'a123456')
