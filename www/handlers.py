#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-22
import hashlib
import re
import time
import json
from aiohttp import web
from www.apis import APIValueError, APIError
from www.config import configs
from www.coroweb import get, post
from www.models import User, Blog, next_id

__author__ = 'Devin -- http://zhangchuzhao.site'
COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def user2cookie(user, max_age):
    """
    Generate cookie str by user.
    """
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    cookie_info_list = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(cookie_info_list)


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


@post('/api/users')
async def api_register_user(*, name, email, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passswd')
    users = User.findall('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '*' * 6
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r
























