# encoding: utf-8
from six.moves import input
from random import choice, sample
import time
import datetime
import os
import copy
from collections import Counter

from xlsxwriter import Workbook

"""小根根用分配器"""


class FuckXiaoGenGenError(Exception): pass


def neworder(l):
    new_l = []
    # print(l)
    length = len(l)
    left = right = (length // 3)
    new_l.append(l[left])
    left -= 1
    right += 1
    while left >= 0 or right <= (length - 1):
        if left >= 0:
            new_l.append(l[left])
            left -= 1
        if right <= (length - 1):
            new_l.append(l[right])
            right += 1
    # print(new_l)
    return new_l

class WangZhiJian:
    def __init__(self):

        self.result_list = []

    def distribute_money(self, total_amount, max_per_amount, account_list, par_value_list, mess=10):
        """
        给不同账号分配金额
        :param total_amount: 总金额
        :param max_per_amount: 各个账号最大限额
        :param account_list: 账号列表
        :param par_value_list: 面值列表
        :return: result: 分配字典
        """
        account_list = [i.strip() for i in account_list]
        num_account = len(account_list)
        self.par_value_list = par_value_list
        if not (num_account and par_value_list):
            raise FuckXiaoGenGenError('参数错误')

        # 降序面值，并且转为int
        par_value_list = sorted([int(i) for i in par_value_list], reverse=True)
        # par_value_list = sorted([int(i) for i in par_value_list])
        if par_value_list[0] > total_amount:
            raise FuckXiaoGenGenError('最大面值比总金额大')

        if num_account * par_value_list[-1] > total_amount:
            raise FuckXiaoGenGenError('无法保证每个账号分得金额, 因为 最小面值 * 账号数量 > 总金额')

        if max_per_amount < par_value_list[-1]:
            raise FuckXiaoGenGenError('限额比最小面值还小, 你是傻逼吗?')

        # ##### 新的分配算法 #######
        # TODO new order 从面值的中间开始，往两边发散
        # par_value_list = sample(par_value_list, len(par_value_list))
        par_value_list = neworder(par_value_list)
        # self.balance = total_amount
        min_par = par_value_list[-1]
        # self.count_distribte = 0  # 分配次数

        account_remains = copy.copy(account_list)

        counter_result = []
        max_par = par_value_list[0]
        division = total_amount // max_par

        def test(x, l=None):
            if len(counter_result) > 0:
                return
            if l is None:
                _l = []
            else:
                _l = copy.copy(l)
            if x == 0:
                if sum([k * v for k, v in Counter(_l).items()]) == total_amount:
                    c = Counter(_l)
                    if c not in counter_result:
                        if sum([v for k, v in c.items()]) >= num_account:
                            counter_result.append(c)
                            return
            elif x < min_par:
                return
            else:
                for par in par_value_list:
                    if x - par >= 0:
                        _l.append(par)
                        test(x - par, _l)

        par_max_dict = {par: int(total_amount // par) for par in par_value_list}

        def test2(x, par, l=None):
            # print(x, par, Counter(l))
            if len(counter_result) > 2:
                return
            if l is None:
                _l = []
            else:
                _l = copy.copy(l)
            if x == 0:
                if sum(_l) == total_amount:
                    c = Counter(_l)
                    if c not in counter_result:
                        if sum([v for k, v in c.items()]) >= num_account:
                            counter_result.append(c)
                            return
            elif x < min_par:
                return
            elif x % par == 0 or par == par_value_list[-1]:
                # elif par == par_value_list[-1]:
                if x % par == 0:
                    _l_copy = copy.copy(_l)
                    _l_copy.extend([par] * int(x // par))
                    c = Counter(_l_copy)
                    if c not in counter_result:
                        if sum([v for k, v in c.items()]) >= num_account:
                            counter_result.append(c)
                            return
            else:
                try:
                    par_next = par_value_list[par_value_list.index(par) + 1]
                    for n in xrange(int(x // par), 0, -1):
                        if x - n * par >= 0:
                            _l_copy = copy.copy(_l)
                            _l_copy.extend([par] * n)
                            # print(x - n*par, par_next, Counter(_l_copy), par_value_list.index(par))
                            test2(x - n * par, par_next, _l_copy)
                except Exception as e:
                    print(par_value_list.index(par))

        # for n in xrange(int(division), 0, -1):
        #     if len(counter_result) > 0:
        #         break
        #     balance = total_amount - max_par * n
        #     test(balance, l=[max_par] * n)
        test2(total_amount, max_par)
        if len(counter_result) == 0:
            raise FuckXiaoGenGenError('No result!')

        for c in counter_result:
            print(c, sum([v for k, v in c.items()]))
        return counter_result
        # init result
        # result = {account: [] for account in account_list}
        # counter_result = counter_result[0]
        # counter_par_list = reduce(lambda x, y: x + y, [[k] * v for k, v in counter_result.items()])
        # index = 0
        # while len(counter_par_list) > 0:
        #     account_choose = account_list[index % num_account]
        #     par_pop = counter_par_list.pop()
        #     if sum(result[account_choose]) + par_pop <= max_per_amount:
        #         result[account_choose].append(par_pop)
        #         index += 1
        #     else:
        #         if sum([sum(v) for k, v in counter_par_list]) > max_per_amount * num_account:
        #             raise FuckXiaoGenGenError('error, greater then max_per_amount * num_account')
        #         counter_par_list.append(par_pop)
        # for account in account_list:
        #     result[account] = []

        #
        # # total_amount -  (par1 * x1 + par2 * x2 ...) 最小
        # # x1 + x2 + ... >= num_account
        #
        # # min_distribte = num_account  # 最小分配次数
        # # max_distribte = total_amount / min_par  # 最大分配次数
        # # self.min_balance = total_amount
        # # self.par_value_list = par_value_list
        # # self.step = max_distribte
        # # print('start')
        # # start = time.time()
        # # self.distrite(par_value_list, total_amount, [])
        # # print(self.result_list)
        # # cau = zip(par_value_list, self.result_list)
        # # print(sum([i * j for i, j in cau]))
        # # print(time.time() - start)
        #
        # while len(account_remains) and self.balance > 0:
        #     # 1. 随机取一个账号
        #     random_account = choice(account_remains)
        #     for par in par_value_list:  # 从大到小取面值
        #         if self.balance <= 0:
        #             break
        #         while (sum(result[random_account]) + par <= max_per_amount) and self.balance >= par:  # 如果小于限额, 分配
        #             result[random_account].append(par)
        #             self.balance -= par  # 余额
        #             self.count_distribte += 1  # 分配次数
        #             if sum(result[random_account]) + min_par > max_per_amount:
        #                 account_remains.remove(random_account)
        # #
        # #
        # #
        # # ##### end #####
        # #
        # #
        # # # 首先从最大面值开始尝试给每个账号分配。如果金额和小于总金额，采取这个面额分配
        # # for par in par_value_list:
        # #     if par * num_account < total_amount:
        # #         first_par = par
        # #         break
        # #
        # # # init result
        # # result = {}
        # # for account in account_list:
        # #     result[account] = [first_par]
        # #
        # # account_remains = copy.copy(account_list)  # 剩余可以分配的账号
        # # # 余额
        # # self.balance = total_amount - (first_par * num_account)
        # # min_par = par_value_list[-1]
        # # self.count_distribte = num_account  # 分配次数
        # #
        # # while self.balance > min_par:
        # #     random_par = choice(par_value_list)
        # #     if self.balance - random_par < 0:
        # #         continue
        # #     if not account_remains:  # 没有剩余账号，退出
        # #         break
        # #     random_account = choice(account_remains)
        # #
        # #     random_account_sum_amount = sum(result[random_account])
        # #     if random_account_sum_amount > max_per_amount:  # 账号总额大于限额
        # #         # 删除账号
        # #         account_remains.remove(random_account)
        # #         continue
        # #
        # #     # 分配
        # #     result[random_account].append(random_par)
        # #     self.count_distribte += 1
        # #     self.balance -= random_par
        #
        # # 补救
        # trans_dict = {}
        # if len(account_remains) > 0:
        #     # 随机取一个账户的金额，拆分
        #     # 2000, 1000, 200, 100, 50, 30, 6
        #     num_par = len(par_value_list)
        #     for i in xrange(num_par - 1):
        #         trans_dict[par_value_list[i]] = []
        #         host_par = par_value_list[i]
        #         for j in xrange(i + 1, num_par):
        #             cp1_par = par_value_list[j]
        #             if host_par % cp1_par == 0:  # 如果当前能整除，采用这个拆分方法
        #                 tmp_list = [cp1_par] * (host_par / cp1_par)
        #                 if tmp_list not in trans_dict[host_par]:
        #                     trans_dict[host_par].append(tmp_list)
        #             else:
        #                 pass
        #         pass
        #     pass
        #     account_have_par = [k for k, v in result.items() if len(v) > 0]  # 被分配到钱的账户
        #     can_tans = [k for k, v in trans_dict.items() if len(v) > 0]
        #     while len(account_remains) > 0:
        #         # 随机取一个有钱的账户
        #         random_account = choice(account_have_par)
        #         for par in sorted(result[random_account], reverse=True):
        #             if par in can_tans:
        #                 # 去除
        #                 result[random_account].remove(par)
        #                 # 拆分
        #                 trans_par = copy.copy(choice(trans_dict[par]))
        #                 # 补充一个
        #                 result[random_account].append(trans_par.pop())
        #                 while len(trans_par) > 0:
        #                     trans = trans_par.pop()
        #                     if account_remains:
        #                         a = choice(account_remains)
        #                         account_remains.remove(a)
        #                     else:
        #                         a = choice(account_list)
        #                         if sum(result[a]) + trans > max_per_amount:
        #                             trans_par.append(trans)
        #                             continue
        #
        #                     result[a].append(trans)
        #
        #     # 混乱用
        #     for i in xrange(mess):
        #         # 随机取一个有钱的账户
        #         random_account = choice(account_list)
        #         for _ in xrange(mess):
        #             par = choice(result[random_account])
        #             if par in can_tans:
        #                 if sum(result[random_account]) + par <= max_per_amount:
        #                     # 去除
        #                     result[random_account].remove(par)
        #                     # 拆分
        #                     trans_par = copy.copy(choice(trans_dict[par]))
        #                     # 补充一个
        #                     result[random_account].append(trans_par.pop())
        #                     while len(trans_par) > 0:
        #                         trans = trans_par.pop()
        #                         a = choice(account_list)
        #                         if sum(result[a]) + trans <= max_per_amount:
        #                             result[a].append(trans)
        #                         else:
        #                             trans_par.append(trans)

        return result

    def write_result(self, result):
        print('开始导出')
        # 10月6日15:21
        filename = 'fenpei%s.txt' % datetime.datetime.now().strftime('%m_%d_%H_%M')
        index = 0
        with open(filename, 'w') as f:

            for c in result:
                index += 1
                f.write('方案%s:\n' % index)
            # for k, v in result.items():
                # tmp_counter = Counter(sorted(v, reverse=True))
                # tmp_distribute = ' + '.join([' * '.join([str(par), str(n)]) for par, n in tmp_counter.items()])
                # line = '%s  ----  %s  \n' % (k.strip(), tmp_distribute)
                line = ''
                c_sorted = sorted(c.items(), key=lambda x: x[0], reverse=True)
                line = reduce(lambda x, y: '\n'.join((x, y)), map(lambda x: '----'.join((str(x[0]), str(x[1]))), c_sorted))
                line = line + '\n\n'
                f.write(line)
        print('导出完成:%s' % filename)

    def writer_result_excel(self, result):
        print('开始导出')
        workbook = Workbook('result.xlsx')
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

        worksheet.merge_range(0, 0, 2, 3, u'这里是个标题', title_format)

        width = 4
        worksheet.freeze_panes(4, 1)

        worksheet.set_column(0, 0, width * 1.5)
        worksheet.set_column(1, 1, width * 5)
        worksheet.set_column(2, 2, width * 15)
        worksheet.set_column(3, 3, width * 4)

        worksheet.write(3, 0, u'No.', top_format)
        worksheet.write(3, 1, u'账号', top_format)
        worksheet.write(3, 2, u'分配', top_format)
        worksheet.write(3, 3, u'总额', top_format)

        set_row = 3
        index = 0

        result_list_desc = sorted(result.items(), key=lambda x: sum(x[1]), reverse=True)
        for account, par_list in result_list_desc:
            set_row += 1
            index += 1
            if index % 2 == 0:
                tmp_body_format = body_format
            else:
                tmp_body_format = body_format_t
            worksheet.write(set_row, 0, index, tmp_body_format)
            worksheet.write(set_row, 1, '', tmp_body_format)

            tmp_counter = Counter(sorted(par_list, reverse=True))
            par_content = ' + '.join(
                [' * '.join([str(par), str(tmp_counter[par])]) for par in sorted(set(par_list), reverse=True)])
            worksheet.write(set_row, 2, par_content, tmp_body_format)
            worksheet.write(set_row, 3, sum(par_list), tmp_body_format)

        set_row += 1
        worksheet.merge_range(set_row, 0, set_row, 1, u'总额', title_format)
        worksheet.merge_range(set_row, 2, set_row, 3, self.total_amount, title_format)
        set_row += 1
        worksheet.merge_range(set_row, 0, set_row, 1, u'余额', title_format)
        worksheet.merge_range(set_row, 2, set_row, 3, self.balance, title_format)
        # 面额 分配数量
        set_row += 1
        worksheet.write(set_row, 0, u'No.', top_format)
        worksheet.write(set_row, 1, u'面值', top_format)
        worksheet.write(set_row, 2, u'数量', top_format)
        merge_list = reduce(lambda x, y: x + y, result.values())
        counter = Counter(merge_list)
        index = 0
        for par in self.par_value_list:
            set_row += 1
            index += 1
            count = counter.get(int(par.strip()), 0)
            worksheet.write(set_row, 0, index, body_format)
            worksheet.write(set_row, 1, par.strip(), body_format)
            worksheet.write(set_row, 2, count, body_format)

        workbook.close()
        print('导出完成:result.xlsx')

    def run(self):
        total_amount = input(u"请输入总金额: ".encode('gbk')) or '43942'
        if not total_amount.isdigit():
            raise FuckXiaoGenGenError('请输入数字')
        self.total_amount = float(total_amount)

        max_per_amount = input(u"请每个账号的限额: ".encode('gbk')) or '2000'
        if not max_per_amount.isdigit():
            raise FuckXiaoGenGenError('请输入数字')
        self.max_per_amount = float(max_per_amount)

        account_num = input(u"请输入账号数量: ".encode('gbk')) or '286'
        if not account_num.isdigit():
            raise FuckXiaoGenGenError('请输入数字')
        # if not os.path.exists(account_path):
        #     raise FuckXiaoGenGenError('路径不存在:%s' % account_path)

        par_path = input(u"请输入面额文件的相对路径(默认: par.txt): ".encode('gbk')) or 'par.txt'
        if not os.path.exists(par_path):
            raise FuckXiaoGenGenError('路径不存在:%s' % par_path)

        # with open(account_path, 'r') as file_account:
        #     account_list = file_account.readlines()
        #     account_list = [i for i in account_list if i.strip()]
        account_list = [str(i) for i in xrange(int(account_num))]

        with open(par_path, 'r') as file_par:
            par_value_list = file_par.readlines()
            par_value_list = [i.strip() for i in par_value_list if i.strip()]

        result = self.distribute_money(self.total_amount, self.max_per_amount, account_list, par_value_list)
        self.write_result(result)
        # self.writer_result_excel(result)

    def distrite(self, par_list, amount, history):
        if len(par_list) == 0:
            print('len(par_list) == 0')
            return
        if amount <= 0:
            print('amount <= 0')
            return
        if self.balance == 0:
            print('balance = 0')
            return
        if len(par_list) == 1:
            print('compare', self.balance, amount, par_list)
            tmp_remind = amount % par_list[0]
            tmp_step = (amount + 0.5) // (par_list[0] + 1)
            if tmp_remind <= self.balance and sum(par_list) + tmp_step <= self.step:
                self.balance = tmp_remind
                history.append(amount // par_list[0])
                self.result_list = history
                self.step = tmp_step
                print('min -> %s' % self.min_balance)
                print('result: %s' % str(history))
                print('step: %s' % self.step)
        else:
            tmp_max_par_num = amount // par_list[0]  # 当前面值的最大数量

            for tmp_par_num in xrange(int(tmp_max_par_num) + 1, 0, -1):
                tmp_history = copy.copy(history)
                tmp_balance = amount - tmp_par_num * par_list[0]
                if tmp_balance < 0:
                    continue
                if sum(history) + tmp_par_num >= self.step:
                    continue

                tmp_history.append(tmp_par_num)

                tmp_amount = amount - tmp_par_num * par_list[0]
                print('len > 1', par_list[1:], tmp_amount, tmp_history, self.result_list)
                return self.distrite(par_list[1:], tmp_amount, tmp_history)


if __name__ == '__main__':
    w = WangZhiJian()
    w.run()
