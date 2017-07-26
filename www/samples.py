#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 17-5-20
import asyncio
from www.models import User
from www.orm import create_pool, close_pool

__author__ = 'Devin -- http://zhangchuzhao.site'


loop = asyncio.get_event_loop()
async def user_demo(loop):
    await create_pool(loop, user='devin', password='devin', db='awesome')
    u = User(name='Devin', email='zhangchuzhao@qq.com', passwd='123456', image='http://pic121.nipic.com/file/20170209/13134720_111306332000_2.jpg')
    await u.save()
    await close_pool()
loop.run_until_complete(user_demo(loop))
loop.close()
