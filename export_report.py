# encoding: utf-8
import json
import logging
import os
from collections import Counter

import datetime
from lxml import etree
import chardet
import requests
import sys

import time

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='log.log',
                    filemode='w')


class FuckException(Exception): pass


class LoginException(Exception): pass


class CanNotFindGameException(Exception): pass


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


###############################

class ExportReport(object):
    def __init__(self):
        # settings
        self.interval_time = 2
        self.timeout = 10
        self.length = 50
        self.search_before_days = 0
        self.separator = '----'
        self.preset_filename = 'data.txt'
        self.result_filename = 'result.txt'
        self.preset_data_dict = {}  # 预设的字典
        self.search_result = {}  # 查询的结果
        self.game_dict = {}  # 游戏名称和id字典
        self.failed_list = []  # 失败的列表
        self.username = ''
        self.password = ''
        #
        self.headers = {
            'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Host': 'tcoin.52tt.com',
        }
        self.init_sess()
        # url
        self.url_login = 'http://tcoin.52tt.com/tcoin/login'
        self.url_detail = 'http://tcoin.52tt.com/tcoin/admin/details/vouchers.shtml'  # 玩家账号明细
        self.url_api_detail = 'http://tcoin.52tt.com/tcoin//admin/details/listVouchers.shtml'  # 查询玩家明细接口
        self.url_dist_html = 'http://tcoin.52tt.com/tcoin/admin/dist/single/voucherDist.shtml'  # 分发页面

    def init_sess(self):
        self.sess = requests.Session()
        self.sess.headers = self.headers

    def settings(self):
        # interval_time = raw_input(encode_info(u'请输入间隔时间(默认2s): ')) or 2
        # self.interval_time = int(interval_time)
        search_before_days = raw_input(encode_info(u'请输入需要查询多少天前至今的数据(默认:0 即当天): ')) or 0
        self.search_before_days = int(search_before_days)

        WELCOME = u'''
            导入账号列表的文件格式:
                用户名:密码:游戏1
                账号1{separator}预设1
                账号2{separator}预设2
                账号3{separator}预设3
                
                用户名:密码:游戏2
                账号1{separator}预设1
                账号2{separator}预设2
                账号3{separator}预设3
        '''.format(separator=self.separator)
        print(encode_info(WELCOME))
        self.preset_filename = raw_input(encode_info(u'请输入导入账号列表的文件名称(默认: data.txt): ')) or u'data.txt'

    def read_preset_data(self):
        '''
        {
            'username:password': {
                                    'gamename' : {'account': counter},
                                    'gamename' : {'account': counter},
                                }
        }
        :return: 
        '''

        def expect_amount_to_counter(expect):
            result = []
            parts = expect.split('+')
            for part in parts:
                tmp = part.split('*')
                num = 1
                if len(tmp) > 1:
                    num = tmp[1]
                result.extend([int(tmp[0])] * int(num))
            return Counter(result)

        debug(encode_info(u'开始读取账号列表: %r' % self.preset_filename))
        if not os.path.exists(self.preset_filename):
            raise FuckException(encode_info(u'文件不存在'))
        lines = bom_read(self.preset_filename)
        last_username_password = ''
        gamename = ''
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if len(line.split(':')) == 3:  # 是账号密码和游戏
                _tmp = line.split(':')
                last_username_password = ':'.join(_tmp[:2])
                gamename = _tmp[-1]
                continue
            tmp = line.split(self.separator)
            if len(tmp) != 2:
                raise_error(encode_info(u'账号密码书写格式错误: %r' % tmp))
            # gamename = tmp[0].strip()
            account = tmp[0].strip()
            expect_amount = tmp[1].strip()
            if last_username_password not in self.preset_data_dict:
                self.preset_data_dict[last_username_password] = {}

            if gamename not in self.preset_data_dict[last_username_password]:
                self.preset_data_dict[last_username_password][gamename] = {}

            self.preset_data_dict[last_username_password][gamename][account] = expect_amount_to_counter(expect_amount)

        logging.debug(json.dumps(self.preset_data_dict, indent=4))

    def login(self, username, password):
        debug(encode_info(u'=== 开始登录 %r ===' % username))
        try:
            data = {
                'username': username,
                'password': password,
            }
            r = self.sess.post(self.url_login, data=data, timeout=10)
            r.encoding = 'utf-8'
            cookies = self.sess.cookies.get_dict()
            # cookies 中不存在_amount
            if '_amount' not in cookies:
                # if u"库存列表" not in r.text:
                logging.error(u'登录失败: %r ;%r' % (username, password))
                raise LoginException(encode_info(u'登录失败: %r ;%r' % (username, password)))
            debug(encode_info(u'=== 开始成功 %r ===' % username))
        except Exception as e:
            raise LoginException(e)

    def get_game_dict(self):
        '''
        :return: {'gametile':value}
        '''
        debug(encode_info(u'开始获取游戏id字典'))
        self.game_dict = {}
        r = self.sess.get(self.url_dist_html, timeout=10)
        r.encoding = 'utf-8'
        root = etree.HTML(r.text)
        options = root.xpath('//select[@id="gameId"]/option')
        for option in options:
            value = option.xpath('@value')
            title = option.text
            value = value[0] if value else ''
            if not value:
                logging.error("can not find value: %r" % title)
                raise FuckException(encode_info(u"找不到数值: %r" % title))
            if title in self.game_dict.keys():
                debug(encode_info(u'保存过: %r' % title))
            self.game_dict[title] = value

        if self.game_dict:
            logging.debug(encode_info(u'游戏id字典'))
            logging.debug(json.dumps(self.game_dict, indent=4))
            return True
        else:
            raise_error(encode_info(u'获取游戏id字典失败'))

    def search_onepage(self, gameid, operation, startdate, enddate, start=0):
        params = {
            'draw': 1,
            'order': 'true',
            'start': start,
            'length': self.length,
            'search': '',
            'startDate': startdate,
            'endDate': enddate,
            'effectiveDate': '',
            'expiryDate': '',
            'accountName': '',
            'mobile': '',
            'type': operation,
            'gameId': gameid,
            'invUid': '',
            '_': int(time.time() * 1000),
        }
        r = self.sess.get(self.url_api_detail, params=params, timeout=self.timeout)
        response = json.loads(r.text)
        return response

    def search_by_game(self, gameid, operation, startdate, enddate):  # 查询一个游戏
        debug(encode_info(u'开始获取数据'))
        search_result = []
        start = 0
        hasNextPage = True
        index = 1
        while hasNextPage:
            debug(encode_info(u'开始获取第 %r 页开始的记录' % index))
            response = self.search_onepage(gameid, operation, startdate, enddate, start=start)
            logging.debug(json.dumps(response, indent=4))
            # 处理数据
            totalcount = response['totalCount']  # 全部记录数量
            hasNextPage = response['hasNextPage']  # 是否有下一页
            totalPages = response['totalPages']  # 全部页数
            page = response['page']  # 当前页码
            nextPage = response['nextPage']  # 下一页页码
            endRow = response['endRow']  # 数据结束行数
            startRow = response['startRow']  # 数据开始行数

            items = response['items']
            search_result.extend(items)

            start = endRow  # 下次查询的起点
            index += 1
            time.sleep(self.interval_time)
            debug(encode_info(u'当前 %s 条记录' % (int(endRow - startRow + 1))))

        debug(encode_info(u'结束获取数据'))
        return search_result

    def search_by_presetdata(self, username_password):  # 根据游戏名搜索所有结果
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=int(self.search_before_days))
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        for gamename in self.preset_data_dict[username_password].keys():
            try:
                debug(encode_info(u'=== 开始搜索游戏: %s ====' % gamename))
                gameid = self.game_dict.get(gamename, '')
                if not gameid:
                    raise_error(encode_info(u'字典中找不到游戏id: %s' % gamename))
                # 获取游戏所有记录
                search_result = self.search_by_game(gameid, '使用', start_date, end_date)
                # 清空历史数据
                self.search_result = {}
                # 分析记录
                self.analyze_data(search_result)
                # 对比记录
                self.contrast(username_password, gamename)

                debug(encode_info(u'=== 结束游戏: %s ====' % gamename))
            except Exception as e:
                debug(str(e))
                self.failed_list.append(gamename)
                # 结果写上失败
                error_msg = e.message
                try:
                    encoding = chardet.detect(error_msg)['encoding']
                    error_msg = error_msg.decode(encoding)
                except Exception as ex:
                    print(ex)
                    error_msg = ''

                self.write_result_oneline(
                    self.separator.join((gamename, u'失败', error_msg)))

    def analyze_data(self, items):  # 分析查询结果，转化格式为字典
        debug(encode_info(u'开始分析数据'))
        for item in items:
            amount = item['spendingAmount']  # 账号操作的面值
            accountName = item['accountName']  # 账号
            gameName = item['gameName']  # 游戏名
            if gameName not in self.search_result:
                self.search_result[gameName] = {}
            if accountName not in self.search_result[gameName]:
                self.search_result[gameName][accountName] = []

            self.search_result[gameName][accountName].append(int(amount))
        debug(encode_info(u'结束分析数据'))
        logging.debug(json.dumps(self.search_result, indent=4))

    @staticmethod
    def counter2str(c):  # 将counter转化为string
        return ' + '.join([' * '.join((str(k), str(v))) for k, v in c.iteritems()])

    def write_result_oneline(self, line):
        debug(encode_info(u'写入: %s' % line))
        with open(self.result_filename, 'a') as f:
            f.write(encode_info(line + '\n'))

    def write_result_lines(self, lines):
        with open(self.result_filename, 'a') as f:
            for line in lines:
                f.write(encode_info(line + '\n'))
                debug(encode_info(u'写入: %s' % line))

    def contrast(self, username_password, gamename=None):  # 对比结果和预设
        debug(encode_info(u'开始对比: %s' % gamename))
        lines_tobe_write = []  # 最后需要写入的行
        if gamename:
            result = self.search_result.get(gamename, {})
            preset = self.preset_data_dict[username_password][gamename]
            account_list = preset.keys()
            for account, counter in preset.iteritems():
                preset_account_value = preset[account]
                result_account_value = result.get(account, [])
                if not result_account_value:
                    line_list = [gamename, account, self.counter2str(counter), u'没有结果', u'异常']
                else:
                    result_acocunt_counter = Counter(result_account_value)

                    line_list = [gamename, account, self.counter2str(counter),
                                 self.counter2str(result_acocunt_counter)]

                    if result_acocunt_counter != preset_account_value:
                        line_list.extend([u'异常', u'结果不对'])

                line = self.separator.join(line_list)

                # self.write_result_oneline(line)
                lines_tobe_write.append(line)
        # 排序，并写入所有的行，异常的在上面
        lines_tobe_write_sorted = sorted(lines_tobe_write, key=lambda x: len(x.split(self.separator)), reverse=True)
        self.write_result_lines(lines_tobe_write_sorted)
        debug(encode_info(u'对比结束: %s' % gamename))

    def run(self):
        self.settings()

        self.read_preset_data()
        # 根据预设的游戏查询
        # 查询结果对比预设的账号金额
        for username_password, v_dict in self.preset_data_dict.iteritems():
            try:
                tmp = username_password.split(':')
                username = tmp[0]
                password = tmp[1]
                self.login(username, password)
                # 登录完成后写入账号密码
                self.write_result_oneline(username_password)
                self.get_game_dict()  # 获取游戏id字典

                self.search_by_presetdata(username_password)
            except LoginException as ex:
                debug(ex)
                self.write_result_oneline(encode_info('----'.join((username_password, u'登录失败'))))
            except Exception as ex:
                debug(ex)

        raw_input(encode_info(u'回车结束'))


if __name__ == '__main__':
    e = ExportReport()
    e.run()
