import json
import math
import time
from anytree import findall
from anytree.importer import DictImporter
from flask_limiter.util import get_remote_address
from flask_restplus import Resource, reqparse, Namespace, fields

from utils import constants
from haozhuan.resources.user import user_api
from utils.decorators import verify_required, login_required
from utils.http_status import HttpStatus
from utils.constants import ET_DRP_CONFIG,ET_MEMBER_WITHDRAWAL,MEMBERS_TABLE,ET_MEMBER_EARNINGS,ET_MEMBER_RELATIONS
from utils.mysql_cli import MysqlSearch,MysqlWrite
from flask import g, current_app
from datetime import datetime
from utils.limiter import limiter as lmt

# 用户提现页面
user_carry = Namespace('user_carry_money',description='获取用户提现页面 请求方式:带token请求即可')
user_api.add_namespace(user_carry)
user_carry_model = user_api.model('user_carry_model', {
        '返回信息': fields.String(description='提现页面数据'),
        '提示': fields.String(description='此接口必须携带token'),
})

# 用户提交提现

user_carry_post = Namespace('user_carry_money',description='提交提现 请求方式:json')
user_api.add_namespace(user_carry_post)
user_carry_post_model = user_api.model('user_carry_post_model', {
        'amount': fields.Integer(description='提现的金额'),
        '请求类型': fields.String(description='json'),
        '返回信息': fields.String(description='返回成功或者失败回调'),
        '提示': fields.String(description='此接口必须携带token'),
})

@user_carry.route('')
class UserCarryMoneyView(Resource):

    error_message = 'Too many requests.'

    decorators = [
        lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
                  key_func=get_remote_address,
                  error_message=error_message)
    ]
    method_decorators = [verify_required]
    # method_decorators = {
    #     'get': [login_required],
    #     'post': [verify_required]
    # }
    @user_carry.expect(user_carry_model)
    def get(self):
        # 取出drp_config表里面的withdrawal_condition字段组装数据返回
        sql_charge = f"SELECT handling_fee,daily_withdrawal,min_money,withdrawal_condition FROM {ET_DRP_CONFIG}"
        res = MysqlSearch().get_more(sql_charge)
        # 查询当前用户余额
        y = MysqlSearch().get_one(f"SELECT balance FROM {MEMBERS_TABLE} WHERE ID='{g.user_id}'")
        user_carry_money = dict()
        if res:
            charge = res[-1]
            user_carry_money = json.loads(charge['withdrawal_condition'])
            user_carry_money['手续费'] = charge['handling_fee']
            user_carry_money['最小提现金额'] = charge['min_money']
            user_carry_money['可提现次数'] = charge['daily_withdrawal']
        if y['balance'] is None:
            user_carry_money['钱包余额'] = 0
        else:
            user_carry_money['钱包余额'] = y['balance'] / 100
        # 查询当前用户邀请的人数
        son_member = MysqlSearch().get_more(
            f"SELECT member_id FROM {ET_MEMBER_RELATIONS} WHERE parent_id='{g.user_id}'")
        if son_member is not None:
            member_count = 80
            for son in son_member:
                if son['member_id'] != g.user_id:
                    member_count += 1
            user_carry_money['邀请人数'] = member_count
            return {'data': user_carry_money}, HttpStatus.OK.value


    @user_carry_post.expect(user_carry_post_model)
    def post(self):
        """提交提现数据"""
        parser = reqparse.RequestParser()
        parser.add_argument('amount', type=str, required=True, location='json')
        args = parser.parse_args()
        args.amount= float(args.amount)
        # 查询当前用户余额  #todo 以后增加手续费计算出正常金额对比提现条件是否相等
        y = MysqlSearch().get_one(f"SELECT balance,alipayid FROM {MEMBERS_TABLE} WHERE ID='{g.user_id}'")
        if y['balance'] is None or args.amount > (y['balance'] / 100) or y['alipayid'] == '':
            return {'error': f"余额不足,剩余余额{y['balance']}/支付宝未绑定"}, HttpStatus.OK.value
        # 查询最小提现金额和当天最多提现次数
        sql = f"SELECT daily_withdrawal,handling_fee,withdrawal_condition FROM {ET_DRP_CONFIG}"
        res = MysqlSearch().get_more(sql)[-1]
        # 查询是否已经提现过1元
        if args.amount == 1:
            try:
                sm = current_app.redis_cli.sismember('carry_money_1', g.user_id)
                if sm is True:
                    return {'error': '用户已提现过1元,无法再次提现1元'}, HttpStatus.OK.value
            except TypeError as e:
                current_app.logger.error(f"TypeError{e}")
        # 查询当前用户邀请的人数
        son_member = MysqlSearch().get_more(
            f"SELECT member_id FROM {ET_MEMBER_RELATIONS} WHERE parent_id='{g.user_id}'")

        if son_member is not None:
            member_count = 0
            for son in son_member:
                if son['member_id'] != g.user_id:
                    member_count += 1
            # 对比当前提现条件 # todo conditions要从数据库取出判断.
            # 从数据库取出提现条件
            allow_money = []
            prentice_count = []
            with_data = json.loads(res['withdrawal_condition'])
            for q in with_data.values():
                for i, e in enumerate(q):
                    if 'allow_money' in e:
                        allow_money.append(e['allow_money'])
                        continue
            for k in with_data.values():
                for c, x in enumerate(k):
                    if 'prentice_count' in x:
                        prentice_count.append(x['prentice_count'])
                        continue
            for k, v in enumerate(zip(allow_money, prentice_count)):
                if args.amount == v[0] and member_count >= v[1]:

                    # 查询当前用户当天提现次数
                    c_list = MysqlSearch().get_more(
                        f"SELECT member_id,start_time FROM {ET_MEMBER_WITHDRAWAL} WHERE member_id='{g.user_id}'")

                    if c_list:
                        now_time = datetime.now().strftime("%Y-%m-%d")
                        count = 0
                        for c in c_list:
                            if c['start_time'].strftime("%Y-%m-%d") == now_time:
                                count += 1
                        # 判断当前用户当天是否超过提现次数
                        if count > int(res['daily_withdrawal']):
                            return {'error': '已超过当天提现次数'}, HttpStatus.OK.value
                    
                    if res:
                        # 提现最小金额限制暂时取消使用
                        # new_res = res
                        # min_money = new_res['min_money'] / 100
                        # if args.amount < min_money:
                        new_res = res
                        min_money = 0

                        if args.amount < min_money:
                            return {'error': '提现金额过小最小提现金额为:{}'.format(min_money)}, HttpStatus.BAD_REQUEST.value
                        else:

                            # 查询手续费.当前提现金额减去手续费入库
                            try:
                                if res['handling_fee'] != '0':
                                    handling_fee = int(res['handling_fee']) / 100
                                else:
                                    handling_fee = 0

                                user_handling = args.amount * handling_fee
                                new_amounts = args.amount - user_handling
                                res1 = MysqlWrite().write(
                                    f"INSERT INTO {ET_MEMBER_WITHDRAWAL} (pay_status,amounts,member_id) VALUE (1, {new_amounts}, {g.user_id})")
                               
                            except Exception as e:
                                current_app.logger.info(f"Exception : {e}")

                            if res1 == 1:
                                # 乐观锁解决修改用户余额
                                l = MysqlSearch().get_one(
                                    f"SELECT balance,balance_version FROM {MEMBERS_TABLE} WHERE id='{g.user_id}'")
                                ye = l['balance'] - args.amount * 100
                                version_time = time.time()
                                try:
                                    u = MysqlWrite().write(
                                        f"UPDATE {MEMBERS_TABLE} SET balance='{ye}',balance_version='{version_time}' WHERE balance_version='{l['balance_version']}' and id='{g.user_id}'")
                                except Exception:
                                    return {'error': '请稍后重试'}, HttpStatus.OK.value
                                rc = current_app.redis_cli
                                # 增加redis set 保存已提现过1元的用户
                                if args.amount == 1:
                                    rc.sadd('carry_money_1', g.user_id)
                                rc.delete('user_center:{}'.format(g.user_id))
                                rc.delete('user_withdraw_recode:{}'.format(g.user_id))
                                a_data = {
                                    '手续费': user_handling,
                                    '提现金额': new_amounts
                                }
                                return {'data': a_data, 1: '提现成功!'}, HttpStatus.OK.value
                continue

        return {'error': '提现金额/邀请人数不符合条件'}, HttpStatus.OK.value


