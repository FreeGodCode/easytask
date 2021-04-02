import base64
import json
import time

from flask import current_app,g
from redis.exceptions import RedisError
from cache import constants
from utils.constants import TASKS_TABLE,ET_TASK_ORDERS
from utils.mysql_cli import MysqlSearch
from datetime import datetime

class TasksDetail(object):
    """任务详情缓存"""
    def __init__(self,tasks_id):
        self.tasks_detail_key = 'tasks_detail_:{}'.format(tasks_id)
        self.tasks_id = tasks_id
        self.key = 0
    def save(self,tasks_detail):
        """
        设置任务详情缓存
        :param tasks_detail: 任务详情
        :return:
        """
        try:
            rc = current_app.redis_cli
            # TODO 当redis的key值是detail的情况下redis就会显示为空
            rc.hsetnx(self.tasks_detail_key, self.key, json.dumps(tasks_detail))
            rc.expire(self.tasks_detail_key, constants.TasksDetailCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """
        获取任务详情缓存
        :return:
        """
        rc = current_app.redis_cli
        try:
            tasks_detail = rc.hget(self.tasks_detail_key,self.key)
        except RedisError as e:
            current_app.logger.error(e)
            tasks_detail = None
        if tasks_detail is not None:
            return json.loads(tasks_detail.decode())
        else:
            current_app.logger.info(self.tasks_id)
            # 查询任务详情内容
            sql = f"SELECT task_class,recommend,tags,allow_nums,end_time,task_reward,name,poster_img,task_info,task_steps,virtual_nums,begin_task_time,deadline_time,count_tasks,tasks_counts,check_router FROM {TASKS_TABLE} WHERE ID={self.tasks_id}"
            res = MysqlSearch().get_one(sql)
            # 计算任务剩余数
            tasks_count = res['tasks_counts'] - res['count_tasks']
            # 计算审核时间
            times = str(res['end_time'] - res['begin_task_time']).split(':')
            if len((times[0] + '时' + times[1] + '分').split(',')) > 1:
                audit_time = (times[0] + '时' + times[1] + '分').split(',')[1]
            else:
                audit_time = (times[0] + '时' + times[1] + '分').split(',')[0]
            current_app.logger.info(audit_time)
            tasks_detail = dict()
            tasks_detail['审核时间'] = audit_time
            tasks_detail['任务数量'] = tasks_count
            tasks_detail['开始时间'] = res['begin_task_time'].strftime("%Y-%m-%d-%H-%M-%S")
            tasks_detail['做单时间'] = res['deadline_time']
            tasks_detail['截止时间'] = res['end_time'].strftime("%Y-%m-%d-%H-%M-%S")
            tasks_detail['任务奖励'] = res['task_reward']
            tasks_detail['任务名称'] = res['name']
            tasks_detail['任务头像'] = res['poster_img']
            tasks_detail['任务说明'] = res['task_info']
            tasks_detail['任务步骤'] = res['task_steps']
            tasks_detail['人气'] = res['virtual_nums']
            tasks_detail['标签'] = res['tags']
            tasks_detail['推荐'] = res['recommend']
            tasks_detail['任务类型'] = res['task_class']
            tasks_detail['任务完成数量'] = res['count_tasks'] + int(res['virtual_nums'])
            # 加密二维码链接
            ref_data = 'http://' + '47.113.91.65:5007' + '/share_jump' + f'?td={self.tasks_id}&ref={res["check_router"]}'
            base_url = base64.b64encode(ref_data.encode()).decode()
            tasks_detail['rwmlj'] = base_url
            if tasks_detail:
                self.save(tasks_detail)
                return tasks_detail
            else:
                return False