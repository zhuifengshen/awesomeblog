#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-22
import hashlib
import logging
import re
import time
import json
from aiohttp import web

from www import markdown2
from www.apis import APIValueError, APIError, APIPermissionError, Page
from www.config import configs
from www.coroweb import get, post
from www.models import User, Blog, next_id, Comment

__author__ = 'Devin -- http://zhangchuzhao.site'
COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def user2cookie(user, max_age):
    """
    Generate cookie str by user.
    """
    expires = str(int(time.time() + max_age))
    user_info = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    cookie_info_list = [user.id, expires, hashlib.sha1(user_info.encode('utf-8')).hexdigest()]
    return '-'.join(cookie_info_list)


async def cookie2user(cookie_str):
    """
    parse cookie and load user if cookie is valid.
    """
    if not cookie_str:
        return None
    try:
        user_info = cookie_str.split('-')
        if len(user_info) != 3:
            return None
        uid, expires, sha1 = user_info
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '*' * 6
        return user
    except Exception as e:
        logging.exception(e)
        return None


def get_page_index(page):
        p = 1
        try:
            p = int(page)
        except ValueError as e:
            pass
        if p < 1:
            p = 1
        return p


# ********************* Awesome blog URL Handler Function ***********************
# @get('/')
# async def index(request):
#     summary1 = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
#     summary2 = '目前包含web服务器、决策采样器、Python解释器、爬虫、模板引擎、OCR持续集成系统、分布式系统、静态检查等内容。。。'
#     summary3 = '实现一个高性能网络爬虫，它能够抓取你指定的网站的全部地址。。。'
#     blogs = [
#         Blog(id='1', name='Welcome awesome blog', summary=summary1, created_at=time.time()),
#         Blog(id='2', name='Pythonic idea', summary=summary2, created_at=time.time() - 3600),
#         Blog(id='3', name='小米5x，重磅来袭', summary=summary3, created_at=time.time() - 7200),
#
#     ]
#     return {
#         '__template__': 'blogs.html',
#         'blogs': blogs
#     }


@get('/')
async def index(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findall('count(id)')
    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findall(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }


def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


@get('/blog/{id}')
async def get_blog(id):
    """显示指定id的博客内容和所有评论"""
    blog = await Blog.find(id)
    comments = await Comment.findall('blog_id=?', [id], orderBy='created_at desc')  # created_at desc 可能SQL无法识别。。。。。。。。。。。。。。。。。。。。。。。。。
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',  # blog.html是不是自动生产的。。。。。。。。。。。。。。。。。。。。。
        'blog': blog,
        'comments': comments
    }


@get('/manage/blogs')
def manage_blogs(*, page='1'):
    """显示博客管理页面"""
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }


@get('/manage/blogs/create')
def manage_create_blog():
    """
    打开创建新博客编辑界面
    """
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }


@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-delete-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r


# ********************* Awesome blog RESTfull web api ***********************
# @get('/api/users')
# async def api_get_users():
#     users = await User.findall()
#     for u in users:
#         u.passwd = '*'*6
#     return dict(users=users)


@post('/api/authenticate')
async def authenticate(*, email, passwd):
    """
    用户登录验证
    """
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid email.')
    users = await User.findall('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid passwd')
    # authenticate ok, set cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '*'*6
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@post('/api/users')
async def api_register_user(*, name, email, passwd):
    """
    用户注册验证
    """
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passswd')
    users = await User.findall('email=?', [email])
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


@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    """
    获取指定id的博客
    """
    blog = await Blog.find(id)
    return blog


def check_admin(request):
    """
    检测权限
    """
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    """
    创建博客
    """
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not name.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog


@get('/api/blogs')
async def api_blogs(*, page='1'):
    """
    分页显示博客列表
    """
    try:
        page_index = int(page)
    except ValueError as e:
        page_index = 1
    num = await Blog.findall('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findall(orderBy='created_at desc', limit=(p.offset, p.limit))  # limit应用在分页获取上。。。。。。。。。。。。。。。。created_at desc
    return dict(page=p, blogs=blogs)


















