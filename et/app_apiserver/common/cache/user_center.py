import json
from flask import current_app,g
from redis.exceptions import RedisError
from cache import constants
from utils.constants import MEMBERS_TABLE, ET_MEMBER_EARNINGS, ET_MEMBER_RELATIONS,ET_APPS_PUB_HISTORY, ET_MEMBER_WITHDRAWAL
from utils.invite_intercept import intercept
from utils.mysql_cli import MysqlSearch
from utils.short_link import get_short_link


class UserCentreCache(object):
    """用户个人中心缓存"""
    def __init__(self):
        self.user_center_key = 'user_center:{}'.format(g.user_id)
        self.key = 0

    def save(self, user_center):
        """设置用户个人中心信息缓存"""
        try:
            rc = current_app.redis_cli
            rc.hsetnx(self.user_center_key, self.key, json.dumps(user_center))
            rc.expire(self.user_center_key, constants.UserCenterCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """获取用户个人中心信息缓存"""
        rc = current_app.redis_cli
        try:
            user_center = rc.hget(self.user_center_key,self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_center = None
        if user_center:
            return json.loads(user_center.decode())
        else:
            try:
                user_center = dict()
                # 查询当前app版本号
                config = MysqlSearch().get_more(f"SELECT version,update_status,down_url FROM {ET_APPS_PUB_HISTORY}")
                if config:
                    new_config = config[-1]
                    config_data = dict()
                    user_center['当前系统版本'] = new_config['version']
                # 用户uuid
                sql_user = f"SELECT nickname,avatar,IIUV,balance,mobile,setreal,alipayid FROM {MEMBERS_TABLE} WHERE ID='{g.user_id}'"
                user = MysqlSearch().get_one(sql_user)
                if user['alipayid'] is None or user['alipayid'] == '0':
                    user_center['支付宝状态'] = 0
                else:
                    user_center['支付宝状态'] = 1
                # 用户资金收益
                sql_earnings = f"SELECT sum(amounts) FROM {ET_MEMBER_EARNINGS} WHERE member_id='{g.user_id}'"
                # {'sum(amounts)': Decimal('300')}
                earnings = MysqlSearch().get_one(sql_earnings)
                # 查询当前用户提现状态
                tx = MysqlSearch().get_one(f"SELECT verify FROM {ET_MEMBER_WITHDRAWAL} WHERE member_id='{g.user_id} AND verify=2'")
                if tx is False:
                    user_center['提现状态'] = 0
                else:
                    user_center['提现状态'] = 1
                # 查询我的邀请人
                m = MysqlSearch().get_one(f"SELECT IIUV FROM {MEMBERS_TABLE} WHERE id in (SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{g.user_id}')")
                if m is False or m['IIUV'] == user['IIUV']:
                    user_center['我的邀请人'] = ""
                else:
                    user_center['我的邀请人'] = m['IIUV']
                user_center['手机号码'] = int(user['mobile'])
                user_center['用户名称'] = user['nickname']
                user_center['头像'] = user['avatar']
                user_center['邀请码'] = user['IIUV']
                user_center['余额'] = user['balance'] / 100
                # user_center['邀请链接'] = get_short_link(user['IIUV'])
                user_center['邀请链接'] = ''
                user_center['实名状态'] = user['setreal']
                if earnings['sum(amounts)'] is not None:
                    user_center['总收益'] = str((earnings['sum(amounts)']))
                    user_center["红包状态"] = 1
                else:
                    user_center["红包状态"] = 0
                    user_center['总收益'] = str(0)
                user_center['用户邀请权限'] = intercept()
            except Exception as e:
                current_app.logger.error(e)
            if user_center:
                self.save(user_center)
                return user_center
            else:
                return False