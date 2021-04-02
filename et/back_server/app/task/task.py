import hashlib
import json
import time
import logging
from datetime import datetime
from app.models.task import EtTask
from app.models.task import EtTaskOrder
from app.models.task import EtTasksVerify
from app.models.accounts import EtAccount
from app.models.member import EtMember
from app.models.member import EtMemberExtend
from app.models.orders import EtMemberEarning
from app.models.orders import EtMemberRelation
from app.models.orders import EtMemberWithdrawal
from app.models.drp import EtDrpConfig

from flask import Blueprint, jsonify, session, request, current_app
from app.utils.util import route, Redis, helpers
from app.utils.core import db, scheduler
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.response import ResMsg
from app.celery import flask_app_context, async_alipay_service
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='logs/task.log',
                    filemode='a')

logging.getLogger('scheduler').setLevel(logging.DEBUG)


redis_key_drp = "drpconfig"
redis_key_sys = "sysconfig"
realtion_tree_key = "drp_relation_member_"
user_center_key = "user_center:"
user_info_key="user_info:"
user_withdraw_recode_key= "user_withdraw_recode:"
user_task_earnings_key=  "user_task_earnings_:"
user_appretice_detail_key = "user_appretice_detail_:"
user_apprentice_key= "user_apprentice_:"


def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')

# scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

def test_my_job():
    with db.app.app_context():
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("job test health-------:)")
        print(datetime.now())

def get_rank_data():
    """
    获取每周邀请的排行榜
    更新至activity_rewards表
    """
    with db.app.app_context() as app_context:

        limit_num = 10
        activity_id = 1
        round_num= 1

        activity_is_open = db.session.execute(f'SELECT id,act_name FROM `et_activity` WHERE status = 1').first()
        
        if not activity_is_open:
            print('暂无活动数据！')
            return '暂无活动数据！'

        if activity_is_open:
            activity_id= activity_is_open[0]
            print(activity_is_open[1]+': 更新活动数据')

        act_config = db.session.execute(f'SELECT * FROM `et_activity_configs` WHERE `act_id` = {activity_id}').first()

        if not act_config:
            print('活动配置数据异常！')
            return '活动配置数据异常！'

        act_configs = dict(act_config)
        configs= json.loads(act_configs['act_configs'])
        
        if configs:
            limit_num= configs['page_show']

        rank_sql= f'SELECT COUNT(mr.id) AS counts,m.id,m.IIUV,m.avatar,m.nickname,m.realname FROM et_member_relations AS mr LEFT JOIN et_members AS m on m.id= mr.parent_id WHERE week(mr.create_time) = week(now()) AND m.id is not null GROUP BY (mr.parent_id) ORDER BY counts DESC LIMIT 0 ,{limit_num}'

        rank_lists = db.session.execute(rank_sql).fetchall()

        rank_data =  [{k: v for (k, v) in row.items()} for row in rank_lists]
        
        is_send = db.session.execute(f'SELECT * FROM `activity_rewards` WHERE `activity_id` = {activity_id}')
        send_data =  [{k: v for (k, v) in row.items()} for row in is_send]
        
        # if data already exist,only update
        # else insert new data 
        
        if send_data:
            is_fake = db.session.execute(f'SELECT * FROM `activity_rewards` WHERE `activity_id` = {activity_id} AND fake=1')
            send_data =  [{k: v for (k, v) in row.items()} for row in is_fake]
            fake_len= len(send_data)

            for index,item in enumerate(rank_data):
                avatar= f'{item["avatar"]}'
                update_sql= f'UPDATE `activity_rewards` SET member_id={item["id"]},invite_count={item["counts"]},avatar="{avatar}" WHERE activity_id={activity_id} AND fake=0 AND rank_num = {index+fake_len+1}'
            
                db.session.execute(update_sql)
            db.session.commit()

        else:
            for index,item in enumerate(rank_data):
                avatar= f'{item["avatar"]}'
                insert_sql = f'INSERT INTO activity_rewards (member_id, invite_count, activity_id,rank_num,avatar) VALUES ({item["id"]}, {item["counts"]}, {activity_id},{index+1},"{avatar}");'
                db.session.execute(insert_sql)
            db.session.commit()

        print('插入排行榜数据成功')



def auto_verify_withdrawals():
    with db.app.app_context() as app_context:
        """
            用户提现自动审核后台任务
            @logic 审核完成 异步发送任务至redis队列执行支付宝付款任务
        """
        def auto_handle_wd(app_context, wd_id:int,member_id:int,status:int = 2):
            with app_context:
                res = {}
                
                verify_log = '系统自动发放'

                account_name = 'system'
                now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                verify_orders = db.session.query(EtMemberWithdrawal).filter(
                    EtMemberWithdrawal.id == wd_id, EtMemberWithdrawal.member_id == member_id).first()

                if not verify_orders:
                    res.update(code=ResponseCode.Success, data={},
                               msg=f'数据异常')
                    return res
                
                if verify_orders.pay_status==3:
                    res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'该单已发放无法再次提现'))
                    return res

                # if verify_orders.pay_status==2:
                #     res.update(dict(code=ResponseCode.Success, data={},
                #                 msg=f'正在支付走账'))
                #     return res
                
                user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, EtMember.realname, EtMember.mobile, EtMember.IIUV,EtMember.balance,EtMember.balance_version, EtMember.setreal, EtMember.alipayid).filter(EtMember.id == member_id).first()

                if not user:
                    res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'用户信息异常'))
                    return res

                user_info = (dict(zip(user.keys(), user)))

                pay_status= 2

                if user_info['status']==2:
                    verify_log= '账号违规,无法发放提现'
                    pay_status= 4
                    verify= 1
                    status= 1

                update_dict = {
                    "verify": status,
                    "verify_log": verify_log,
                    "account": account_name,
                    "check_time": now_timestr,
                    "pay_status": pay_status
                }
                update_dict_ready = helpers.rmnullkeys(update_dict)

                db.session.query(EtMemberWithdrawal).filter(
                    EtMemberWithdrawal.id == wd_id).update(update_dict_ready)
                
                res_data = dict()
                ret=''

                try:
                    if user_info['status']==2:
                        # back balace to member
                        drp_config = Redis.hgetall(redis_key_drp)
                        handling_fee_s = drp_config[b'handling_fee']
                        handling_fee = float(str(handling_fee_s, encoding = "utf-8"))

                        add_balance=0
                        if handling_fee==0:
                            add_balance= verify_orders.amounts
                        else:
                            handling_fee = (1- float(handling_fee) / 100)
                            add_balance= round(verify_orders.amounts/handling_fee,2)
                        
                        if verify_orders.origin_amount:
                            add_balance = verify_orders.origin_amount

                        user_update_dict = {
                            "balance": user_info['balance'] + add_balance*100,
                            "balance_version": int(time.time())
                        }
                        db.session.query(EtMember).filter(
                            EtMember.id == mid, EtMember.balance_version == user_info['balance_version']).update(user_update_dict)

                    db.session.commit()

                    # verify pass go alipay
                    ret= async_alipay_service.delay(serial_number=wd_id, alipay_account=user_info['alipayid'], real_name=user_info['realname'], pay_amount=verify_orders.amounts, mid= member_id)

                    res.update(code=ResponseCode.Success,
                               data=res_data, msg=f'提现审核成功,系统将发放收益到用户收款账户,请留意支付返回消息')
                    return res

                except Exception as why:

                    res.update(code=ResponseCode.Success, data={},msg=f'用户提现订单审核失败，数据异常{why}')
                    return res

        all_verify_orders = db.session.query(EtMemberWithdrawal).filter(
            EtMemberWithdrawal.verify == 0, EtMemberWithdrawal.amounts <=10).all()
        
        if len(all_verify_orders)==0:

            payfail_verify_orders = db.session.query(EtMemberWithdrawal).filter(EtMemberWithdrawal.pay_status == 2).all()

            if len(payfail_verify_orders) > 0:
                all_verify_orders = payfail_verify_orders
            else:
                print("没有待发放订单")
            
        for item in all_verify_orders:
            print(item.id)
            print(item.member_id)
            res= auto_handle_wd(app_context, wd_id=item.id, member_id=item.member_id)
            print(res)

