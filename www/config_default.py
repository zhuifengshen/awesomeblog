#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-22
__author__ = 'Devin -- http://zhangchuzhao.site'


"""
Default configurations，即本地开发配置
由于Python本身语法简单，完全可以直接用Python源代码来实现配置，而不需要再解析一个单独的.properties或者.yaml等配置文件
"""

configs = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'devin',
        'password': 'devin',
        'db': 'awesome'
    },
    'session': {
        'secret': 'Awesome'
    }
}
