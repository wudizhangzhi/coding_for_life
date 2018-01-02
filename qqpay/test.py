# encoding: utf-8
import re
import sys

import requests
from PIL import Image

from qqpay import read_mouse_trace

sys.path.append("..")
import os
from random import choice

import time
from selenium.webdriver import DesiredCapabilities, ActionChains
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities

from base.agents import AGENTS_ALL
import random
import numpy as np


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


def drag(driver):
    driver.switch_to.frame(driver.find_element_by_xpath('//*[@id="newVcodeIframe"]/iframe'))

    # 等待元素出现
    slidebkg = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, 'slideBkg'))
    )

    slideblock = driver.find_element(By.ID, 'slideBlock')

    # slideblock_src = slideblock.get_attribute('src')
    slidebkg_src = slidebkg.get_attribute('src')

    slideblock_style = slideblock.get_attribute('style')
    # slidebkg_style = slidebkg.get_attribute('style')

    # slideblock_imgpath = 'tmp/slideblock_src.png'
    slidebkg_imgpath = 'tmp/slidebkg.jpeg'

    # 下载图片
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
    download_url = 'https://ssl.captcha.qq.com' + slidebkg_src if not slidebkg_src.startswith('http') else slidebkg_src
    r = sess.get(download_url, timeout=10)
    with open(slidebkg_imgpath, 'wb') as f:
        f.write(r.content)

    # 分析图片
    match = re.findall(r'top: ([\d\.]+)px; left: ([\d\.]+)px', slideblock_style)
    if match:
        top = int(float(match[0][0]))  #
        left = float(match[0][1])  # 滑块相对于背景图的位置
    else:
        top = None
        left = 0

    # 计算背景图片大小
    tcaptcha_imgarea = driver.find_element(By.CLASS_NAME, 'tcaptcha-imgarea')
    tcaptcha_imgarea_style = tcaptcha_imgarea.get_attribute('style')

    match = re.findall(r'width: ([\d\.]+)px; height: ([\d\.]+)px', tcaptcha_imgarea_style)
    if match:
        resize = (int(match[0][0]), int(match[0][1]))
    else:
        resize = None
    dark_left, dark_top = find_most_dark_part(slidebkg_imgpath, 55, 55, top=top, resize=resize)

    distance = dark_left - left  # 需要移动的距离

    # 开始移动图片
    distance = float(distance)
    tcaptcha_drag_button = driver.find_element(By.ID, 'tcaptcha_drag_button')
    location = tcaptcha_drag_button.location
    action = ActionChains(driver)
    # TODO delete 拖拽前挪动鼠标
    for _ in range(10):
        action.move_by_offset(random.random(), random.random()).perform()
        action.reset_actions()
        time.sleep(random.random())

    action.move_to_element(tcaptcha_drag_button)
    action.click_and_hold(tcaptcha_drag_button).perform()
    action.reset_actions()
    if distance < 0:
        distance = random.randint(50, 200)
    ## TODO 故意错一次
    # action.move_by_offset(50, 2).perform()
    # action.reset_actions()
    # time.sleep(0.5)
    # action.release().perform()
    # time.sleep(2)


    action.move_to_element(tcaptcha_drag_button)
    action.click_and_hold(tcaptcha_drag_button).perform()
    action.reset_actions()
    ########### 3.方案3 缩放录制的轨迹
    # moves = read_mouse_trace('drag.rms')
    # total_move = moves[-1][0]
    # ratio = float(distance) / total_move
    # last_x = last_y = 0
    # for _m in iter(moves):
    #     x, y, delay = _m
    #     _x, _y, delay = (x - last_x) * ratio, (y - last_y) * ratio, delay * ratio
    #     last_x, last_y = x, y
    #     action.move_by_offset(_x, _y).perform()
    #     time.sleep(delay)
    #     action.reset_actions()
    tracks = get_track(distance)
    for x in tracks:
        action.move_by_offset(xoffset=x, yoffset=random.randint(-1, 1)).perform()
        action.reset_actions()
        # time.sleep(0.2)

    action.release().perform()
    action.reset_actions()


def test():
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
    service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=any']
    driver = webdriver.Chrome(
        chrome_driver_path,
        service_args=service_args,
        # desired_capabilities=dcap,
    )

    # 隐式等待5秒，可以自己调节
    driver.implicitly_wait(5)

    driver.set_page_load_timeout(60)
    driver.set_window_size(1366, 942)
    driver.get('https://pay.qq.com/')
    driver.delete_all_cookies()

    btn_login = driver.find_element(By.ID, 'login')
    btn_login.click()

    # 转到登录用iframe
    driver.switch_to.frame(driver.find_element(By.ID, 'login_frame'))
    time.sleep(2)
    # 等待元素出现
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, 'switcher_plogin'))
    )
    element.click()

    # TODO 是否等在元素出现
    input_username = driver.find_element(By.ID, 'u')
    input_username.clear()
    input_username.send_keys(username)
    time.sleep(3)

    input_password = driver.find_element(By.ID, 'p')
    input_password.click()
    input_password.clear()
    input_password.send_keys(Keys.HOME)
    # for k in list(password):
    #     input_password.send_keys(k)
    #     time.sleep(random.random())
    input_password.send_keys(password)
    time.sleep(5)
    # 登录
    input_submit = driver.find_element(By.ID, 'login_button')
    input_submit.click()
    time.sleep(3)
    ##### 检测验证码
    drag(driver)


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
        # 加入轨迹
        track.append(round(move))
    # if distance - current != 0:
    #     track.append(distance - current)
    return track

if __name__ == '__main__':
    test()
    time.sleep(100)
