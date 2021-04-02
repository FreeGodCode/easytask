import json
from flask import g, current_app
from redis import RedisError
from cache import constants
from utils.mysql_cli import MysqlSearch
from utils.hashids_iiuv import hashids_iivu_encode

class UserApprenticeDetailCache(object):
    """用户收徒收益明细缓存"""
    def __init__(self):
        self.user_appretice_detail = 'user_appretice_detail_:{}'.format(g.user_id)

    def save(self, user_apprentice_detail):
        """设置用户收徒明细缓存"""
        try:
            rc = current_app.redis_cli
            rc.lpush(self.user_appretice_detail, json.dumps(user_apprentice_detail))
            rc.expire(self.user_appretice_detail, constants.UserApprenticeDetailCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self, p_i, p_num):
        """获取用户收徒明细信息缓存"""
        rc = current_app.redis_cli
        try:
            user_apprentice_detail = rc.lrange(self.user_appretice_detail, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            user_apprentice_detail = None
        if user_apprentice_detail:
            return json.loads(user_apprentice_detail[0].decode())
        else:
            fetch_columns = "d.id,emr.levels, m1.nickname as username, \
                                m2.nickname as from_user, m1.IIUV, t.name\
                                    as taskname, d.amounts, d.add_time"

            drp_sql = f"SELECT {fetch_columns} FROM \
                   (SELECT * FROM et_member_drps WHERE member_id ={g.user_id} ORDER BY add_time DESC limit {p_i}, {p_num} ) AS d \
                        LEFT JOIN et_members AS m1 ON d.member_id = m1.id \
                            LEFT JOIN et_members AS m2 ON d.from_member_id = m2.id \
                                LEFT JOIN et_tasks AS t ON d.from_task_id = t.id \
								    LEFT JOIN et_member_relations as emr ON d.from_member_id = emr.member_id;"
            drp_list = MysqlSearch().get_more(drp_sql)
            user_apprentice_detail = []
            for res in drp_list:
                user_apprentice_detail.append({
                    '任务名称':res['taskname'],
                    '徒弟名称':res['from_user'],
                    '提交时间':res['add_time'].strftime("%Y-%m-%d-%H-%M-%S"),
                    '金额':res['amounts'],
                    '流水号':hashids_iivu_encode(res['id']),
                    '等级':res['levels'],
                })
            if user_apprentice_detail:
                self.save(user_apprentice_detail)
                return user_apprentice_detail
            else:
                return False
