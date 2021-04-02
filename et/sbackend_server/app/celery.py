import json
import logging
import time

import requests
from flask import current_app
from celery import Celery

from app.models.drp import EtMemberDrp
from app.models.member import EtMember
from app.models.orders import EtMemberWithdrawal
from app.utils.code import ResponseCode
from app.utils.core import db
from app.utils.util import Redis, helpers


celery_app = Celery(__name__)
logger = logging.getLogger(__name__)

redis_key_drp = "drpconfig"
redis_key_sys = "sysconfig"
realtion_tree_key = "drp_relation_member_"
user_center_key = "user_center:"
user_info_key = "user_info:"
user_withdraw_recode_key = "user_withdraw_recode:"
user_task_earnings_key = "user_task_earnings_:"
user_appretice_detail_key = "user_appretice_detail_:"
user_apprentice_key = "user_apprentice_:"
is_sendbalance_key = "is_sendbalance_"
is_new_member_key = "is_new_member"


@celery_app.task
def flask_app_context():
    """
    celery使用Flask上下文
    :return:
    """
    with current_app.app_context():
        return str('yes')


@celery_app.task
def async_calculating_earnings(parentid: int, level: int, earning_dict: dict, task_id: int, profit_percentage_arr: list,
                               type_set: int = 2):
    '''
        异步任务 计算该用户 所有上级 收益更新
        #type_set 收益来源：2：分销佣金 
        '''
    with current_app.app_context():
        res = dict()
        if earning_dict:
            fromuser = earning_dict['member_id']
            origin_money = earning_dict['amounts']
            logger.info(f'ORING收益:{origin_money}')
            logger.info(profit_percentage_arr)

            # get drpconfigs from cache
            drp_config = Redis.hgetall(redis_key_drp)
            per_set = drp_config[b'profit_percentage']
            per_set = str(per_set, encoding="utf-8")

            logger.info(f'分销比例all:{per_set}')
            per_set = json.loads(per_set)
            per_set = per_set[::-1]

            logger.info(f'reversed分销比例all:{per_set}')
            profit_percentage = per_set[level - 1]['per']
            logger.info(f'分销比例cur:{profit_percentage}')

            drp_money = origin_money * float(profit_percentage)
            logger.info(f'分销收益:{drp_money}')

            drp_earning_dict = {
                "member_id": parentid,
                "from_task_id": earning_dict['task_id'],
                "amounts": drp_money,
                "from_member_id": fromuser,
            }
            new_drp_earning = EtMemberDrp(**drp_earning_dict)
            db.session.add(new_drp_earning)
            logger.info(f'edt: {earning_dict}')

            user = db.session.query(EtMember).filter(
                EtMember.id == parentid).first()

            if user.status == 2:
                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'该用户已禁用，无法获得收益'))
                return res
            try:
                update_dict = {
                    "balance": drp_money * 100 + user.balance,
                    "balance_version": int(time.time())
                }

                db.session.query(EtMember).filter(
                    EtMember.id == parentid, EtMember.balance_version == user.balance_version).update(update_dict)

                db.session.commit()

                # update user cache
                Redis.delete(user_center_key + str(user.id))
                Redis.delete(user_info_key + str(user.mobile))
                Redis.delete(user_task_earnings_key + str(user.id))
                Redis.delete(user_appretice_detail_key + str(user.id))
                Redis.delete(user_apprentice_key + str(user.id))

                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'用户{fromuser}to{parentid}分销收益发放成功'))
                logger.info(res)
                return res
            except Exception as why:

                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'用户{fromuser}to{parentid}分销收益发放失败{why}'))
                logger.info(res)
                return res


def new_member_reward(from_user: int = 1):
    # 拉新邀请奖励
    from_user_id = from_user

    is_new_member = Redis.hget(is_new_member_key, from_user_id)

    if is_new_member:

        logger.info('parentid: is_new_member：' + is_new_member)
        parent_id = is_new_member
        is_sendbalance_redis = is_sendbalance_key + str(parent_id)

        is_send_balance = Redis.sismember(is_sendbalance_redis, from_user_id)

        # not in the set that means the mid not send balance to the parent_id
        if not is_send_balance:

            user = db.session.query(EtMember).filter(
                EtMember.id == parent_id).first()

            logger.info(f'{is_sendbalance_redis}:' + str(is_send_balance))

            drp_send = db.session.query(EtMemberDrp).filter(
                EtMemberDrp.member_id == parent_id, EtMemberDrp.from_task_id == 9999_9999,
                EtMemberDrp.from_member_id == from_user_id).first()
            logger.info(drp_send)
            if not drp_send:
                # from_task_id give a max value
                # add drp records
                drp_earning_dict = {
                    "member_id": parent_id,
                    "from_task_id": 9999_9999,
                    "amounts": 1,
                    "from_member_id": from_user_id,
                }
                new_drp_earning = EtMemberDrp(**drp_earning_dict)
                db.session.add(new_drp_earning)

                update_dict = {
                    "balance": 100 + user.balance,
                    "balance_version": int(time.time())
                }

                # update member balance
                db.session.query(EtMember).filter(
                    EtMember.id == user.id, EtMember.balance_version == user.balance_version).update(update_dict)
            try:
                db.session.commit()

                # update user cache
                Redis.delete(user_center_key + str(user.id))
                Redis.delete(user_info_key + str(user.mobile))
                Redis.delete(user_task_earnings_key + str(user.id))
                Redis.delete(user_appretice_detail_key + str(user.id))
                Redis.delete(user_apprentice_key + str(user.id))

                # update set of the send mids under the parentid
                Redis.sadd(is_sendbalance_redis, from_user_id)

                logger.info(f'from {from_user_id} to {parent_id} 发放邀请奖励成功')

            except Exception as why:

                logger.info(str(why))


@celery_app.task
def async_alipay_service(serial_number: int, alipay_account: str, real_name: str, pay_amount: int, mid: int):
    """
    @req: req_data
    req_data = {'alipay_account': alipay, 'alipay_name': real_name,
                        'amount': amount, 'serial_number': serial_number}
    @resp: result_status, error_code

    :return:
    """
    with current_app.app_context():
        res = {}
        now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        headers = {'content-type': 'application/json;charset=UTF-8'}
        req_data = {'alipay_account': alipay_account, 'alipay_name': real_name,
                    'amount': pay_amount, 'serial_number': serial_number}

        req_data['secret_key'] = 'FA77E2804734C22F72B22D9B7EDB41A9'
        wd_record = db.session.query(EtMemberWithdrawal).filter(
            EtMemberWithdrawal.id == serial_number).first()

        if wd_record:
            if wd_record.pay_status == 3:
                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'该单已发放无法再次提现'))
                return res

        user = db.session.query(EtMember).filter(
            EtMember.id == mid).first()

        verify_orders = db.session.query(EtMemberWithdrawal).filter(
            EtMemberWithdrawal.id == serial_number, EtMemberWithdrawal.member_id == mid).first()

        if user.status == 2:

            drp_config = Redis.hgetall(redis_key_drp)
            handling_fee_s = drp_config[b'handling_fee']
            handling_fee = float(str(handling_fee_s, encoding="utf-8"))

            add_balance = 0
            if handling_fee == 0:
                add_balance = verify_orders.amounts
            else:
                handling_fee = (1 - float(handling_fee) / 100)
                add_balance = round(verify_orders.amounts / handling_fee, 2)

            if verify_orders.origin_amount:
                add_balance = verify_orders.origin_amount

            update_dict = {
                "balance": user.balance + add_balance * 100,
                "balance_version": int(time.time())
            }

            db.session.query(EtMember).filter(
                EtMember.id == mid, EtMember.balance_version == user.balance_version).update(user_update_dict)
            update_dict = {
                "id": serial_number,
                "verify": 1,
                "pay_status": 4,
                "end_time": now_timestr,
                "verify_log": '账号已封禁,无法提现',
                "pay_log": '账号已封禁,无法提现',
            }
            update_dict_ready = helpers.rmnullkeys(update_dict)

            db.session.query(EtMemberWithdrawal).filter(
                EtMemberWithdrawal.id == serial_number).update(update_dict_ready)
            try:
                db.session.commit()
                Redis.delete(user_center_key + str(user.id))
                Redis.delete(user_info_key + str(user.mobile))
                Redis.delete(user_withdraw_recode_key + str(user.id))

            except Exception as why:
                msg = f'支付失败，请稍后再试{why}'
                logging.info(str(why))
                return msg

            if user.status == 2:
                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'该用户已禁用，无法提现'))
                return res

            res.update(dict(code=ResponseCode.Success, data={},
                            msg=f'该用户余额已不足，无法提现'))
            return res

        try:

            resp = requests.post('http://47.91.142.164/api/alipay/transfer', data=req_data, )

            resp_json = resp.json()

            if resp_json.get('code') == 0:
                resp_data = resp_json.get('data', {})
                result_status, error_code = resp_data.get(
                    'status'), resp_data.get('error_code')
            else:
                result_status, error_code = False, resp_json.get('msg', u'')

        except Exception as e:
            result_status, error_code = False, '网络错误' + str(e)
            logger.info(str(e))
            logger.info(result_status)

        if result_status:
            # update_db pay_status

            pay_status = 3
            update_dict = {
                "id": serial_number,
                "pay_status": pay_status,
                "end_time": now_timestr,
                "verify_log": '提现成功，已到账',
                "pay_log": '提现成功，已到账',
            }
            update_dict_ready = helpers.rmnullkeys(update_dict)

            db.session.query(EtMemberWithdrawal).filter(
                EtMemberWithdrawal.id == serial_number).update(update_dict_ready)

            try:
                db.session.commit()
                # update user cache
                Redis.delete(user_center_key + str(user.id))
                Redis.delete(user_info_key + str(user.mobile))
                Redis.delete(user_withdraw_recode_key + str(user.id))
                # send balance 100 to a parent which is never get the balance from this member
                new_member_reward(from_user=user.id)
            except Exception as why:
                msg = f'修改失败，请稍后再试{why}'
                return msg

            # title = '提现成功'
            # content = '恭喜您提现审核通过成功提现 {0}元'.format('%.2f' % (pay_amount))
            # logger.info(result_status)

        else:
            remark = ''
            if error_code in ['支付宝提现系统升级中！', 'INVALID_PARAMETER', 'PAYCARD_UNABLE_PAYMENT',
                              'PAYER_DATA_INCOMPLETE', 'PERMIT_CHECK_PERM_LIMITED', 'PAYER_STATUS_ERROR',
                              'PAYER_STATUS_ERROR', 'PAYER_DATA_INCOMPLETE', 'PAYMENT_INFO_INCONSISTENCY',
                              'CERT_MISS_TRANS_LIMIT', 'CERT_MISS_ACC_LIMIT', 'PAYEE_ACC_OCUPIED',
                              'MEMO_REQUIRED_IN_TRANSFER_ERROR', 'PERMIT_PAYER_LOWEST_FORBIDDEN',
                              'PERMIT_PAYER_FORBIDDEN',
                              'PERMIT_CHECK_PERM_IDENTITY_THEFT', 'REMARK_HAS_SENSITIVE_WORD', 'ACCOUNT_NOT_EXIST',
                              'PAYER_CERT_EXPIRED', 'SYNC_SECURITY_CHECK_FAILED', 'TRANSFER_ERROR']:
                remark = '支付宝提现系统升级中！请销后尝试'
            elif error_code in ['PERM_AML_NOT_REALNAME_REV', 'PERM_AML_NOT_REALNAME_REV',
                                'PERMIT_NON_BANK_LIMIT_PAYEE']:
                remark = '请登录支付宝站内或手机客户端完善身份信息后，重试！'
            elif error_code in ['PAYEE_NOT_EXIST', 'PERMIT_NON_BANK_LIMIT_PAYEE']:
                remark = '支付宝账号不存在！请检查之后重试'
            elif error_code == 'PAYEE_USER_INFO_ERROR':
                remark = '支付宝账号和姓名不匹配，请更换成实名信息支付宝账号！'
            elif error_code in ['服务暂时不可用！', 'SYSTEM_ERROR', 'PAYER_BALANCE_NOT_ENOUGH']:
                remark = '服务暂时不可用'
            elif error_code == 'BLOCK_USER_FORBBIDEN_RECIEVE':
                remark = '账户异常被冻结，无法收款，请咨询支付宝客服95188'
            else:
                remark = '支付失败,请稍后再试' + str(error_code)

            now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            pay_status = 4

            update_dict = {
                "id": serial_number,
                "verify": 1,
                "pay_status": pay_status,
                "verify_log": str(remark),
                "pay_log": str(remark) + ':' + str(error_code),
                # "end_time": now_timestr
            }
            update_dict_ready = helpers.rmnullkeys(update_dict)

            db.session.query(EtMemberWithdrawal).filter(
                EtMemberWithdrawal.id == serial_number).update(update_dict_ready)

            drp_config = Redis.hgetall(redis_key_drp)
            handling_fee_s = drp_config[b'handling_fee']
            handling_fee = float(str(handling_fee_s, encoding="utf-8"))
            logging.info('+提现失败金额：')
            logging.info(str(verify_orders.amounts))
            add_balance = 0
            if handling_fee == 0:
                add_balance = verify_orders.amounts
            else:
                handling_fee = (1 - float(handling_fee) / 100)
                add_balance = round(verify_orders.amounts / handling_fee, 2)

            if verify_orders.origin_amount:
                add_balance = verify_orders.origin_amount

            user_update_dict = {
                "balance": user.balance + add_balance * 100,
                "balance_version": int(time.time())
            }

            db.session.query(EtMember).filter(
                EtMember.id == mid, EtMember.balance_version == user.balance_version).update(user_update_dict)

            try:
                db.session.commit()
                Redis.delete(user_center_key + str(user.id))
                Redis.delete(user_info_key + str(user.mobile))
                Redis.delete(user_withdraw_recode_key + str(user.id))

            except Exception as why:
                msg = f'支付失败，请稍后再试{why}'
                logging.info(str(why))
                return msg

            logging.info(error_code + remark)
            return error_code + remark
        # return str(current_app.config)
