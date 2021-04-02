import json
from flask import current_app,g
from redis.exceptions import RedisError
from cache import constants
from utils.constants import ET_MEMBER_EXTEND
from utils.mysql_cli import MysqlSearch

class UserExtendCache(object):
    """用户信息扩展缓存"""
    def __init__(self):
        # TODO 要修改id值.调用前要传值
        self.user_extend_key = 'user_extend_id:{}'.format('id')
        self.key = 0

    def save(self,user_extend):
        """设置用户扩展信息缓存"""
        try:
            rc = current_app.redis_cli
            rc.hsetnx(self.user_extend_key, self.key, json.dumps(user_extend))
            rc.expire(self.user_extend_key, constants.UserExtendCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """获取用户扩展信息缓存"""
        rc = current_app.redis_cli
        try:
            user_extend = rc.hget(self.user_extend_key,self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_extend = None
        if user_extend is not None:
            return True
        else:
            return False