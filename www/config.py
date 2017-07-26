#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-7-22
from www import config_default

__author__ = 'Devin -- http://zhangchuzhao.site'


class Dict(dict):
    """
    Simple dict but support access as x.y style.
    """
    def __init__(self, names=(), values=(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def merge(defaults, override):
    """
    递归合并两个字典对象
    :param defaults: 默认字典对象，拥有默认所有的配置项
    :param override: 更新的字典对象，拥有默认配置项的新值
    :return: 合并后的字典对象
    """
    result = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                result[k] = merge(v, override[k])
            else:
                result[k] = override[k]
        else:
            result[k] = defaults[k]
    return result


def toDict(d):
    D = Dict()
    for k, v in d.items():
        # if isinstance(v, dict):
        #     D[k] = toDict(v)
        # else:
        #     D[k] = v
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D


# 自动配置线上环境实现方案
configs = config_default.configs  # 读取配置文件
try:
    import config_override
    configs = merge(configs, config_override.configs)  # 如果存在config_override配置文件，则合并
except ImportError:
    pass
configs = toDict(configs)
