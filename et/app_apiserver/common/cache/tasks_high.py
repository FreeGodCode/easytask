import datetime
import json
from flask import current_app, g
from redis.exceptions import RedisError
from utils.constants import TASKS_TABLE,ET_GLOBAL_CONFIG, ET_TASK_ORDERS
from utils.mysql_cli import MysqlSearch
from cache import constants

class TasksHighCache(object):
    """任务缓存"""
    def __init__(self):

        self.tasks_info_key = f"tasks_high_info"
        self.key = 0

    def save(self, tasks_info):
        """
        设置任务缓存
        :param tasks_info: 任务列表
        :return:
        """
        try:
            rc = current_app.redis_cli
            rc.hsetnx(self.tasks_info_key, self.key, json.dumps(tasks_info))
            rc.expire(self.tasks_info_key, constants.TasksCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self, page_index, page_size):
        """
        获取任务缓存
        :return:
        """
        rc = current_app.redis_cli
        try:
            tasks_info = rc.hget(self.tasks_info_key,self.key)
        except RedisError as e:
            current_app.logger.error(e)
            tasks_info = None
        if tasks_info is not None:
            return json.loads(tasks_info.decode())
        else:
            try:
                # 判断用户登录状态
                # if g.user_id:
                #     # 查询用户任务列表
                #     tasks_info_list = MysqlSearch().get_more(f"SELECT t.task_reward,t.id,t.name,t.\
                #                                     tasks_counts,t.allow_nums,\
                #                                         t.poster_img,t.count_tasks, \
                #                                             t.tasks_fulfil,t.tags,t.recommend,t.virtual_nums,t.end_time, \
                #                                                 t.begin_task_time,t.task_class,t.check_time FROM {TASKS_TABLE} as t \
                #                                                     WHERE t.`status`=2 and t.id not IN \
                #                                                         (SELECT task_id FROM {ET_TASK_ORDERS} as et where member_id={g.user_id}) \
                #                                                             order by check_time desc LIMIT {page_index},{page_size} ")
                # else:
                tasks_info_list = MysqlSearch().get_more(f"SELECT task_reward,id,name,tasks_counts,allow_nums,poster_img, \
                                                       count_tasks,tasks_fulfil,tags,recommend,virtual_nums,end_time,begin_task_time,\
                                                            task_class,check_time FROM {TASKS_TABLE} WHERE status=2 AND task_class=2 \
                                                                order by check_time desc LIMIT {page_index},{page_size} ")
                # 查询系统公告,并返回
                gg = MysqlSearch().get_one(f"SELECT notice FROM {ET_GLOBAL_CONFIG}")
                tasks_info = []
                for res in tasks_info_list:
                    # 判断任务是否过期
                    end_time = res['end_time'].strftime("%Y-%m-%d-%H-%M-%S")
                    now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                    if end_time > now_time:
                        tasks_count = int(res['tasks_counts']) - int(res['count_tasks'])
                        tasks_info.append({
                            '任务奖金': res['task_reward'],
                            '任务id': res['id'],
                            '任务名称': res['name'],
                            '任务总参与次数': res['allow_nums'],
                            '任务已赚': res['count_tasks'] + int(res['virtual_nums']),
                            '任务头像': res['poster_img'],
                            '任务数量': int(tasks_count),
                            '任务标签': res['tags'],
                            '推荐': res['recommend'],
                            '人气': res['virtual_nums'],
                            '任务开始时间': res['begin_task_time'].strftime("%Y-%m-%d %H:%M:%S"),
                            '任务结束时间': res['end_time'].strftime("%Y-%m-%d %H:%M:%S"),
                            '任务类型': res['task_class'],
                        })
                tasks_info.append({'系统公告': gg['notice']})

            except Exception as e:
                current_app.logger.error(e)
            if tasks_info:
                self.save(tasks_info)
                return tasks_info
            else:
                return False
