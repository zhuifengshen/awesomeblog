#!/usr/bin/env python
# _*_ coding:utf-8 _*_
# create time: 4/23/2017
import logging

import aiomysql

__author__ = 'Devin -- http://zhangchuzhao.site'
__doc__ = 'ORM module'
logging.basicConfig(level=logging.DEBUG)


# 数据库连接池全局变量
__pool = None

async def create_pool(loop, **kwargs):
    """
    创建一个全局的数据库连接池
    """
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        loop=loop,
        host=kwargs.get('host', 'localhost'),
        port=kwargs.get('port', 3306),
        user=kwargs['user'],
        password=kwargs['password'],
        db=kwargs['db'],
        charset=kwargs.get('charset', 'utf8'),  # 注意数据库连接编码不能误写为utf-8
        autocommit=kwargs.get('autocommit', True),
        maxsize=kwargs.get('maxsize', 10),
        minsize=kwargs.get('minsize', 1)
    )

async def close_pool():
    """
    销毁连接池
    :return: 
    """
    global __pool
    if __pool:
        __pool.close()
        await __pool.wait_closed()


def log(sql, args=()):
    """
    输出SQL语句
    """
    logging.debug('SQL: %s, args: %s' % (sql, args))


def create_args_string(num):
    """
    生成SQL语句参数?
    :param num: 参数个数
    :return: ?参数字符串

    >>> create_args_string(4)
    '?,?,?,?'
    """
    return ','.join(['?'] * num)


async def select(sql, args, size=None):
    """
    查询方法
    :param sql: 查询SQL语句 
    :param args: 查询参数
    :param size: 查询行数(可选)
    :return: 查询结果集
    """
    log(sql, args)
    global __pool
    async with __pool.get() as conn:  # async with ????????????????????????????
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned: %s' % len(rs))
        return rs

async def execute(sql, args, autocommit=True):
    """
    更新|插入|删除方法
    :param sql: SQL语句
    :param args: 语句参数
    :param autocommit: 是否自动提交 
    :return: 影响的行数
    """
    log(sql, args)
    async with __pool.get() as conn:
        if not autocommit:
            conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
    return affected


class Field(object):
    """
    字段类型基类
    """
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    """
    字符字段
    """
    def __init__(self, name=None, ddl='varchar(50)', primary_key=False, default=None):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    """
    布尔字段
    """
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):
    """
    整型字段
    """
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
    """
    浮点字段
    """
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    """
    文本字段
    """
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tableName = attrs.get('__table__', None) or name
        logging.info(' found model: %s (table: %s)' % (name, tableName))
        mappings = dict()  # 字典=字段名:字段类型
        fields = []  # # 除主键外的字段名
        primaryKey = None  # 主键名
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info(' found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise Exception('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise Exception('Table(%s) Primary key not found.' % tableName)
        for k in mappings.keys():
            attrs.pop(k)  # 删除字段类属性,避免对字典键对值的干扰(因为实例属性会覆盖类属性）
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))  # 为字段名加上:`字段名`
        attrs['__table__'] = tableName
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        logging.info('\nTable: %s\nPrimaryKey: %s\nFields: %s' % (tableName, primaryKey, fields))
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ','.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ','.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)  # 如果字段名无自定义名称,则使用属性本身变量名
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        logging.info('\nSelect: %s\nInsert: %s\nUpdate: %s\nDelete: %s' % (attrs['__select__'], attrs['__insert__'], attrs['__update__'], attrs['__delete__']))
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    """
    数据库表面向对象映射模型
    1.父类字典dict的键值对对应字段和字段值
    2.元类ModelMetaclass用于在提取模型中的定义的字段和字段类型的映射关系
    """
    def __init__(self, **kwargs):
        """
        调用父类字典初始化方法进行初始化
        """
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, key):
        """
        让字典支持通过x.y取值
        """
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        """
        让字典支持通过x.y = z赋值
        """
        self[key] = value

    def getValue(self, key):
        """
        获取指定键的值
        """
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        """
        获取指定键的值,如果未指定则返回默认值
        """
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def find(cls, pk):
        """
        find object by primary key
        """
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    @classmethod
    async def findall(cls, where=None, args=None, **kwargs):
        """
        find objects by where clause.
        """
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args  = []
        orderBy = kwargs.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kwargs.get('limit', None)
        if limit is not None:
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    # TODO: _num_的意思？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        """
        find number by select and where.
        """
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    async def save(self):
        """
        保存实例数据
        """
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s' % rows)
        else:
            logging.info('success to insert record: affected rows: %s' % rows)

    async def update(self):
        """
        通过主键更新实例数据
        """
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update record: affected rows: %s' % rows)
        else:
            logging.info('success to update record: affected rows: %s' % rows)

    async def remove(self):
        """
        通过主键删除实例数据
        """
        args = [self.getValueOrDefault(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to delete record: affected rows: %s' % rows)
        else:
            logging.info('success to delete record: affected rows: %s' % rows)


# class User(Model):
#     __table__ = 'users'
#     id = IntegerField(primary_key=True)
#     name = StringField()
#
# user = User(id=123, name='Devin')
# print(user.id, ' ', user.name)
# print(dir(User))
# log(user.__insert__, ('Devin', 22))


# if __name__ == '__main__':
    # import doctest
    # doctest.testmod()
