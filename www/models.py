#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-5-18
import time
import uuid

from www.orm import Model, StringField, BooleanField, FloatField, TextField

__author__ = 'Devin -- http://zhangchuzhao.site'


def next_id():
    """
    根据时间戳生产唯一id
    """
    return '%015d%s000' % (int(time.time()*1000), uuid.uuid4().hex)


class User(Model):
    """
    用户映射模型
    """
    __table__ = 'users'
    id = StringField(primary_key=True, default=next_id)
    email = StringField()
    passwd = StringField()
    admin = BooleanField()
    name = StringField()
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)


class Blog(Model):
    """
    博客映射模型
    """
    __table__ = 'blogs'
    id = StringField(primary_key=True, default=next_id)
    user_id = StringField()
    user_name = StringField()
    user_image = StringField(ddl='varchar(500)')
    name = StringField()
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    """
    评论映射模型
    """
    __table__ = 'comments'
    id = StringField(primary_key=True, default=next_id)
    blog_id = StringField()
    user_id = StringField()
    user_name = StringField()
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)
