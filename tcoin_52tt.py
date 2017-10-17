# coding=utf8

"""
http://tcoin.52tt.com/tcoin/login.shtml
用于自动登录批量分配

read_preset_data -> select one account
login ->  get_balance -> get_game_list -> dist_values

账号字典
{
    'account1': [['game1', 'account1', 'par', 'count'], ['game1', 'account1', 'par', 'count'],],
}
"""
import copy
import requests
import time
import datetime
import os
from lxml import etree
import json
import logging
import chardet
from collections import OrderedDict

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='log.log',
                    filemode='w')


class FuckWangzhijianError(Exception): pass


FORMAT = u"""
    data.txt文件请以下列格式书写, 并另存为utf8格式:
    
    用户名1：密码1：支付密码1
    游戏名1----账户1----面值----数量
    游戏名2----账户2----面值----数量
    
    用户名2：密码2：支付密码2
    游戏名3----账户3----面值----数量
""".encode('gbk')


class Wangzhijian:
    def __init__(self):

        self.headers = {
            'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Host': 'tcoin.52tt.com',
        }
        self.init_sess()
        # url
        self.url_login = 'http://tcoin.52tt.com/tcoin/login'
        self.url_balance = 'http://tcoin.52tt.com/tcoin/admin/pa/getBalance.shtml?_=%s'
        self.url_dist_html = 'http://tcoin.52tt.com/tcoin/admin/dist/single/voucherDist.shtml'  # 分发页面
        self.url_valid = 'http://tcoin.52tt.com/tcoin/admin/dist/rest/single/validAccount.shtml'  # 验证是否有效,返回一些信息
        self.url_checkbalance = 'http://tcoin.52tt.com/tcoin/admin/dist/rest/single/checkBalanceD.shtml?v='  # 验证余额
        self.url_dist_post = 'http://tcoin.52tt.com/tcoin/admin/dist/single/distVouchers.shtml?token=be37cdf5-2369-4950-8b4d-6a0ca9936075'  # 分发金额
        self.HOST = 'http://tcoin.52tt.com'
        #
        self.last_success = None
        self.last_username_password_paypwd = None
        self.success_list = []

    def init_sess(self):
        self.sess = requests.Session()
        self.sess.headers = self.headers

    def detect_charset(self, text):
        try:
            self.CHARSET = chardet.detect(text)['encoding']
        except Exception as e:
            self.CHARSET = 'utf-8'
            print(e)
        logging.debug(self.CHARSET)

    # def read_preset_data(self, filename):
    #     '''
    #     {'account:password': ['line1','line2', 'line3']}
    #     :param filename:
    #     :return:
    #     '''
    #     self.account_dict = OrderedDict()
    #     if not os.path.exists(filename):
    #         raise FuckWangzhijianError('no file exists!')
    #     with open(filename, 'rb') as f:
    #         content = f.readlines()
    #         self.content = copy.deepcopy(content)
    #         logging.debug(json.dumps(self.content, indent=4))
    #         f.seek(0)
    #         self.detect_charset(f.read())
    #     tmp_list = []
    #     while content:
    #         line = content.pop(0)
    #         if not line.strip() or not content:
    #             if line.strip():
    #                 tmp_list.append(line)
    #             if len(tmp_list) == 1:
    #                 raise FuckWangzhijianError('account set no game : %r' % tmp_list[0])
    #             elif len(tmp_list) > 0:
    #                 # save tmp
    #                 if tmp_list[0] in self.account_dict.keys():
    #                     raise FuckWangzhijianError('duplicate %r' % tmp_list[0])
    #                 self.account_dict[tmp_list[0]] = tmp_list[1:]
    #             # reset tmp_list
    #             tmp_list = []
    #         else:
    #             tmp_list.append(line)
    #
    #             print(self.account_dict)

    def login(self, username, password):
        print('=== start login %r ===' % username)
        logging.debug('=== start login %r ===' % username)
        data = {
            'username': username,
            'password': password,
        }
        r = self.sess.post(self.url_login, data=data, timeout=10)
        r.encoding = 'utf-8'
        if u"库存列表" not in r.text:
            logging.error('login failure: %r ;%r' % (username, password))
            raise FuckWangzhijianError('login failure: %r ;%r' % (username, password))
            # with open('test.html', 'w') as f:
            #     f.write(r.content)

    def get_game_dict(self):
        '''
        :return: {'gametile':value}
        '''
        self.game_dict = {}
        r = self.sess.get(self.url_dist_html, timeout=10)
        r.encoding = 'utf-8'
        root = etree.HTML(r.text)
        options = root.xpath('//select[@id="gameId"]/option')
        for option in options:
            value = option.xpath('@value')
            title = option.text
            # print(title.encode('utf8'))
            value = value[0] if value else ''
            if not value:
                logging.error("can not find value: %r" % title)
                raise FuckWangzhijianError("can not find value", title)
            if title in self.game_dict.keys():
                print('already saved game', title)
            self.game_dict[title] = value

        # 获取form post 地址
        form = root.xpath('//form[@id="SUBMIT_FORM"]')
        if not form:
            raise FuckWangzhijianError('can not find form!')
        form = form[0]
        self.action_url = form.xpath('@action')[0]  # 分发用的地址
        # self.uidStr = root.xpath('//input[@id="uidStr"]/@value')[0]
        # self.discount = root.xpath('//input[@id="discount"]/@value')[0]
        # self.balance = root.xpath('//input[@id="balance"]/@value')[0]

        if self.game_dict:
            return True
        else:
            return False

    def get_uid_and_so_on(self, account, gameId):
        #     {"balance":17.92,"uids":[45988370],"validedAccounts":["59809567"],"discount":0.43}
        print('--- get info ---')
        data = {
            'accounts': account,
            'gameId': gameId,
        }
        r = self.sess.post(self.url_valid, data=data, timeout=10)
        logging.debug('get_uid_and_so_on: %r' % r.text)
        j = json.loads(r.text)
        self.balance = j.get('balance', None)
        self.uids = j.get('uids', None)
        self.discount = j.get('discount', None)
        self.validedAccounts = j.get('validedAccounts', None)
        if not (self.uids and self.validedAccounts):
            logging.error('game account does not valid:%r, gameid:%r' % (account, gameId))
            raise FuckWangzhijianError('game account does not valid:%r, gameid:%r' % (account, gameId))
        self.uids = self.uids[0]
        logging.debug('uid: %r' % self.uids)
        logging.debug('discount: %r' % self.discount)
        logging.debug('balance: %r' % self.balance)

    def dist_values(self, username, paypwd, gamename, gameid, account, par, count):
        '''
        gameId:207705240
        accounts:59809567
        gameName:去吧皮卡丘-tx【安卓】
        balance:17.92
        discount:0.43
        uidStr:45988370
        validedAccounts:59809567
        counts[0].createAmount:1
        counts[0].createVouchersCount:1
        counts[0].costTcoin:0.43
        effectiveDate:2017-10-13
        expiryDate:2017-11-12
        comment:15951910150
        payPwd:51573872
        :param game: 
        :param par: 
        :param count: 
        :return: 
        '''
        print('--- start distribute %r , par:%r, count:%r ---' % (gamename, par, count))
        logging.debug('--- start distribute %r , par:%r, count:%r ---' % (gamename, par, count))
        url_dist = self.HOST + self.action_url if self.action_url.startswith('/') else '/' + self.action_url
        effectiveDate = datetime.datetime.today()
        expiryDate = effectiveDate + datetime.timedelta(days=30)
        data = {
            'gameId': gameid,
            'accounts': account,
            'gameName': gamename,
            'balance': self.balance,
            'discount': self.discount,
            'uidStr': self.uids,
            'validedAccounts': account,
            'counts[0].createAmount': par,
            'counts[0].createVouchersCount': count,
            'counts[0].costTcoin': self.discount,
            'effectiveDate': effectiveDate.strftime('%Y-%m-%d'),
            'expiryDate': expiryDate.strftime('%Y-%m-%d'),
            'comment': username,
            'payPwd': paypwd,
        }
        r = self.sess.post(url_dist, data=data, timeout=10)
        r.encoding = 'utf-8'
        if u"alert('密码错误')" in r.text:
            logging.error('paypwd is wrong:%r' % paypwd)
            raise FuckWangzhijianError('paypwd is wrong:%r' % paypwd)
        elif u"条件查询" in r.text:
            print('success:%r %r %r %r %r' % (username, gamename, account, par, count))
            logging.debug('success:%r %r %r %r %r' % (username, gamename, account, par, count))
        else:
            logging.error('unknow error occured!save response html to dist_result.html')
            with open('dist_result.html', 'w') as f:
                f.write(r.content)
            raise FuckWangzhijianError('unknow error occured!save response html to dist_result.html')

    def update_game_list(self, gamelist):
        '''
        返回更新后的游戏列表
        :param gamelists: 输入设定好的一个账号内的 游戏名----账号----金额----数量 列表
        :return: [['game_v', 'account', 'par', 'count', 'game_title'],]
        '''
        tmplist = gamelist.split('----')
        game_title = tmplist[0].strip()
        game_account = tmplist[1].strip()
        game_par = tmplist[2].strip()
        par_count = tmplist[3].strip()
        game_value = None
        _game_title = None
        # search for game value
        # self.game_dict 是网络获取的游戏名称字典
        # gamelist 是文件写的游戏名称
        for title, v in self.game_dict.iteritems():
            game_title_encoder = game_title.decode(self.CHARSET)
            if game_title_encoder in title:
                game_value = v
                _game_title = title
                break
        if not game_value:
            logging.error('can not find game value: %r' % game_title)

            raise FuckWangzhijianError('can not find game value: %r' % game_title)
        return [game_value, game_account, game_par, par_count, _game_title]

    # def writer_data_left(self):
    #     '''
    #     # TODO
    #     :return:
    #     '''
    #     try:
    #         if self.last_username_password_paypwd is None:
    #             index_username = 0
    #         else:
    #             index_username = self.content.index(self.last_username_password_paypwd)
    #         if self.last_success is None:
    #             index_game = -1
    #         else:
    #             index_game = self.content[index_username:].index(self.last_success)
    #         logging.error('index_username: %r' % index_username)
    #         logging.error('index_game: %r' % index_game)
    #         with open('data_left.txt', 'w') as f:
    #             f.write(self.last_username_password_paypwd)
    #             for line in self.content[index_username:][index_game + 1:]:
    #                 f.write(line)
    #     except Exception as e:
    #         logging.error(e)
    #     print('!!! occur err,saved left data in data_left.txt !!!')
    #     logging.error('last username line: %r' % self.last_username_password_paypwd)
    #     logging.error('last game line: %r' % self.last_success)
    #     print('last username line: %r' % self.last_username_password_paypwd)
    #     print('last game line: %r' % self.last_success)
    #
    # def write_data_success(self):
    #     try:
    #         with open('data_success.txt', 'w') as f:
    #             index = 0
    #             for line in self.success_list:
    #                 if '----' not in line and index != 0:
    #                     f.write('\r\n')
    #                 f.write(line)
    #                 index += 1
    #         print('!!! occur err,saved success data in data_success.txt !!!')
    #         logging.error('!!! occur err,saved success data in data_success.txt !!!')
    #         logging.error('last username line: %r' % self.last_username_password_paypwd)
    #         logging.error('last game line: %r' % self.last_success)
    #     except Exception as e:
    #         logging.error(e)
    #         print(e)
    #
    # def main(self, filename):
    #     now = time.time()
    #     logging.debug('******** start running ********')
    #     try:
    #         self.read_preset_data(filename)
    #         for username_password_paypwd, gamelists in self.account_dict.iteritems():
    #             # init
    #             tmp = username_password_paypwd.split(':')
    #             username = tmp[0].strip()
    #             password = tmp[1].strip()
    #             paypwd = tmp[2].strip()
    #             logging.debug('username:%r' % username)
    #             logging.debug('password:%r' % password)
    #             logging.debug('paypwd:%r' % paypwd)
    #             logging.debug(gamelists)
    #
    #             self.last_username_password_paypwd = username_password_paypwd
    #             self.success_list.append(username_password_paypwd)
    #             # login
    #             self.login(username, password)
    #
    #             for gamelist in gamelists:
    #                 # get game list
    #                 self.get_game_dict()
    #                 logging.debug(self.game_dict)
    #                 _new_game_list = self.update_game_list(gamelist)
    #                 logging.debug('_new_game_list: %r' % _new_game_list)
    #                 game_id = _new_game_list[0]
    #                 game_account = _new_game_list[1]
    #                 par = _new_game_list[2]
    #                 par_count = _new_game_list[3]
    #                 game_title = _new_game_list[4]
    #                 # 获取数据
    #                 self.get_uid_and_so_on(game_account, game_id)
    #                 # 判断余额是否足够
    #                 if float(self.balance) < (float(par) * float(par_count)):
    #                     logging.debug('balance not enough')
    #                     raise FuckWangzhijianError('balance not enough')
    #
    #                 # 开始分发
    #                 self.dist_values(username, paypwd, game_title, game_id, game_account, par, par_count)
    #
    #                 # 记录最后一次成功的记录
    #                 self.last_success = gamelist
    #                 self.success_list.append(gamelist)
    #
    #             print('=== end username:%r ===' % username)
    #     except Exception as e:
    #         # 记录在哪
    #         # 里失败的，保存内容
    #         logging.error(self.content)
    #         logging.error(e)
    #         # self.writer_data_left()
    #         self.write_data_success()
    #         raise e
    #     logging.info('******** end: duration:%s ********' % (time.time() - now))
    #     # print('******** end: duration:%s ********' % (time.time() - now))
    #
    # def run(self):
    #     print(FORMAT)
    #     filename = raw_input(u"please type in filename(default: data.txt): ") or 'data.txt'
    #     try:
    #         self.main(filename)
    #     except Exception as e:
    #         print(e)
    #     raw_input(u"结束！按回车按钮结束！".encode('gbk'))

    def write_data_left_v2(self):
        with open('data_left.txt', 'w') as f:
            if self.last_username_password_paypwd is not None and self.last_username_password_paypwd != self.content[self.content_index]:
                f.write(self.last_username_password_paypwd)
            for line in self.content[self.content_index:]:
                f.write(line)
        print('!!! occur err,saved left data in data_left.txt !!!')
        logging.error('last username line: %r' % self.last_username_password_paypwd)
        logging.error('last game line: %r' % self.last_success)

    def read_preset_data_v2(self, filename):
        with open(filename, 'rb') as f:
            content = f.readlines()
            self.content = copy.deepcopy(content)
            logging.debug(json.dumps(self.content, indent=4))
            f.seek(0)
            self.detect_charset(f.read())
            return content

    def main_v2(self, filename):
        now = time.time()
        logging.debug('******** start running ********')

        content = self.read_preset_data_v2(filename)
        self.content_index = 0
        try:
            while len(content) > 0:
                line = content.pop(0)  # 取一行
                if not line.strip():
                    continue

                elif '----' in line:  # 游戏名1----账户1----面值----数量
                    # 访问网页，获取数据
                    self.get_game_dict()
                    logging.debug(self.game_dict)
                    _new_game_list = self.update_game_list(line.strip())
                    logging.debug('_new_game_list: %r' % _new_game_list)
                    game_id = _new_game_list[0]
                    game_account = _new_game_list[1]
                    par = _new_game_list[2]
                    par_count = _new_game_list[3]
                    game_title = _new_game_list[4]
                    # 获取数据
                    self.get_uid_and_so_on(game_account, game_id)
                    time.sleep(self.interval_time)
                    print('sleep %r' % self.interval_time)
                    # 判断余额是否足够
                    if float(self.balance) < (float(par) * float(par_count) * float(self.discount)):
                        logging.debug('balance not enough: %r' % self.balance)
                        raise FuckWangzhijianError('balance not enough: %r' % self.balance)
                    # 开始分发
                    self.dist_values(self.username, self.paypwd, game_title, game_id, game_account, par, par_count)
                    time.sleep(self.interval_time)
                    print('sleep %r' % self.interval_time)

                elif len(line.split(':')) == 3:  # 账号：密码：支付密码
                    self.last_username_password_paypwd = line
                    # 登录
                    _line = line.strip().split(':')
                    self.username = _line[0].strip()
                    password = _line[1].strip()
                    self.paypwd = _line[2].strip()
                    self.login(self.username, password)
                    time.sleep(self.interval_time)
                    print('sleep %r' % self.interval_time)
                else:
                    raise FuckWangzhijianError('wrong format: %r' % line)
                self.content_index += 1
        except Exception as e:
            self.write_data_left_v2()
            logging.error(e)
            raise e

        logging.info('******** end: duration:%s ********' % (time.time() - now))
        print('******** end: duration:%s ********' % (time.time() - now))

    def run_v2(self):
        print(FORMAT)
        filename = raw_input(u"please type in filename(default: data.txt): ") or 'data.txt'
        self.interval_time = raw_input(u"please type in default interval time(default: 2s)") or 2
        try:
            self.interval_time = int(self.interval_time)
            self.main_v2(filename)
        except Exception as e:
            print(e)
            logging.error(e)
        raw_input(u"结束！按回车按钮结束！".encode('gbk'))


if __name__ == '__main__':
    w = Wangzhijian()
    w.run_v2()
