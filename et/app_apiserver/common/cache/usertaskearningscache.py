import json
from flask import g, current_app
from redis import RedisError
from utils.mysql_cli import MysqlSearch
from cache import constants
from utils.constants import ET_MEMBER_EARNINGS,TASKS_TABLE,ET_TASK_ORDERS

class UserTaskEarningsCache(object):
    """用户个人任务收益缓存"""
    def __init__(self):
        self.user_task_earnings_key = 'user_task_earnings_:{}'.format(g.user_id)

    def save(self, user_task_earnings):
        """设置用户个人任务收益缓存"""
        try:
            rc = current_app.redis_cli
            rc.lpush(self.user_task_earnings_key, json.dumps(user_task_earnings))
            rc.expire(self.user_task_earnings_key, constants.UserTaskEarningsCacheTTl.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """获取用户个人收益缓存"""
        rc = current_app.redis_cli
        try:
            rc = current_app.redis_cli
            user_tasks = rc.lrange(self.user_task_earnings_key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            user_tasks = None
        if user_tasks:
            return json.loads(user_tasks[0].decode())
        else:
            try:
                user_task_earnings = []
                # 获取个人任务收益内容
                res_list = MysqlSearch().get_more(f"SELECT et.task_order_id,et.task_id,et.amounts,et.add_time,t.name from \
                                        (SELECT * FROM {ET_MEMBER_EARNINGS} where member_id='{g.user_id}' ) as et \
                                        LEFT JOIN {TASKS_TABLE} as t on t.id=et.task_id;")
                for res in res_list:
                    user_task_earnings.append({
                        '任务名称': res['name'],
                        '流水号': res['task_order_id'],
                        '收益': res['amounts'],
                        '提交日期': res['add_time'].strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                current_app.logger.error(e)
                return False
        if user_task_earnings:
            self.save(user_task_earnings)
            return user_task_earnings
        else:
            return False