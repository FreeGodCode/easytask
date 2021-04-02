import hashlib
import time
import logging
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
from app.utils.core import db
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.response import ResMsg
from app.celery import flask_app_context, async_alipay_service


bp = Blueprint("orders", __name__, url_prefix='/orders')
# 运营平台用户收益流水 服务
logger = logging.getLogger(__name__)

user_center_key = "user_center:"
user_info_key="user_info:"
redis_key_drp= "drpconfig"


@route(bp, '/earninglists', methods= ["GET"])
@login_required
def handle_earninglists():
    """
    用户收益流水列表接口
    @todo 根据索引优化sql查询
    :return: json
    """
    res = ResMsg()
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))

    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')

    member_id = request.args.get("member_id", '')
    task_id = request.args.get("task_id", '')
    task_order_id = request.args.get("task_order_id", '')
    nickname = request.args.get("nickname", '')

    mobile = request.args.get("mobile", '')
    IIUV = request.args.get("IIUV", '')
    realname = request.args.get("realname", '')
    
    cond_by= ''
    if mobile:
       cond_by= f' WHERE m.mobile={mobile} '

    query_dict = {
        "member_id": int(member_id) if member_id else None,
        "task_id": int(task_id) if task_id else None,
        "task_order_id": int(task_order_id) if task_order_id else None,
    }
    filters = helpers.rmnullkeys(query_dict)

    flatten_filters = 'and '.join("{!s}={!r}".format(key, val)
                                for (key, val) in filters.items())

    fetch_columns = "e.id, e.amount_type, e.amounts, e.task_order_id,e.amount_type, e.add_time, m.nickname,m.IIUV,t.name as taskname,t.task_class, m.m_class,m.alipayid,m.mobile,m.nickname,m.realname,m.status as mstatus,m.reg_time"

    p_i, p_num = (page_index-1) * page_size, page_size

    where_cond = ''
    if flatten_filters:
        where_cond = f"WHERE {flatten_filters} "
        
        if start_time and end_time:
            where_cond +=f" AND add_time>'{start_time}' AND add_time<='{end_time}' "
    else:
        if start_time and end_time:
            where_cond =f" WHERE add_time>'{start_time}' AND add_time<='{end_time}' "


    earning_sql= f"SELECT {fetch_columns} FROM(SELECT id,amounts,member_id,task_order_id,task_id,amount_type,add_time FROM et_member_earnings {where_cond} ORDER BY add_time DESC ) AS e LEFT JOIN et_members AS m ON e.member_id = m.id LEFT JOIN et_tasks AS t ON e.task_id = t.id {cond_by} LIMIT {p_i},{p_num};"
    
    count_earning_sql= f"SELECT {fetch_columns} FROM(SELECT id,amounts,member_id,task_order_id,task_id,amount_type,add_time FROM et_member_earnings {where_cond} ) AS e LEFT JOIN et_members AS m ON e.member_id = m.id LEFT JOIN et_tasks AS t ON e.task_id = t.id {cond_by};"

    earnings = db.session.execute(earning_sql).fetchall()
    
    counts = db.session.execute(count_earning_sql).fetchall()
    
    res_data = dict()
    if earnings:
        res_data['list'] = [{k: v for (k, v) in row.items()}
                                       for row in earnings]
        res_data['length'] = len(counts)
        res.update(code=ResponseCode.Success, data=res_data,
                   msg=f'用户收益列表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='用户收益数据异常')
        return res.data


@route(bp, '/getorderinfo', methods=["GET"])
@login_required
def handle_orderinfo():
    """
    查询某条流水详情
    :return: json
    """
    res = ResMsg()

    order_id = int(request.args.get("id"))

    res_data = dict()

    task = db.session.query(EtMemberEarning).filter(
        EtMemberEarning.id == order_id).first()
    if task:
        res_data.update(dict(helpers.model_to_dict(task)))
        res.update(code=ResponseCode.Success, data=res_data, msg=f'收益详情获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='收益数据异常')
        return res.data


@route(bp, '/withdrawals_list', methods=["GET"])
@login_required
def handle_withdrawals_list():
    """
    用户提现列表
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))

    member_id = request.args.get("member_id", '')
    realname = request.args.get("realname", '')
    nickname = request.args.get("nickname", '')
    
    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')
    mobile = request.args.get("mobile", '')
    verify = request.args.get("verify", '')
    pay_status = request.args.get("pay_status", '')
    
    cond_by= ''
    if mobile:
       cond_by= f' WHERE m.mobile={mobile} '
    
    query_dict = {
        "member_id": member_id,
        "verify": verify,
        "pay_status": pay_status,
    }
    filters = helpers.rmnullkeys(query_dict)

    flatten_filters = 'and '.join("{!s}={!r}".format(key, val)
                                for (key, val) in filters.items())
    
    where_cond = ''
    if flatten_filters:
        where_cond = f"WHERE {flatten_filters} "
        if start_time and end_time:
            where_cond +=f" AND start_time>'{start_time}' AND start_time<='{end_time}' "
    else:
        if start_time and end_time:
            where_cond +=f" WHERE start_time>'{start_time}' AND start_time<='{end_time}'"
    
    fetch_columns= "w.id as id,w.member_id as member_id,m.id as mid, w.verify,w.verify_log,w.amounts,w.start_time,w.pay_status,w.pay_log,w.check_time,w.account,w.end_time,m.m_class,m.alipayid,m.mobile,m.nickname,m.realname,m.status as mstatus,m.reg_time,m.IIUV"
    p_i, p_num = (page_index-1) * page_size, page_size
    order_sql =f"SELECT {fetch_columns} FROM \
                    (SELECT * FROM et_member_withdrawal {where_cond}) AS w LEFT JOIN et_members AS m ON w.member_id = m.id {cond_by} ORDER BY w.start_time DESC LIMIT {p_i},{p_num} ;"
    count_order_sql =f"SELECT {fetch_columns} FROM \
                    (SELECT * FROM et_member_withdrawal {where_cond} ) AS w LEFT JOIN et_members AS m ON w.member_id = m.id {cond_by};"

    # logger.info(order_sql) 
    wd_orders = db.session.execute(order_sql).fetchall()
    count_orders=db.session.execute(count_order_sql).fetchall()

    res_data = dict()
    
    
    if wd_orders:
        res_data['list'] = [{k: v for (k, v) in row.items()}
                                       for row in wd_orders]
        res_data['length'] = len(count_orders)
        res.update(code=ResponseCode.Success,
                   data=res_data, msg=f'{order_sql}用户提现列表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='提现列表数据为空or异常')
        return res.data


@route(bp, '/withdrawals_verify', methods=["POST","OPTIONS"])
@login_required
def handle_withdrawals_verify():
    """
    用户提现审核接口
    @logic 审核完成 异步发送任务至redis队列执行支付宝付款任务
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    wd_id = int(req.get("id", 1))
    member_id = int(req.get("member_id", 1))
    status = int(req.get("status", 1))
    verify_log = str(req.get("verify_log", '数据真实有效，情节感人，通过'))

    account_name = session.get("user_name")
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    verify_orders = db.session.query(EtMemberWithdrawal).filter(
        EtMemberWithdrawal.id == wd_id, EtMemberWithdrawal.member_id == member_id).first()

    if not account_name or not verify_orders:
        res.update(code=ResponseCode.Success, data={},
                   msg=f'账户{account_name}数据异常')
        return res.data

    if not status:
        res.update(code=ResponseCode.Success, data={}, msg='未提交审核数据,操作已经撤销')
        return res.data
    pay_status=1
    if status == 2:
        pay_status=2
    
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
        user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, EtMember.realname, EtMember.mobile, EtMember.IIUV,EtMember.balance,EtMember.balance_version, EtMember.setreal, EtMember.alipayid).filter(EtMember.id == member_id).first()
        
        user_info = (dict(zip(user.keys(), user)))
        drp_config = Redis.hgetall(redis_key_drp)
        handling_fee_s = drp_config[b'handling_fee']
        handling_fee = float(str(handling_fee_s, encoding = "utf-8"))
        logger.info("handling_fee:")
        logger.info(handling_fee)
        
        # verify reject
        if status == 1:
            
            if handling_fee==0:
                add_balance= verify_orders.amounts
            else:
                handling_fee = (1- float(handling_fee) / 100)
                add_balance= round(verify_orders.amounts/handling_fee,2)
            
            if verify_orders.origin_amount:
                add_balance = verify_orders.origin_amount
            
            logger.info("add_balance:")
            logger.info(add_balance)
            
            update_dict = {
                "balance": user_info['balance'] + add_balance*100,
                "balance_version": int(time.time())
            }
            logger.info(update_dict)

            db.session.query(EtMember).filter(
                EtMember.id == member_id, EtMember.balance_version == user_info['balance_version']).update(update_dict)
            try:
                db.session.commit()
                
                Redis.delete(user_center_key + str(user_info['id']))
                Redis.delete(user_info_key + str(user_info['mobile']))

                res.update(code=ResponseCode.Success,
                           data={}, msg='该单未通过审核')
                return res.data      

            except Exception as why:
                
                res.update(code=ResponseCode.Success, data={},msg=f'审核拒绝操作数据异常{why}')
                return res.data

        db.session.commit()
        # verify pass go alipay
        if status == 2:
            if user:
                ret= async_alipay_service.delay(serial_number=wd_id, alipay_account=user_info['alipayid'], real_name=user_info['realname'], pay_amount=verify_orders.amounts, mid= member_id)

        logger.info(ret)
        res.update(code=ResponseCode.Success,
                   data=res_data, msg=f'提现审核成功,系统将发放收益到用户收款账户,请留意支付返回消息')
        return res.data

    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'用户提现订单审核失败，数据异常{why}')
        return res.data


@route(bp, '/withdrawals_verify_auto', methods=["POST"])
def handle_auto_withdrawals_verify():
    """
    APP端自动完成用户提现审核接口
    @logic 审核完成 异步发送任务至redis队列执行支付宝付款任务
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    wd_id = req.get("id", 1)
    member_id = req.get("member_id", 1)
    status = 2
    verify_log = '系统自动发放提现'

    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    verify_orders = db.session.query(EtMemberWithdrawal).filter(
        EtMemberWithdrawal.id == wd_id, EtMemberWithdrawal.member_id == member_id).first()
    
    if not verify_orders:
        res.update(code=ResponseCode.Success, data={}, msg='审核数据异常')
        return res.data

    if not status:
        res.update(code=ResponseCode.Success, data={}, msg='未提交审核数据,操作已经撤销')
        return res.data

    update_dict = {
        "verify": status,
        "verify_log": verify_log,
        "account": 'system',
        "check_time": now_timestr,
        "pay_status": 1
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)

    db.session.query(EtMemberWithdrawal).filter(
        EtMemberWithdrawal.id == wd_id).update(update_dict_ready)
    res_data = dict()
    ret=''
    try:
        user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, EtMember.realname, EtMember.mobile, EtMember.IIUV,EtMember.balance,EtMember.balance_version, EtMember.setreal, EtMember.alipayid).filter(EtMember.id == member_id).first()
        user_info = (dict(zip(user.keys(), user)))

        db.session.commit()
        # verify pass go alipay
        if status == 2:
            if user:
                ret= async_alipay_service.delay(serial_number=wd_id, alipay_account=user_info['alipayid'], real_name=user_info['realname'], pay_amount=verify_orders.amounts, mid= member_id)

        logger.info(ret)
        res.update(code=ResponseCode.Success,
                   data=res_data, msg=f'提现审核成功,系统将发放收益到用户收款账户,请留意支付返回消息')
        return res.data

    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'用户提现订单审核失败，数据异常{why}')
        return res.data


