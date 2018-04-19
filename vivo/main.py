import logging

import time
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import operator
from vivo import get_balance

from MainWindow import Ui_MainWindow

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='log.log',
                    filemode='w')
"""
选择输入文件
开始
查看结果输出
记录日志
"""


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        # 一些参数
        root_path = os.path.dirname(os.path.abspath(__file__))
        self.input_data_path = default_input_data_path = os.path.join(root_path, 'input.txt')

        # 设置默认值
        self.textEdit.setText(default_input_data_path)

        # 绑定事件
        self.btn_start.pressed.connect(self.start_search_balance)
        self.btn_select.pressed.connect(self.showDialog)

        self.show()

    def start_search_balance(self):
        # 重置
        self.progressBar.setValue(0)
        self.textBrowser.append('-'*40)
        self.textBrowser.append('')

        starttime = time.time()
        # 读取内容
        with open(self.input_data_path, 'rb') as f:
            lines = f.readlines()
        self.lines = [line.strip() for line in lines if line.strip()]
        self.total = len(self.lines)
        count = 0
        results = []
        for line in self.lines:
            count += 1
            line = line.decode('gbk')
            username, password = line.split('---')
            self.textBrowser.append('开始查询: {}, 第{}个'.format(username, count))
            QApplication.processEvents()
            # 开始查询
            ret = get_balance(username, password)
            balance = ret['balance']
            userTicketBalance = ret['userTicketBalance']
            results.append([username, balance, userTicketBalance])
            # 更新显示
            self.textBrowser.append('余额:{}, 礼券余额:{}'.format(balance, userTicketBalance))
            self.progressBar.setValue(count * 100.0 / self.total)
            QApplication.processEvents()

        self.textBrowser.append('开始导出结果到 output.txt')
        QApplication.processEvents()
        # 导出文件
        with open('output.txt', 'w') as f:
            for r in results:
                f.write('用户名:{}, 余额:{}, 礼券余额: {}\r\n'.format(*r))
        self.textBrowser.append('完成! 用时: {}s'.format(time.time() - starttime))

    def showDialog(self):
        self.input_data_path, _ = QFileDialog.getOpenFileName(self, '选择文件', './')
        if self.input_data_path:
            self.textEdit.setText(self.input_data_path)
        else:
            self.textBrowser.append('请选择文件!!!')


if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("Vivo")

    window = MainWindow()
    app.exec_()
