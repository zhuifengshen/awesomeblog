#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-5-20
import functools
import inspect

import asyncio

import logging
import os
from urllib import parse
from aiohttp import web
from www.apis import APIError


__author__ = 'Devin -- http://zhangchuzhao.site'
__doc__ = 'Web框架的设计是完全从使用者出发，目的是让使用者编写尽可能少的代码'


def get(path):
    """
    define decorator @get('/path')
    把一个函数映射为一个URL处理函数，并附带了URL信息
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path):
    """
    define decorator @post('path')
    把一个函数映射为一个URL处理函数，并附带了URL信息
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator


def get_required_kw_args(fn):
    """
    获取必传的关键字参数（必须且无默认值）
    """
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
        return tuple(args)


def get_named_kw_args(fn):
    """
    获取有名称的关键字参数（包括有默认值的）
    """
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_named_kw_args(fn):
    """
    判断函数是否包含有名称的关键字参数
    """
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


def has_var_kw_arg(fn):
    """
    判断函数是否包含无名称关键字参数(即 **kw)
    """
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_request_arg(fn):
    """
    判断函数是否包含'request'参数且其后不能为var positional parameter、keword only parameter和var keyword parameter   ===且为最后一个参数（或者在可变参数和关键字参数之前）
    """
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.king != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found


class RequestHandler(object):
    """
    RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数，然后把结果转换为web.Response对象。这样，就完全符号aiohttp框架的要求！
    """
    def __init__(self, app, fn):
        self._app = app
        self._func =fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):  # aiohttp框架都会将request对象传给URL处理函数
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:  # URL处理函数中存在关键字参数，则从请求中获取
            if request.method == 'POST':  # POST请求中获取
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':  # GET请求中获取
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:  # 如果不存在var keyword parameter，则 remvoe all unamed kw
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in naned arg and kw args: %s' % k)
                kw[k] = v
        # some URL handler function need the request object
        if self._has_request_arg:
            kw['request'] = request
        # check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        try:
            result = await self._func(**kw)
            return result
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
    """
    添加静态资源文件夹
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


def add_route(app, fn):
    """
    注册URL处理函数
    """
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if method is None or path is None:
        raise ValueError('@get or @post not define in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)  # URL处理函数封装为coroutine
    app.router.add_route(method, path, RequestHandler(app, fn))  # 通过RequestHandler把所有URL处理函数统一封装起来调用，同时巧妙利用了__call__()的实现
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))


def add_routes(app, module_name):
    """
    批量注册模块里所有的URL处理函数
    """
    n = module_name.rfind('.')
    if n == -1:
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)










