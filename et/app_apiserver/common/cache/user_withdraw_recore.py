import json
from flask import current_app,g
from redis.exceptions import RedisError
from cache import constants
from utils.constants import ET_MEMBER_WITHDRAWAL,ET_DRP_CONFIG
from utils.mysql_cli import MysqlSearch
import math


class UserWithdrawRecodeCache(object):
    """用户提现记录缓存"""
    def __init__(self):
        self.user_withdraw_recode_key = 'user_withdraw_recode:{}'.format(g.user_id)
        self.key = 0

    def save(self, user_recode):
        """设置用户提现缓存"""
        try:
            rc = current_app.redis_cli
            rc.lpush(self.user_withdraw_recode_key, json.dumps(user_recode))
            rc.expire(self.user_withdraw_recode_key, constants.UserWithdrawCacheTTL.get_val())
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """获取用户提现信息缓存"""
        rc = current_app.redis_cli
        try:
            user_recode = rc.lrange(self.user_withdraw_recode_key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            user_recode = None
        if user_recode:
            return json.loads(user_recode[0].decode())
        else:
            try:
                # 查询当前用户提现流水
                sql = f"SELECT withdrawal_type,start_time,amounts,verify FROM {ET_MEMBER_WITHDRAWAL} \
                            WHERE member_id='{g.user_id}' order by start_time desc"
                res_list = MysqlSearch().get_more(sql)
                # 查询提现手续费,计算出手续费金额返回
                s = MysqlSearch().get_more(f"SELECT handling_fee FROM {ET_DRP_CONFIG}")[-1]
                user_recode = []
                for res in res_list:
                    user_recode.append({
                        '提现方式': res['withdrawal_type'],
                        '提现时间': res['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
                        '提现金额': res['amounts'],
                        '审核状态': res['verify'],
                        '提现手续费': s['handling_fee'],
                    })
            except Exception as e:
                current_app.logger.error(e)
            if user_recode:
                self.save(user_recode)
                return user_recode
            else:
                return False