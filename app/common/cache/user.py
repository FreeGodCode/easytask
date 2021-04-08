import json
from flask import current_app
from redis.exceptions import RedisError
# from cache import constants
from app.common.cache import constants
from utils.constants import MEMBERS_TABLE
from utils.mysql_cli import MysqlSearch


class UserCache(object):
    """用户缓存"""
    def __init__(self, mobile):
        self.user_info_key = 'user_info_:{}'.format(mobile)
        self.mobile = mobile
        self.key = 0

    def save(self, user_info):
        """
        设置用户状态缓存
        """
        try:
            rc = current_app.redis_cli
            rc.hsetnx(self.user_info_key, self.key, json.dumps(user_info))
            rc.expire(self.user_info_key, constants.UserInfoCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """
        获取用户状态
        :return:
        """
        rc = current_app.redis_cli
        try:
            user_info = current_app.redis_cli.hget(self.user_info_key, self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_info = None
        if user_info is not None:
            return json.loads(user_info.decode())
        else:
            try:
                sql = f"SELECT * FROM {MEMBERS_TABLE} WHERE mobile='{self.mobile}'"
                user_data = MysqlSearch().get_one(sql)
                user_info = dict()
                for k, v in user_data.items():
                    if k == "reg_time" or k == "logout_time":
                        continue
                    user_info[k] = v
            except Exception as e:
                current_app.logger.error(e)
            if user_info:
                self.save(user_info)
                return user_info
            else:
                return False
