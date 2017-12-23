# encoding: utf-8
import os
import sys
import time
from ConfigParser import ConfigParser

#######################
CONFIG_PATH = 'config.ini'
BY_CLASS = 'class'
BY_ID = 'id'
#######################

assert os.path.exists(CONFIG_PATH)
cf = ConfigParser(CONFIG_PATH)
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from user_agent import generate_user_agent
from PIL import Image

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
    logging.error(e)
    raise Exception(e)


class BasePhantomjs(object):
    def __init__(self):
        self.url_login = ''
        self.interval_time = 3
        self.rule = {
            'startlogin': {'type': BY_CLASS, 'name': ''},
            'username': {'type': BY_CLASS, 'name': ''},
            'password': {'type': BY_CLASS, 'name': ''},
            'captcha_img': {'type': BY_CLASS, 'name': ''},
            'captcha': {'type': BY_CLASS, 'name': ''},
            'submit': {'type': BY_CLASS, 'name': ''},
            'show_success': {'type': BY_CLASS, 'name': ''},
            'show_error': {'type': BY_CLASS, 'name': ''},
            'captcha_tuple': ('', '', '', ''),   # x, y, w, h
        }
        self.captcha_mode = 2

    @staticmethod
    def recognize_captcha_by_yourself(captcha_filename):
        debug(encode_info(u'开始人工识别验证码'))
        img = Image.open(captcha_filename)
        img.show()
        chaptcha_code = raw_input(encode_info(u'请输入验证码: '))
        if not chaptcha_code:
            raise_error(encode_info(u'请输入正确的验证码!'))
        return chaptcha_code

    @staticmethod
    def yundama(captcha_filename=None):  # 云打码
        from yundama import recognize_by_http
        captcha_filename = captcha_filename
        debug(encode_info(u'验证码地址: %r' % captcha_filename))
        debug(encode_info(u'验证码是否存在: %r' % os.path.exists(captcha_filename)))

        result, balanse = recognize_by_http(captcha_filename, cf.get('captcha', 'username'),
                                            cf.get('captcha', 'password'))
        debug(encode_info(u'余额: %r' % balanse))
        return result

    @staticmethod
    def get_by(key):
        '''
        返回by的类型
        :param key: 
        :return: 
        '''
        if key == BY_CLASS:
            return By.CLASS_NAME
        elif key == BY_ID:
            return By.ID
        else:
            return By.NAME

    def login(self, username, password):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
        dcap["phantomjs.page.settings.userAgent"] = (generate_user_agent(os=('linux', 'mac')))
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
            driver.get(self.url_login)

            if self.rule.get('startlogin', ''):
                # 点击登录按钮
                debug(encode_info(u'点击登录按钮'))
                btn_login = driver.find_element(self.get_by(self.rule['startlogin']['type']),
                                                self.rule['startlogin']['name'])
                btn_login.click()

                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (self.get_by(self.rule['username']['type']), self.rule['username']['name']))
                )

            # 填写用户名密码
            debug(encode_info(u'键入用户名: %r' % username))
            input_username = driver.find_element(self.get_by(self.rule['username']['type']),
                                                 self.rule['username']['name'])
            input_username.clear()
            input_username.send_keys(username)
            time.sleep(self.interval_time)

            debug(encode_info(u'键入密码: %r' % password))
            input_password = driver.find_element(self.get_by(self.rule['password']['type']),
                                                 self.rule['password']['name'])
            input_password.clear()
            input_password.click()
            time.sleep(self.interval_time)
            input_password.send_keys(password)
            # 验证码
            class_name_captha = self.rule.get('captcha', '')
            if class_name_captha:
                captcha = driver.find_element(self.get_by(self.rule['captcha_img']['type']),
                                              self.rule['captcha_img']['name'])
                debug(encode_info(u'验证码是否显示: %r' % captcha.is_displayed()))

                captcha_src = captcha.get_attribute('src')
                debug('captcha_src: %r' % captcha_src)

                if captcha_src:
                    debug(encode_info(u'需要验证码!: %r' % captcha_src))
                    # 获取二维码坐标
                    location = captcha.location
                    size = captcha.size
                    # 截取二维码
                    x = int(location.get('x', self.rule['captcha_tuple'][0]))
                    y = int(location.get('y', self.rule['captcha_tuple'][1]))
                    w = int(size.get('width', self.rule['captcha_tuple'][2]))
                    h = int(size.get('height', self.rule['captcha_tuple'][3]))
                    box = (x, y, x + w, y + h)
                    _screenshot_filename = 'tmp/screenshow_' % username
                    _captcha_filename = 'tmp/captcha_' % username
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
                        yzm = self.yundama(_captcha_filename)

                    else:
                        yzm = self.recognize_captcha_by_yourself(_captcha_filename)

                    debug(encode_info(u'验证码解码为: %r' % yzm))
                    if not yzm.strip():
                        # self.error_dict[username] = 0
                        raise_error(encode_info(u'解码验证码失败'))
                    debug(encode_info(u'填入验证码'))
                    input_captcha = driver.find_element(self.get_by(self.rule['captcha']['type']),
                                                        self.rule['captcha']['name'])
                    input_captcha.send_keys(yzm)
                    # 删除图片
                    try:
                        # os.remove(_captcha_filename)
                        os.remove(_screenshot_filename)
                        debug(encode_info(u'删除图片'))
                    except Exception as e:
                        print(e)

            # 登录
            input_submit = driver.find_element(self.get_by(self.rule['submit']['type']),
                                               self.rule['submit']['name'])
            input_submit.click()

            time.sleep(self.interval_time)

            if self.rule.get('show_error', ''):
                # 判断是否成功
                error_tips = driver.find_elements(self.get_by(self.rule['show_error']['type']),
                                                  self.rule['show_error']['name'])
                if len(error_tips) > 0:
                    error = error_tips[0].text
                    debug(error)
                    raise Exception(error)

            if self.rule.get('show_success', ''):
                # 登录成功会显示的
                display_name = driver.find_elements(self.get_by(self.rule['show_success']['type']),
                                                    self.rule['show_success']['name'])
                if len(display_name) > 0:
                    debug(encode_info(u'登录成功'))
                else:
                    driver.quit()
                    driver = None
        except Exception as e:
            driver.quit()
            driver = None
        return driver
