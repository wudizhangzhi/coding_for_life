# encoding: utf-8

from ConfigParser import ConfigParser
import os

cf = ConfigParser()
assert os.path.exists('config.ini'), u'配置文件不存在'
cf.read('config.ini')