import json
from flask import current_app,g
from redis.exceptions import RedisError

from cache import constants
from utils.constants import ET_MEMBER_EARNINGS,TASKS_TABLE
from utils.mysql_cli import MysqlSearch

class UserEarningsCache(object):
    """用户个人收益缓存"""
    def __init__(self):
        self.user_earnings_key = 'user_earnings:{}'.format(g.user_id)

    def save(self,user_earnings):
        """设置用户个人收益缓存"""
        try:
            rc = current_app.redis_cli
            rc.lpush(self.user_earnings_key, json.dumps(user_earnings))
            rc.expire(self.user_earnings_key, constants.UserEarningsCacheTTL.get_val())
        except RedisError as e:
            print('RedisError:{}'.format(e))

    def get(self):
        """获取用户个人收益缓存"""
        rc = current_app.redis_cli
        try:
            user_earnings = rc.lrange(self.user_earnings_key, 0, -1)
        except RedisError as e:
            print('RedisError:{}'.format(e))
            user_earnings = None
        if user_earnings:
            return json.loads(user_earnings[0].decode())
        else:
            try:
                user_earnings = []
                # 任务id对应的名称
                sql_tasks_name = f"SELECT name FROM {TASKS_TABLE} WHERE id IN (SELECT task_id FROM {ET_MEMBER_EARNINGS} WHERE member_id='{g.user_id}')"
                tasks_name = MysqlSearch().get_more(sql_tasks_name)
                # 用户流水资料
                sql_info = f"SELECT task_order_id,add_time,amounts FROM {ET_MEMBER_EARNINGS} WHERE member_id='{g.user_id}' order by add_time asc;"
                info = MysqlSearch().get_more(sql_info)
                for k, v in zip(tasks_name, info):
                    user_earnings.append({
                        '流水号':v['task_order_id'],
                        '任务名称':k['name'],
                        '完成时间':v['add_time'].strftime("%Y-%m-%d-%H-%M-%S"),
                        '奖励金额':v['amounts'] / 100
                    })
            except Exception as e:
                current_app.logger.error(e)
            if user_earnings:
                user_list = user_earnings.sort(reverse=True)
                self.save(user_list)
                return user_list
            else:
                return False
