import json
from flask import current_app
from redis import RedisError
from cache import constants
from utils.constants import TASKS_TABLE,ET_TASK_ORDERS
from utils.mysql_cli import MysqlSearch
import datetime

class UserTasks(object):
    """用户任务缓存"""
    def __init__(self,user_id):
        self.user_tasks_key = 'user_tasks_:{}'.format(user_id)
        self.user_id = user_id
        self.key = 0

    def save(self, user_tasks):
        """设置用户任务缓存"""
        try:
            rc = current_app.redis_cli
            rc.lpush(self.user_tasks_key, json.dumps(user_tasks))
            rc.expire(self.user_tasks_key, constants.UserTasksCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """获取用户任务缓存"""
        rc = current_app.redis_cli
        try:
            rc = current_app.redis_cli
            user_tasks = rc.lrange(self.user_tasks_key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            user_tasks = None
        if user_tasks:
            return json.loads(user_tasks[0].decode())
        else:
            try:
                user_tasks = []
                # sql_order = f"select id,task_reward,poster_img,name,end_time from {TASKS_TABLE} where id in (select task_id from {ET_TASK_ORDERS} WHERE member_id='{self.user_id}')"
                # res_list = MysqlSearch().get_more(sql_order)
                # sql_tasks = f"SELECT `status`,add_time,task_id FROM {ET_TASK_ORDERS} WHERE member_id='{self.user_id}';"
                # tasks_list = MysqlSearch().get_more(sql_tasks)
                member_all_task = MysqlSearch().get_more(f"SELECT tt.id,tt.task_reward,tt.poster_img,tt.name,tt.end_time,ett.`status`,ett.add_time,ett.verify_log FROM {TASKS_TABLE} as tt \
				                                                LEFT JOIN {ET_TASK_ORDERS} as ett on ett.task_id=tt.id where member_id='{self.user_id}' \
				                                                    ORDER BY ett.`status` DESC LIMIT 0,100;")
                now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for k in member_all_task:
                    if k["end_time"].strftime("%Y-%m-%d %H:%M:%S") > now_time:
                        continue
                    user_tasks.append({
                        '任务id': k['id'],
                        '用户id': self.user_id,
                        '任务名称': k['name'],
                        '任务奖励': k['task_reward'],
                        '任务头像': k['poster_img'],
                        '任务截止时间': k['end_time'].strftime("%Y-%m-%d %H:%M:%S"),
                        '用户提交时间': k['add_time'].strftime("%Y-%m-%d %H:%M:%S"),
                        '任务状态': k['status'],
                        '审核提示': k['verify_log'],
                    })
            except Exception as e:
                current_app.logger.error(e)
            if user_tasks:
                sor_user_task_list = sorted(user_tasks, key=lambda e: e.__getitem__('用户提交时间'), reverse=True)
                self.save(sor_user_task_list)
                return user_tasks
            else:
                return False




