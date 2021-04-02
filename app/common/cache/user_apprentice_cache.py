from datetime import datetime
import json
from flask import g, current_app
from redis import RedisError
from cache import constants
from utils.constants import MEMBERS_TABLE, ET_MEMBER_RELATIONS, ET_DRP_CONFIG
from utils.mysql_cli import MysqlSearch

class UserApprenticeCache(object):
    """用户收徒页面缓存"""
    def __init__(self):
        self.user_apprentice_key = 'user_apprentice_:{}'.format(g.user_id)

    def save(self, user_apprentice):
        """设置用户收徒页面缓存"""
        try:
            rc = current_app.redis_cli
            rc.hsetnx(self.user_apprentice_key, 0, json.dumps(user_apprentice))
            rc.expire(self.user_apprentice_key, constants.UserApprenticeCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """获取用户收徒页面信息缓存"""
        rc = current_app.redis_cli
        try:
            user_apprentice = rc.hget(self.user_apprentice_key,0)
        except RedisError as e:
            current_app.logger.error(e)
            user_apprentice = None
        if user_apprentice is not None:
            return json.loads(user_apprentice.decode())
        else:
            # 查询用户名称, 邀请码
            sql_nickname = f"SELECT nickname,iiuv FROM {MEMBERS_TABLE} WHERE id={g.user_id}"
            res_nickname = MysqlSearch().get_one(sql_nickname)
            # 查询用户分销收益总奖励
            sql_amounts = f"SELECT amounts,add_time FROM et_member_drps WHERE  member_id ={g.user_id}"
            res_amounts = MysqlSearch().get_more(sql_amounts)
            # 查询我的好友(徒弟(下级))
            h = MysqlSearch().get_more(
                f"SELECT id,nickname,reg_time,avatar FROM {MEMBERS_TABLE} WHERE ID in (SELECT member_id FROM {ET_MEMBER_RELATIONS} WHERE parent_id='{g.user_id}')")
            my_f = []
            if h:
                for i in h:
                    if i['id'] != g.user_id:
                        my_f.append({
                            '头像': i['avatar'],
                            '名称': i['nickname'],
                            '注册时间': i['reg_time'].strftime("%Y-%m-%d-%H-%M-%S")
                        })
            user_apprentice = dict()
            user_apprentice['我的好友'] = my_f
            # 用户邀请总奖励
            sum_amounts = 0
            # 用户当天邀请总奖励
            today_amounts = 0
            now_time = datetime.now().strftime("%Y-%m-%d")
            if res_amounts:
                # 计算总奖励
                for amounts in res_amounts:
                    for k, v in amounts.items():
                        if k == 'amounts':
                            sum_amounts = sum_amounts + v
                    # 剔除不是当天的奖励,计算当天奖励的和
                    if amounts['add_time'].strftime("%Y-%m-%d") == now_time:
                        for k, v in amounts.items():
                            if k == 'amounts':
                                today_amounts = today_amounts + v
            user_apprentice['邀请总奖励'] = sum_amounts / 100
            user_apprentice['当天邀请奖励'] = today_amounts / 100
            user_apprentice['用户名称'] = res_nickname['nickname']
            user_apprentice['邀请码'] = res_nickname['iiuv']
            # todo 如果查不到此用户要捕捉返回错误
            # 查询当前用户邀请的人数
            son_member = MysqlSearch().get_more(f"SELECT member_id FROM {ET_MEMBER_RELATIONS} WHERE parent_id='{g.user_id}'")
            if son_member is not None:
                member_count = 0
                for son in son_member:
                    if son['member_id'] != g.user_id:
                        member_count += 1
                user_apprentice['邀请人数'] = member_count
            # 查询并计算当前用户当天邀请人数
            today_member_count = 0
            today_member = MysqlSearch().get_more(f"SELECT reg_time,id FROM {MEMBERS_TABLE} WHERE id IN (SELECT member_id FROM {ET_MEMBER_RELATIONS} WHERE parent_id='{g.user_id}')")
            if today_member:
                now_time = datetime.now().strftime("%Y-%m-%d")
                for today in today_member:
                    if today['id'] != g.user_id and today['reg_time'].strftime("%Y-%m-%d") == now_time:
                        today_member_count += 1
            user_apprentice['当天邀请人数'] = today_member_count
            # 查询各分销奖金比例
            ss = MysqlSearch().get_more(f"SELECT profit_percentage FROM {ET_DRP_CONFIG}")
            if ss:
                user_apprentice['各级分销奖金比例'] = ss[-1]
            if user_apprentice:
                self.save(user_apprentice)
                return user_apprentice
            else:
                return False













