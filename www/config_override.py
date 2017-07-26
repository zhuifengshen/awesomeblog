#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-22
__author__ = 'Devin -- http://zhangchuzhao.site'


"""
Override configurations，即线上部署生产环境配置
当部署线上环境时，通过添加本线上配置，程序自动会更新默认配置，方便快捷
"""

configs = {
    'db': {
        'host': '127.0.0.1'
    }
}
