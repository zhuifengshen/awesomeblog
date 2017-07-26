#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-22
import re
import time

from www.config import configs
from www.coroweb import get
from www.models import User, Blog

__author__ = 'Devin -- http://zhangchuzhao.site'
COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret



@get('/')
async def index(request):
    summary1 = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    summary2 = '目前包含web服务器、决策采样器、Python解释器、爬虫、模板引擎、OCR持续集成系统、分布式系统、静态检查等内容'
    summary3 = '实现一个高性能网络爬虫，它能够抓取你指定的网站的全部地址'
    blogs = [
        Blog(id='1', name='Welcome awesome blog', summary=summary1, created_at=time.time()),
        Blog(id='2', name='Pythonic idea', summary=summary2, created_at=time.time() - 3600),
        Blog(id='3', name='小米5x，重磅来袭', summary=summary3, created_at=time.time() - 7200),

    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }


# @get('/api/users')
# async def api_get_users():
#     users = await User.findall()
#     for u in users:
#         u.passwd = '*'*6
#     return dict(users=users)


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')