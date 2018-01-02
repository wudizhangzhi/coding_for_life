import json
import re
import sys

sys.path.append("..")
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains  # 引入ActionChains鼠标操作类
import requests
from PIL import Image, ImageChops
import numpy as np
from functools import reduce
from lxml import etree

from base.base import *

'''
1. login 
2. get captcha
3. find the most dark part of image (pixel minimum)
4. calulate distance
'''


def avhash(im):  # 通过计算哈希值来得到该张图片的“指纹”
    if not isinstance(im, Image.Image):  # 判断参数im，是不是Image类的一个参数
        im = Image.open(im)
    im = im.resize((8, 8), Image.ANTIALIAS).convert('L')
    # resize，格式转换，把图片压缩成8*8大小，ANTIALIAS是抗锯齿效果开启，“L”是将其转化为
    # 64级灰度，即一共有64种颜色
    avg = reduce(lambda x, y: x + y, im.getdata()) / 64.  # 递归取值，这里是计算所有
    # 64个像素的灰度平均值
    return reduce(lambda x, y: x | (y[1] << y[0]),
                  enumerate(map(lambda i: 0 if i < avg else 1, im.getdata())),
                  0)  # 比较像素的灰度，将每个像素的灰度与平均值进行比较，>=avg：1；<avg：0


def hamming(h1, h2):  # 比较指纹，等同于计算“汉明距离”（两个字符串对应位置的字符不同的个数）
    h, d = 0, h1 ^ h2
    while d:
        h += 1
        d &= d - 1
    return h


def find_most_dark_part(img, w=0, h=0, top=None, resize=None):
    '''
    找到图像灰度最小(最黑)的区域
    :param img: 图像
    :param w: 区域宽度
    :param h: 区域高度
    :param top: top距离
    :return: (left, top)
    '''
    if not isinstance(img, Image.Image):  # 判断参数im，是不是Image类的一个参数
        img = Image.open(img)
    img = img.convert('L')
    if resize:
        img = img.resize(resize)
    width, height = img.size
    max_dark_value = float('inf')
    max_dark_img = None
    # print(width, height)
    matrix = np.matrix(img.getdata()).reshape((height, width))  # (行, 列)
    for i in range(w, width - w):
        if top:  # 如果固定高度
            j = top
            dark_value = np.sum(matrix[j:j + h, i:i + w])
            if dark_value < max_dark_value:
                max_dark_value = dark_value
                max_dark_img = (i, j)
        else:
            for j in range(height - h):
                dark_value = np.sum(matrix[j:j + h, i:i + w])
                if dark_value < max_dark_value:
                    max_dark_value = dark_value
                    max_dark_img = (i, j)
    # TODO delete; for test, show most dark part
    # if max_dark_img:
    #     left, top = max_dark_img
    #     Image.fromarray(matrix[top:top + w, left:left + h].astype(np.uint8)).show()
    return max_dark_img


def read_mouse_trace(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    result = []
    xoffset = yoffset = None
    x_pos = y_pos = 0
    is_first = True
    for line in lines:
       if not line.strip():
            continue 
       elif 'Delay' in line:  # delay
            match = re.findall(r'([\d\.]+)', line)
            delay = match[0]
            if xoffset and yoffset:
                result.append((int(xoffset) - x_pos, int(yoffset) - y_pos, float(delay)))
        else:  # move
            match = re.findall(r'(\d+)', line)
            if match:
                xoffset, yoffset = match
                if is_first:
                    x_pos, y_pos = int(xoffset), int(yoffset)
                    is_first = False

    return result


def scale_trace(distance, trace_old):
    pass


def get_track(distance):
    """
    根据偏移量获取移动轨迹
    :param distance: 偏移量
    :return: 移动轨迹
    """
    # 移动轨迹
    track = []
    # 当前位移
    current = 0
    # 减速阈值
    mid = distance * 4 / 5
    # 计算间隔
    t = 0.2
    # 初速度
    v = 0

    while current < distance:
        if current < mid:
            # 加速度为正2
            a = 2
        else:
            # 加速度为负3
            a = -3
        # 初速度v0
        v0 = v
        # 当前速度v = v0 + at
        v = v0 + a * t
        # 移动距离x = v0t + 1/2 * a * t^2
        move = v0 * t + 1 / 2 * a * t * t
        # 当前位移
        current += move
        track.append(round(move))
    if current != distance:
        track.append(round(distance - current))
    return track


RULE = {
    'startlogin': {'type': BY_ID, 'name': 'login'},
    'login_frame': {'type': BY_ID, 'name': 'login_frame'},
    'switch_plogin': {'type': BY_ID, 'name': 'switcher_plogin'},
    'username': {'type': BY_ID, 'name': 'u'},
    'password': {'type': BY_ID, 'name': 'p'},

    'submit': {'type': BY_ID, 'name': 'login_button'},
    'show_success': {'type': BY_ID, 'name': 'loginNickName'},
    'show_error': {'type': BY_ID, 'name': 'error_tips'},
    #### 验证码部分 ####
    # 'captcha_tuple': (380.0, 515.0, 69, 24),  # x, y, w, h
    # 'captcha_img': {'type': BY_ID, 'name': 'ctl00_MainContent_imgExtCode'},
    'captcha': {'type': BY_ID, 'name': 'newVcodeArea'},
    'slideblock': {'type': BY_ID, 'name': 'slideBlock'},
    'slidebkg': {'type': BY_ID, 'name': 'slideBkg'},
    'tcaptcha_drag_button': {'type': BY_ID, 'name': 'tcaptcha_drag_button'},
    'tcaptcha-imgarea': {'type': BY_CLASS, 'name': 'tcaptcha-imgarea'},  # 验证码背景图的div
}


class QQPay(BasePhantomjs):
    def __init__(self):
        super(QQPay, self).__init__()
        self.rule = RULE
        try:
            use_proxy = True if self.cf.get('proxy', 'url') else False
        except:
            use_proxy = False
        self.use_proxy = use_proxy
        self.url_login = 'https://pay.qq.com/'
        self.separator = self.cf.get('main', 'separator')
        self.HOST = 'https://ssl.captcha.qq.com'
        self.cookies_history = {}  # 保存的cookie历史

    def read_preset_data(self):
        '''
        读取预设的账号密码等数据
        '''
        debug('开始读取账号列表: %r' % self.inputputfilename)
        if not os.path.exists(self.inputputfilename):
            raise Exception(u'文件不存在')
        lines = bom_read(self.inputputfilename)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.separator in line:  # QQ号, 密码
                self.upq.put(line)
            else:
                raise_error(u'账号密码书写格式错误: %r' % line)

        logging.debug(self.preset_data)

    def run(self):
        self._read_cookies()
        # TODO
        self.read_preset_data()

        while not self.upq.empty():
            username_password = self.upq.get_nowait()

            if self.use_proxy:
                proxy = self._get_proxy()
            else:
                proxy = None
            try:
                self.search_by_one_account(username_password, proxy=proxy)
            except CaptchaException as e:
                # TODO 验证码问题
                print(e)
            except TimeoutException as e:
                # 代理ip的问题
                print(e)

            except Exception as e:
                print(e)
                # TODO
                self.raise_error_count(username_password)

    def search_by_one_account(self, username_password, proxy=None):
        separator = self.cf.get('main', 'separator')

        tmp = username_password.split(separator)

        username = tmp[0].strip()
        password = tmp[1].strip()

        debug(u'{:=^40}'.format(username))
        self.write_oneline(username_password)

        user_cookies = self.cookies_history.get(username, None)
        login_success = False
        if not user_cookies or self.is_cookies_expired(user_cookies):
            driver = self.login(username, password, proxy=proxy)
            if not driver:
                raise Exception('登录失败')

            if self.is_need_scroll_capthca(driver):
                driver = self.scroll_capthca(driver)

            # 验证登录是否成功
            login_success = self.is_login_success(driver)
            cookies = driver.get_cookies()
            driver.quit()
        else:
            debug('使用保存好的cookie直接登录')
            cookies = user_cookies

        if user_cookies or login_success:
            self._save_cookies(username, cookies)
            logging.debug(cookies)
            self.search_info(cookies)
        else:
            raise Exception('验证登录结果: 失败')

    def login(self, username, password, proxy=None):
        debug('开始登陆: {}'.format(username))
        driver = self.init_driver(proxy=proxy)

        driver.set_page_load_timeout(60)
        driver.set_window_size(1366, 942)
        driver.get(self.url_login)

        debug(u'获取登录界面')
        btn_login = driver.find_element(self.get_by(self.rule['startlogin']['type']),
                                        self.rule['startlogin']['name'])
        btn_login.click()

        debug(u'进入iframe')
        # 转到登录用iframe
        driver.switch_to.frame(driver.find_element(self.get_by(self.rule['login_frame']['type']),
                                                   self.rule['login_frame']['name']))
        time.sleep(self.interval_time)
        # 等待元素出现
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (self.get_by(self.rule['switch_plogin']['type']), self.rule['switch_plogin']['name']))
        )
        debug(u'点击使用账号密码登录按钮')
        element.click()

        # TODO 是否等在元素出现
        debug(encode_info(u'键入用户名: %r' % username))
        input_username = driver.find_element(self.get_by(self.rule['username']['type']),
                                             self.rule['username']['name'])
        input_username.clear()
        input_username.send_keys(username)
        time.sleep(self.interval_time)

        debug(encode_info(u'键入密码: %r' % password))
        input_password = driver.find_element(self.get_by(self.rule['password']['type']),
                                             self.rule['password']['name'])
        input_password.click()
        input_password.clear()
        input_password.send_keys(Keys.HOME)
        # input_password.send_keys(password)
        for k in list(password):
            input_password.send_keys(k)
            time.sleep(0.2)
        time.sleep(self.interval_time)
        print('结果: {}'.format(input_password.get_attribute('value')))
        driver.save_screenshot('输入完数据.png')
        debug(encode_info(u'点击登录'))
        # 登录
        input_submit = driver.find_element(self.get_by(self.rule['submit']['type']),
                                           self.rule['submit']['name'])
        input_submit.click()

        time.sleep(self.interval_time)
        return driver

    def is_need_scroll_capthca(self, driver):
        has_captcha = False
        # 判断验证码是否存在，也可以根据newVcodeIframe 下是否存在iframe判断
        captcha = driver.find_elements(self.get_by(self.rule['captcha']['type']),
                                       self.rule['captcha']['name'])
        if captcha:
            captcha = captcha[0]
            captcha_style = captcha.get_attribute('style')
            logging.debug('captcha_style: {}'.format(captcha_style))
            if captcha_style:  # 有验证码
                has_captcha = True
        if has_captcha:
            debug('需要验证码')
            return True
        else:
            debug('不需要验证码')
            return False

    def scroll_capthca(self, driver):
        debug('开始滑动解锁')
        # analysis captcha
        # scroll captcha
        # switch to iframe
        debug('跳转到验证码iframe')
        driver.switch_to.frame(driver.find_element_by_xpath('//*[@id="newVcodeIframe"]/iframe'))

        # 等待元素出现
        slidebkg = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (self.get_by(self.rule['slidebkg']['type']), self.rule['slidebkg']['name']))
        )

        slideblock = driver.find_element(self.get_by(self.rule['slideblock']['type']),
                                         self.rule['slideblock']['name'])

        # slideblock_src = slideblock.get_attribute('src')
        slidebkg_src = slidebkg.get_attribute('src')

        slideblock_style = slideblock.get_attribute('style')
        # slidebkg_style = slidebkg.get_attribute('style')

        # slideblock_imgpath = 'tmp/slideblock_src.png'
        slidebkg_imgpath = 'tmp/slidebkg.jpeg'

        # 下载图片
        debug('开始下载验证码图片')
        logging.debug(slidebkg_src)
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        sess = requests.Session()
        headers = {
            'User-Agent': choice(AGENTS_ALL),
        }
        sess.headers = headers
        # r = sess.get(self.HOST + slideblock_src, timeout=self.timeout)
        # with open(slideblock_imgpath, 'wb') as f:
        #     f.write(r.content)
        download_url = self.HOST + slidebkg_src if not slidebkg_src.startswith('http') else slidebkg_src
        r = sess.get(download_url, timeout=self.timeout)
        with open(slidebkg_imgpath, 'wb') as f:
            f.write(r.content)
        debug('验证码图片下载完成: {}'.format(slidebkg_imgpath))

        # 分析图片
        match = re.findall(r'top: ([\d\.]+)px; left: ([\d\.]+)px', slideblock_style)
        if match:
            top = int(float(match[0][0]))  #
            left = float(match[0][1])  # 滑块相对于背景图的位置
        else:
            top = None
            left = 0
        debug('滑块相对位置: left: {left} top: {top}'.format(left=left, top=top))

        # 计算背景图片大小
        tcaptcha_imgarea = driver.find_element(self.get_by(self.rule['tcaptcha-imgarea']['type']),
                                               self.rule['tcaptcha-imgarea']['name'])
        tcaptcha_imgarea_style = tcaptcha_imgarea.get_attribute('style')

        match = re.findall(r'width: ([\d\.]+)px; height: ([\d\.]+)px', tcaptcha_imgarea_style)
        if match:
            resize = (int(match[0][0]), int(match[0][1]))
        else:
            resize = None
        debug('开始查找验证码缺口位置')
        dark_left, dark_top = find_most_dark_part(slidebkg_imgpath, 55, 55, top=top, resize=resize)
        debug('缺口位置: left: {left} top: {top}'.format(left=dark_left, top=dark_top))

        distance = dark_left - left  # 需要移动的距离

        # 开始移动图片
        driver = self.drag_captcha(driver, distance)
        debug('滑动解锁完成')
        return driver

    def drag_captcha(self, driver, distance):
        '''
        拖拽验证码
        :param driver: 
        :param distance: 
        :return: 
        '''
        debug(u'开始拖拽: 距离{}'.format(distance))
        distance = float(distance)
        tcaptcha_drag_button = driver.find_element(self.get_by(self.rule['tcaptcha_drag_button']['type']),
                                                   self.rule['tcaptcha_drag_button']['name'])
        location = tcaptcha_drag_button.location
        action = ActionChains(driver)
        # TODO delete 拖拽前挪动鼠标
        for _ in range(10):
            action.move_by_offset(random(), random()).perform()
            action.reset_actions()
            time.sleep(random())

        action.move_to_element(tcaptcha_drag_button)
        action.click_and_hold(tcaptcha_drag_button).perform()
        action.reset_actions()
        if distance < 0:
            debug('拖拽距离为负数, 重新随机赋值')
            distance = randint(50, 200)
        # TODO 尝试多重拖动,更像人为
        ########## 1.方案1
        # distance_left = distance
        # n = 100
        # for _ in range(n):
        #     _offset = random()
        #     print('移动: {}'.format(_offset))
        #     distance_left -= _offset
        #     direction = 1 if random() < 0.5 else -1
        #     action.move_by_offset(_offset, random() * direction).pause(random()).perform()
        # action.move_by_offset(distance_left, 0).pause(1).release()
        ########### 2.方案2 根据录制的轨迹
        # moves = read_mouse_trace('mouse_trace.rms')
        # last_one = False
        # for _m in iter(moves):
        #     x, y, delay = _m
        #     if distance - x > 0:
        #         move_to_right = x
        #         distance -= x
        #     else:
        #         move_to_right = distance
        #         last_one = True
        #     action.move_by_offset(move_to_right, y).perform()
        #     time.sleep(delay)
        #     debug('移动: {} {} delay: {}'.format(move_to_right, y, delay))
        #     action.reset_actions()
        #     if last_one:
        #         break
        ########### 3.方案3 缩放录制的轨迹
        # moves = read_mouse_trace('mouse_trace.rms')
        # total_move = moves[-1][0]
        # ratio = float(distance) / total_move
        # last_x = last_y = 0
        # for _m in iter(moves):
        #     x, y, delay = _m
        #     _x, _y, delay = (x - last_x) * ratio, (y - last_y) * ratio, delay * ratio
        #     last_x, last_y = x, y
        #     action.move_by_offset(_x, _y).perform()
        #     time.sleep(delay)
        #     debug('移动: {} {} delay: {}'.format(_x, _y, delay))
        #     action.reset_actions()
        ########## 4.方案4 先加速后减速
        tracks = get_track(distance)
        print(sum(tracks))
        for x in tracks:
            action.move_by_offset(xoffset=x, yoffset=randint(-1, 1)).perform()
            action.reset_actions()
            # time.sleep(0.1)

        action.release().perform()
        action.reset_actions()
        # action.perform()
        # 验证码提示
        # tcaptcha_note = driver.find_elements(self.get_by(BY_CLASS), 'tcaptcha-title')
        # if len(tcaptcha_note) > 0:
        #     tcaptcha_note = tcaptcha_note[0]
        #     debug('验证码提示: {}'.format(tcaptcha_note.text))
        #     # TODO 验证码失败
        time.sleep(self.interval_time)
        debug(u'完成拖拽')
        return driver

    def is_login_success(self, driver):
        # switch to main
        # id = loginNickName
        # 转到登录用iframe
        # driver.switch_to.default_content()
        # driver.switch_to.frame(driver.find_element(self.get_by(self.rule['login_frame']['type']),
        #                                            self.rule['login_frame']['name']))
        # error_tips = driver.find_element(self.get_by(self.rule['show_error']['type']),
        #                                  self.rule['show_error']['name'])
        # if error_tips.is_displayed():
        #     debug('错误信息状态为显示')
        #     error_msg = error_tips.find_element(self.get_by(BY_ID), 'err_m').text
        #     debug('登录失败, 错误信息: {}'.format(error_msg))
        #     return False
        time.sleep(self.interval_time)
        # TODO delete
        # root = etree.HTML(driver.page_source)
        # with open('captcha.html', 'w') as f:
        #     f.write(driver.page_source)
        # captcha_error_tips = root.xpath('//*[@id="tcaptcha_window"]/div[2]/p/text()')
        # captcha_error_tips = ''.join(captcha_error_tips)
        # if '拖动下方滑块完成拼图' in captcha_error_tips:
        #     debug('滑块解锁失败')
        #     return False
        tcaptcha_title = driver.find_elements(self.get_by(BY_CLASS), 'tcaptcha-title')
        if len(tcaptcha_title) > 0:
            print('错误信息： {}'.format(tcaptcha_title[0].text))

        driver.switch_to.default_content()
        loginnickname = driver.find_elements(self.get_by(self.rule['show_success']['type']),
                                             self.rule['show_success']['name'])
        driver.save_screenshot('判断是否登录成功.png')
        if len(loginnickname) > 0:
            loginnickname = loginnickname[0]
            nickname = loginnickname.get_attribute('value')
            debug('登录成功: {}'.format(nickname))
            return True
        else:
            debug('登录失败')
            # TODO 失败信息
            # 转到登录用iframe
            driver.switch_to.frame(driver.find_element(self.get_by(self.rule['login_frame']['type']),
                                                       self.rule['login_frame']['name']))
            err_m = driver.find_elements(self.get_by(BY_ID), 'err_m')
            if len(err_m) > 0:
                print('错误信息: {}'.format(err_m[0].text))
            # root = etree.HTML(driver.page_source)
            # with open('test.html', 'w') as f:
            #     f.write(driver.page_source)
            # captcha_error_tips = root.xpath('//*[@id="tcaptcha_window"]/div[2]/p/text()')
            # print(''.join(captcha_error_tips))
            # login_error_tips = root.xpath('//*[@id="err_m"]/text()')
            # print(''.join(login_error_tips + captcha_error_tips))
            return False

    # TODO delete for test
    def init_driver(self, proxy=None):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
        # dcap["phantomjs.page.settings.userAgent"] = (generate_user_agent(os=('linux', 'mac')))
        dcap["phantomjs.page.settings.userAgent"] = (choice(AGENTS_ALL))
        # 不载入图片，爬页面速度会快很多
        # dcap["phantomjs.page.settings.loadImages"] = False
        try:
            chrome_driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')
            if not os.path.exists(chrome_driver_path):
                chrome_driver_path = 'chromedriver'
        except Exception as e:
            chrome_driver_path = 'chromedriver'
            debug(e)
        if proxy:
            # self.proxy = self._get_proxy()
            debug(encode_info(u'使用代理IP: {}'.format(proxy)))
            service_args = [
                '--proxy={proxy}'.format(proxy=proxy),
                '--proxy-type=http',
            ]
        else:
            service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=any']
        driver = webdriver.Chrome(
            chrome_driver_path,
            service_args=service_args,
            # desired_capabilities=dcap,
        )

        # 隐式等待5秒，可以自己调节
        driver.implicitly_wait(5)
        return driver

    def search_info(self, cookies):
        sess = requests.Session()
        sess.cookies.update(dict([(i['name'], i['value']) for i in cookies]))
        sess.headers = {
            'User-Agent': choice(AGENTS_ALL),
        }
        self.search_qbbalance(sess)
        # TODO 默认当天
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        self.search_trade_history(sess, start_date=today, end_date=today)

    def search_qbbalance(self, sess):
        t = round(random(), 17)
        url_qbbalance = 'https://my.pay.qq.com/cgi-bin/personal/' \
                        'balance_query_sortflow.cgi?items=qd,qb&_={t}'.format(t=t)
        r = sess.get(url_qbbalance, timeout=self.timeout)
        j = r.json()
        logging.debug(j)
        if j['resultcode'] == 0:
            qb_balance = j['resultinfo']['qb_balance']
            qd_balance = j['resultinfo']['qd_balance']
            line = 'Q币: {}  Q点: {}'.format(qb_balance, qd_balance)
            debug(line)
            self.write_oneline(line)
            return qb_balance, qd_balance
        else:
            # TODO
            print(j)
            line = 'Q币,Q点, 查询失败'
            self.write_oneline(line)

    def search_trade_history(self, sess, start_date, end_date, page=1):
        t = round(random(), 17)
        url_trade_history = 'https://my.pay.qq.com/cgi-bin/personal/' \
                            'account_tradeinfo.cgi?coin_type=0&' \
                            'start_date={start_date}&end_date={end_date}&page_no={page}&' \
                            'channel=all&per=50&extcode=&t={t}'.format(start_date=start_date,
                                                                       end_date=end_date,
                                                                       page=page,
                                                                       t=t)
        r = sess.get(url_trade_history, timeout=self.timeout)
        j = r.json()
        logging.debug(j)
        if j['resultcode'] == 0:
            count = j['resultinfo']['count']
            pageno = j['resultinfo']['pageno']
            trade_history = j['resultinfo']['list']
            for trade in trade_history:
                print(trade)
                line = '----'.join(trade)
                self.write_oneline(line)
        else:
            # TODO
            print(j)
            line = 'Q币,Q点明细查询失败'
            self.write_oneline(line)

    def _save_cookies(self, username, cookies):
        debug('保存cookies: {}'.format(username))
        self.cookies_history[username] = cookies
        # TODO 写入文件
        with open(self.cf.get('main', 'cookie_file'), 'w') as f:
            f.write(json.dumps(self.cookies_history))

    def _read_cookies(self):
        try:
            debug('读取cookie文件')
            with open(self.cf.get('main', 'cookie_file'), 'r') as f:
                self.cookies_history = json.loads(f.read())
        except Exception as e:
            debug('读取cookie文件失败')
            debug(e)

    @staticmethod
    def is_cookies_expired(user_cookies):
        debug('判断cookie是否过期')
        return int(time.time()) > min([ck['expiry'] for ck in user_cookies if 'expiry' in ck])


if __name__ == "__main__":
    # top = 25
    # result = find_most_dark_part('test.jpeg', 105, 105)
    # print(result)
    qqpay = QQPay()
    # ip_port = '121.61.81.205:7671'
    success = False
    count = 0
    # while not success and count < 20:
    #     # ip_port, expire_time = qqpay._fetch_proxy()
    #     # print(ip_port, expire_time)
    #     count += 1
    #     try:
    #         qqpay.search_by_one_account(username_password, proxy=None)
    #         success = True
    #     except Exception as e:
    #         print(e)
    # ip_port, expire_time = qqpay._fetch_proxy()
    # print(ip_port, expire_time)
    # qqpay.search_by_one_account(username_password, proxy=None)

    # print(read_mouse_trace('mouse_trace.rms'))
    qqpay.run()
