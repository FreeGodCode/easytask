import random
import string
import time
from flask_restplus import Resource, reqparse
from utils.mysql_cli import MysqlSearch, MysqlWrite
from utils.constants import ET_MEMBER_RELATIONS, MEMBERS_TABLE, ACTIVITY_REWARDS
from flask import g, current_app
import datetime
from utils.short_link import get_short_link
from utils.http_status import HttpStatus
from utils.member_short_link import mer_short_link

class RankView(Resource):
    def get(self):
        """邀请排行榜"""
        json_data = dict()
        # 查询我的邀请码
        m = MysqlSearch().get_one(f"SELECT IIUV,avatar FROM {MEMBERS_TABLE} WHERE ID='{g.user_id}'")
        json_data['我的邀请码'] = m['IIUV']
        json_data['头像'] = m['avatar']
        json_data['我的邀请链接'] = mer_short_link()
        # 查询本周邀请好友
        # 计算当天到7天后的日期
        weeks_member_count = 0
        day_time = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        weeks_member = MysqlSearch().get_more(
            f"SELECT reg_time,id FROM {MEMBERS_TABLE}  as em  WHERE id IN (SELECT member_id FROM et_member_relations WHERE parent_id=94) AND WEEK(em.reg_time) = WEEK(now())")
        if weeks_member:
            for weeks in weeks_member:
                if weeks['id'] != g.user_id:
                    weeks_member_count += 1
        json_data['当周邀请人数'] = weeks_member_count
        
        # fixbug-1 by stonesin
        # 当周的 activity_id: SELECT id FROM et_activity WHERE week(create_time)= week(now())
        # 上周的 activity_id：SELECT id FROM et_activity WHERE YEARWEEK(create_time)= YEARWEEK(now())-1
        act_data2 = MysqlSearch().get_one("SELECT id FROM et_activity WHERE YEARWEEK(create_time) = YEARWEEK(now()) - 1")
        act_id2 = act_data2['id']
        rank_data2 = MysqlSearch().get_more(f"SELECT member_id,invite_count,bonus,avatar FROM {ACTIVITY_REWARDS} WHERE activity_id={act_id2} ORDER BY invite_count DESC;")
        rank_data_list_2 = []
        if rank_data2:
            for i in rank_data2:
                # if i['bonus'] == 0:
                #     continue
                rank_data_dict = {
                    '邀请人数': i['invite_count'],
                    '用户id': i['member_id'],
                    '奖金': i['bonus'],
                    '头像': i['avatar']
                }
                rank_data_list_2.append(rank_data_dict)

        # 当周排行榜用户邀请人,奖金数据
        act_data = MysqlSearch().get_one("SELECT id FROM et_activity WHERE week(create_time)= week(now())")
        rank_data_list = []
        if act_data:
            act_id = act_data['id']
            # 获取本周排行榜用户,邀请人,奖金数据.
            rank_data = MysqlSearch().get_more(f"SELECT member_id,invite_count,bonus,avatar FROM {ACTIVITY_REWARDS} WHERE activity_id={act_id} ORDER BY invite_count DESC;")
            # end fixbug
            if rank_data is None:
                return {'error_code': 4007, 'msg': '暂无数据,请稍后再试','data': rank_data_list}, HttpStatus.OK.value
            for i in rank_data:
                # if i['bonus'] == 0:
                #     continue
                rank_data_dict = {
                    '邀请人数': i['invite_count'],
                    '用户id': i['member_id'],
                    '奖金': i['bonus'],
                    '头像': i['avatar']
                }
                rank_data_list.append(rank_data_dict)
            # 获取当前用户邀请奖励
            user_data = MysqlSearch().get_one(f"SELECT bonus FROM {ACTIVITY_REWARDS} WHERE member_id='{g.user_id}'")
            user_bonus = 0
            if user_data and user_data['bonus'] != 0:
                json_data['用户奖励'] = user_data['bonus']
            else:
                json_data['用户奖励'] = user_bonus
            json_data['本周排行'] = rank_data_list
            json_data['上周排行'] = rank_data_list_2
            return {'data': json_data}, HttpStatus.OK.value
        else:
            return {'code': 4007, 'msg': '暂无数据,请稍后再试'}, HttpStatus.OK.value

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('amount', type=int, required=True, location='json')
        args = parser.parse_args()
        # 判断当前用户是否已经领取该奖金
        w = MysqlSearch().get_one(f"SELECT pay_status FROM {ACTIVITY_REWARDS} WHERE member_id='{g.user_id}'")
        if w is False or w['pay_status'] == 1:
            return {'error_code': 4003, 'msg': '改奖励已领取/没有奖金可领'}, HttpStatus.OK.value
        if not args.amount:
            return {'error_code': 4003, 'msg:': '参数异常'}, HttpStatus.OK.value
        # 乐观锁解决修改用户余额
        l = MysqlSearch().get_one(
            f"SELECT balance,balance_version FROM {MEMBERS_TABLE} WHERE id='{g.user_id}'")
        ye = int(args.amount * 100)
        # 生成20位随机字符串
        salt = ''.join(random.sample(string.ascii_letters + string.digits, 20))
        version_time = str(time.time()) + salt
        try:
            u = MysqlWrite().write(
                f"UPDATE {MEMBERS_TABLE} SET balance='{ye}',balance_version='{version_time}' WHERE balance_version='{l['balance_version']}' and id='{g.user_id}'")
            if u == 1:
                # 删除用户余额缓存
                rc = current_app.redis_cli
                rc.delete(f'user_center:{g.user_id}')
                # 修改当前用户是否已领取该奖金
                x = MysqlWrite().write(f"UPDATE {ACTIVITY_REWARDS} SET pay_status=1 WHERE member_id='{g.user_id}'")
                if x == 1:
                    return {'code': 2001, 'msg': '领取成功!'}, HttpStatus.OK.value
                else:
                    return {'error_code': 4001, 'msg': '服务器异常,请稍后再试'}, HttpStatus.OK.value
            else:
                return {'error_code': 4001, 'msg': '服务器异常,请稍后再试'}, HttpStatus.OK.value
        except Exception:
            return {'error_code': 4001, "msg": '请稍后重试'}, HttpStatus.OK.value