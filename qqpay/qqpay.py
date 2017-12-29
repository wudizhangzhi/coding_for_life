from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
import requests
from PIL import Image, ImageChops
import numpy as np
from functools import reduce

from base.base import BasePhantomjs, CaptchaException

'''
1. login 
2. get captcha
3. find the most dark part of image (pixel minimum)
4. calulate distance
'''


def test():
    captcha_host = 'https://ssl.captcha.qq.com'
    img_src = '/cap_union_new_getcapbysig?aid=11000101&asig=&captype=&protocol=https&clientype=2&disturblevel=&apptype=2&curenv=inner&ua=TW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTJfNikgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzYzLjAuMzIzOS44NCBTYWZhcmkvNTM3LjM2&sess=Y_7QXmMLYX-WwBM5UDOUaI3B8LAHXFl9ZgJBAlpGUVbNhHzoaC3XH1I4g5ehveoU11WryRCFwlk-MH5cF5DX6jVnOOE5882p1TZutMxoCIEpuPw4K3PljEJq_38EW6i5HL9bJ1G2ODe81e3oDuakgTEQEfvGlbSz2ZqN2pTC7janyvioDDe1yKY-rGa9yLERYlbEoUF78Aw*&theme=&noBorder=noborder&fb=1&showtype=embed&uid=2634107307&cap_cd=e47nVG9E4yIIJAxgpNW0p4hNC2bSdvtWDhKYGSVS-9tI02agv4MEPw**&lang=2052&rnd=517436&rand=0.38466088829802203&vsig=c01nvV5FE7Sq-SzTid6ZVngNltf91_7K2B4yY5kvDo5KKmna46LmcYzouENZsgq2IQg4af0ISk_vLi2RXELlCFv2B1WPiIFgdETaWAJ_Q-CWj_KM9xT6EonMkTDdzxdFY3AbjpPBww_idavFcbidIs-btMNIP8TZet2TqDl37siQrvx4OTWxlaLdQ**&img_index=2'

    img_whole_src = '/cap_union_new_getcapbysig?aid=11000101&asig=&captype=&protocol=https&clientype=2&disturblevel=&apptype=2&curenv=inner&ua=TW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTJfNikgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzYzLjAuMzIzOS44NCBTYWZhcmkvNTM3LjM2&sess=Y_7QXmMLYX-WwBM5UDOUaI3B8LAHXFl9ZgJBAlpGUVbNhHzoaC3XH1I4g5ehveoU11WryRCFwlk-MH5cF5DX6jVnOOE5882p1TZutMxoCIEpuPw4K3PljEJq_38EW6i5HL9bJ1G2ODe81e3oDuakgTEQEfvGlbSz2ZqN2pTC7janyvioDDe1yKY-rGa9yLERYlbEoUF78Aw*&theme=&noBorder=noborder&fb=1&showtype=embed&uid=2634107307&cap_cd=e47nVG9E4yIIJAxgpNW0p4hNC2bSdvtWDhKYGSVS-9tI02agv4MEPw**&lang=2052&rnd=517436&rand=0.38466088829802203&vsig=c01nvV5FE7Sq-SzTid6ZVngNltf91_7K2B4yY5kvDo5KKmna46LmcYzouENZsgq2IQg4af0ISk_vLi2RXELlCFv2B1WPiIFgdETaWAJ_Q-CWj_KM9xT6EonMkTDdzxdFY3AbjpPBww_idavFcbidIs-btMNIP8TZet2TqDl37siQrvx4OTWxlaLdQ**&img_index=1'

    # TODO 如何对比相似度
    captcha = Image.open('qq_captcha.png').resize((55, 55))
    # captcha = captcha.convert('RGB')
    width, height = captcha.size
    print(captcha.getbands(), width, height)

    captcha_whole = Image.open('qq_capthca_whole.jpeg').resize((280, 158))
    print(captcha_whole.getbands())
    captcha_whole = captcha_whole.convert('.'.join(captcha.getbands()))
    # top = 15
    # right = 485
    top = 3
    left = 200
    for _left in range(55, 280):
        captcha_whole_croped = captcha_whole.crop((_left, top, _left + width, top + height))

        img3 = ImageChops.difference(captcha, captcha_whole_croped)
        pixel = img3.getdata()
        threshold = 100  # 最大差距
        pixel_array = np.array(pixel).reshape((width, height))
        # if np.sum(abs(np.diag(pixel_array))) < threshold:
        #     print('相似! left: {}'.format(_left))
        #     captcha_whole_croped.show()
        #     # img3.show()
        #     break
        result = hamming(avhash(captcha_whole_croped), avhash(captcha))
        if result < 20:
            print(result)
            captcha_whole_croped.show()
        # if _left == 200:  # 4832
        #     # print(np.sum(abs(np.diag(pixel_array))))
        #     # captcha_whole_croped.show()
        #     result = hamming(avhash(captcha_whole_croped), avhash(captcha))
        #     print(result)
        #     break
    else:
        print('未找到相似位置')


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


def find_most_dark_part(img, w=None, h=None, top=None):
    '''
    找到图像灰度最小(最黑)的区域
    :param img: 图像
    :param w: 区域宽度
    :param h: 区域高度
    :param top: top距离
    :return:
    '''
    if not isinstance(img, Image.Image):  # 判断参数im，是不是Image类的一个参数
        img = Image.open(img)
    img = img.convert('L')
    width, height = img.size
    max_dark_value = float('inf')
    max_dark_img = None
    print(width, height)
    matrix = np.matrix(img.getdata()).reshape((height, width))  # (行, 列)
    for i in range(width - w):
        if top:
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
    if max_dark_img:
        left, top = max_dark_img
        # img_croped = img.crop((left, top, left + w, top + h))
        # img_croped.show()
        Image.fromarray(matrix[top:top + w, left:left + h].astype(np.uint8)).show()
    return max_dark_img


class QQPay(BasePhantomjs):

    def __init__(self):
        super(QQPay, self).__init__()

        self.use_proxy = self.cf.get('main', 'proxy')

    def run(self):
        # TODO
        self.read_preset_data()

        while not self.upq.empty():
            need_proxy = False
            username_password = self.upq.get_nowait()

            if need_proxy:
                proxy = self.get_proxy()
            else:
                proxy = None
            try:
                search_result = self.search_by_one_account(username_password, proxy=proxy)
            except CaptchaException as e:
                pass

            except Exception as e:
                pass

            self.write_oneline(search_result)

    def search_by_one_account(self, username_password, proxy):
        separator = self.cf.get('main', 'separator')

        tmp = username_password.split(separator)

        username = tmp[0]
        password = tmp[1]

        driver = self.login(username, password, proxy=proxy)
        if self.is_need_scroll_capthca(driver):
            self.scroll_capthca(driver)






if __name__ == "__main__":
    # test()
    result = find_most_dark_part('qq_capthca_whole.jpeg', 105, 105, top=25)
    print(result)
