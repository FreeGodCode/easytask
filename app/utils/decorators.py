import json
from flask import g, current_app
from functools import wraps
from cache.user import UserCache
from utils.mysql_cli import MysqlSearch
from utils.constants import ET_MEMBER_WITHDRAWAL
from utils.http_status import HttpStatus

def login_required(func):
    """
    用户必须登录装饰器
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user_id:
            return {'error_code': 3001, 'error': '用户必须登录'}, HttpStatus.OK.value
        else:
            # 判断用户状态
            user_info = UserCache(g.mobile).get()
            if user_info is False:
                return {'error': '请登录'}, HttpStatus.OK.value
            if user_info['status'] == 2:
                return {'error': '用户账户异常.'}, HttpStatus.OK.value
            return func(*args, **kwargs)
    return wrapper

def verify_required(func):
    """
    用户必须实名认证通过装饰器
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user_id:
            return {'error_code': 3001, 'error': '用户必须登录'}, HttpStatus.OK.value
        elif not g.setreal:
            return {'error': '用户必须实名.'}, HttpStatus.OK.value
        else:
            # 判断用户状态
            user_info = UserCache(g.mobile).get()
            if user_info['setreal'] == 2 :
                return {'error': '请实名.'}, HttpStatus.OK.value
            return func(*args, **kwargs)
    return wrapper

def withdrawal(func):
    """
    用户必须提现之后,才能进行领取任务操作
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        r = MysqlSearch().get_one(f"SELECT member_id FROM {ET_MEMBER_WITHDRAWAL} WHERE member_id='{g.user_id}'")
        if not r:
            return {'error': '请完成新手提现任务'},HttpStatus.OK.value
        return func(*args, **kwargs)
    return wrapper

def bind_aliplay(func):
    """
    用户必须绑定支付宝,才能进行提现操作
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        rc = current_app.redis_cli
        res = rc.hget(f"user_center:{g.user_id}", 0)
        if res['支付宝状态'] != 1:
            return {'error': '请绑定支付宝再进行提现操作'}, HttpStatus.OK.value
        return func(*args, **kwargs)
    return wrapper






