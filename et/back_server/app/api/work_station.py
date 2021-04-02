import logging
import time
import json
from flask import Blueprint, request, session, jsonify

from app.api.task_service import calculating_earnings
from app.models import et_recharge_withdrawal
from app.models.accounts import EtAccount
from app.models.et_merchants import EtMerchants
from app.models.et_recharge_withdrawal import EtRechargeWithdrawal
from app.models.member import EtMember
from app.models.orders import EtMemberEarning
from app.models.task import EtTask, EtTaskOrder, EtTasksVerify
from app.utils.auth import login_required
from app.utils.code import ResponseCode
from app.utils.core import db, realtionlib
from app.utils.response import ResMsg
from app.utils.util import route, helpers, Redis
from app.celery import flask_app_context, async_calculating_earnings
from anytree.importer import DictImporter

bp = Blueprint("workstation", __name__, url_prefix='/workstation')

logger = logging.getLogger(__name__)

redis_key_drp = "drpconfig"
realtion_tree_key = "drp_relation_member_"

task_info_key = "tasks_info"
task_info_u_key = "tasks_info_"
task_detail_key = "tasks_detail_:"
task_complete_key = "complete_tasks_:"
complete_tasks_uid_key = "complete_tasks_"
task_verifyed_key = "verifyed_tasks_:"
tasks_high_info_key = "tasks_high_info"

user_center_key = "user_center:"
user_info_key = "user_info:"

user_withdraw_recode_key = "user_withdraw_recode:"
user_task_earnings_key = "user_task_earnings_:"


# 商家工作台创建任务
@route(bp, '/create_task', methods=["POST", "OPTIONS"])
@login_required
def handle_create_task():
    """
    商家工作台创建任务
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    taskname = req.get("name", 'tasktest1')
    status = int(req.get("status", 6))
    task_status = int(req.get("task_status", 6))
    task_class = int(req.get("task_class", 1))
    end_time = req.get("end_time", now_timestr)
    mer_id = req.get('mer_id', '')
    advance = req.get('advance', '')
    task_id = int(req.get("task_id", 1))
    begin_task_time = req.get("begin_task_time", now_timestr)
    count_tasks = req.get("count_tasks", 0)
    allow_nums = int(req.get("allow_nums", 99))
    allow_member_nums = int(req.get("allow_member_nums", 99))
    virtual_nums = int(req.get("virtual_nums", 99))
    tasks_counts = int(req.get("tasks_counts", 0))
    task_reward = float(req.get("task_reward", 99))
    task_info = req.get("task_info", '请根据任务步骤完成任务')
    task_steps = req.get("task_steps", '{"name":1}')
    tags = req.get("tags", '')
    poster_img = req.get("poster_img", 'https://qiniu.staticfile.org/user_avatar.jpg')
    sys_tags = req.get("sys_tags", '')
    task_cats = req.get("task_cats", '')
    recommend = int(req.get("recommend", 1))
    deadline_time = int(req.get("deadline_time", 99))
    check_router = req.get("check_router", '')
    task_balance = req.get("task_balance", "")
    servicefree = req.get("service_charge", "")
    # service_charge = req.get('service_charge', 0)
    tasks_id = req.get("tasks_id", "")
    add_time = req.get("add_time", "")

    res_data = dict()
    if req.get("task_reward") == None:
        res.update(code=ResponseCode.Fail, data=res_data, msg=f'任务奖励请正确输入')
        return res.data

    # servicefee_rating = 0.19
    # 计算任务服务费
    # servicefee_balance = (tasks_counts * task_reward) * (service_charge / 100)
    # logging.error(servicefee_balance)
    # total_balance = (tasks_counts * task_reward + servicefee_balance)

    # 发放任务的总费用
    total_balance = advance

    try:
        account_name = session.get("user_name")
        rest_emr = db.session.query(EtMerchants.id).filter(EtMerchants.username == account_name).first()
        et_merchants_id = rest_emr[0]
    except Exception as e:
        res.update(code=ResponseCode.Fail, data={}, msg="请登录")
        return res.data

    task = db.session.query(EtTask.id).filter(EtTask.name == account_name).first()

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(end_time) / 1000))
    begin_task_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(begin_task_time) / 1000))

    update_task_dict = {
        "name": taskname,
        "status": status,
        "task_class": task_class,
        "end_time": end_time,
        "begin_task_time": begin_task_time,
        "count_tasks": count_tasks,
        "allow_nums": allow_nums,
        "allow_member_nums": allow_member_nums,
        "tasks_counts": tasks_counts,
        "task_reward": task_reward,
        "task_info": task_info,
        "task_steps": task_steps,
        "poster_img": poster_img,
        "tags": tags,
        "sys_tags": sys_tags,
        "task_cats": task_cats,
        # "recommend": recommend,
        "deadline_time": deadline_time,
        "check_router": check_router,
        "task_balance": task_balance,
        "mer_id": et_merchants_id,
        # "mer_id": et_merchants[0],
        "servicefree": servicefree
    }
    update_task_verify_dict = {
        "tasks_id": tasks_id,
        "add_time": add_time,
    }

    logging.error(mer_id)
    # 余额
    balance_sql = f"SELECT balance,lock_balance FROM et_merchants WHERE id = {mer_id}"
    balance_q = db.session.execute(balance_sql).first()
    balance_data = dict(balance_q)

    if balance_data:
        # 余额
        all_balance = balance_data['balance'] / 100
        lock_balance_data = balance_data['lock_balance'] / 100
        logging.error(total_balance)
        if int(all_balance) < int(total_balance):
            res.update(code=ResponseCode.Fail, data={}, msg="账户金额不足，请先充值")
            return res.data
        else:
            try:
                # 更新余额
                balance = (all_balance - total_balance) * 100
                lock_balance = (lock_balance_data + total_balance) * 100

                # 冻结金额
                # lock_balance = total_balance * 100
                p = f"UPDATE et_merchants set balance={balance}, lock_balance={lock_balance} where id = {mer_id}"

                db.session.execute(p)

                # 加入流水表
                t = time.time()
                add_w_sql = f"INSERT INTO et_recharge_withdrawal (withdrawal_num, mer_id, balance, type_id, business_id) \
                VALUE ({int(t)}, {mer_id}, {total_balance}, 0, 1)"
                db.session.execute(add_w_sql)
                db.session.commit()
            except Exception as why:
                res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
                return res.data

    update_task_dict_ready = helpers.rmnullkeys(update_task_dict)
    new_task = EtTask(**update_task_dict_ready)
    db.session.add(new_task)
    db.session.flush()

    # 增加商户任务流水
    task_id = new_task.id
    new_lock = total_balance * 100
    task_sql = f"INSERT INTO et_mertask_withdrawal (task_id, lock_balance, mer_id) VALUE ({task_id},{new_lock}, {mer_id})"
    db.session.execute(task_sql)
    db.session.commit()

    update_task_verify_dict_ready = helpers.rmnullkeys(update_task_verify_dict)
    new_task_verify = EtTasksVerify(**update_task_verify_dict_ready)
    db.session.add(new_task_verify)

    try:
        db.session.commit()
        # 清缓存
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key + str(task_id))
        Redis.delete(tasks_high_info_key)
        res_data = dict()
        res.update(code=ResponseCode.Success, data=res_data, msg='新增任务成功')
        return res.data
    except Exception as why:
        res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
        return res.data


# 商家工作台任务列表
@route(bp, '/tasklist', methods=["GET"])
@login_required
def handle_tesk_list():
    """
    商家工作台任务列表
    :param:
    :return:
    """
    res = ResMsg()

    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    task_id = request.args.get("id", '')
    taskname = request.args.get("name", '')
    task_class = request.args.get("task_class", '')
    status = request.args.get("status", '')
    mer_id = request.args.get("mer_id", "")

    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')

    # 任务大分类
    task_cats = request.args.get("task_cats", '')
    sys_tags = request.args.get("sys_tags", '')
    tags = request.args.get("tags", '')

    query_dict = {
        "id": task_id,
        "name": taskname,
        "status": status,
        "task_class": task_class,
        "task_cats": task_cats,
    }
    filters = helpers.rmnullkeys(query_dict)

    tasks_counts = None

    if start_time and end_time:
        tasks = db.session.query(EtTask).filter(EtTask.mer_id == mer_id, EtTask.edit_time >= start_time,
                                                EtTask.edit_time <= end_time, EtTask.id > 1).filter_by(
            **filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()

        tasks_counts = db.session.query(EtTask).filter(EtTask.mer_id == mer_id, EtTask.edit_time >= start_time,
                                                       EtTask.edit_time <= end_time).filter_by(**filters).all()
    else:
        if not filters:
            # tasks = db.session.query(EtTask).filter(EtTask.mer_id == account_name, EtTask.status < 3, EtTask.id > 1).filter_by(**filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()
            tasks = db.session.query(EtTask).filter(EtTask.mer_id == mer_id, EtTask.id > 1).filter_by(
                **filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()

            # tasks_counts = db.session.query(EtTask).filter(EtTask.mer_id == account_name, EtTask.status < 3).filter_by(**filters).all()
            tasks_counts = db.session.query(EtTask).filter(EtTask.mer_id == mer_id).filter_by(**filters).all()
        else:
            tasks = db.session.query(EtTask).filter(EtTask.mer_id == mer_id, EtTask.id > 1).filter_by(
                **filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()

            tasks_counts = db.session.query(EtTask).filter(EtTask.mer_id == mer_id).filter_by(**filters).all()

    if tasks_counts:
        counts = (len(tasks_counts), 0)
    else:
        counts = db.session.execute(f"SELECT count(*) FROM et_tasks;").first()

    res_data = dict()
    if tasks:
        res_data['list'] = helpers.model_to_dict(tasks)
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data=res_data, msg='任务获取成功')
        return res.data
    else:
        res.update(code=ResponseCode.Fail, data={}, msg='任务数据异常or空')
        return res.data


# 提交審核
@bp.route("/commit_verify", methods=["POST"])
@login_required
def handle_commit_verify():
    """提交審核"""
    res = ResMsg()
    req = request.get_json(force=True)

    tasks_id = req.get("tasks_id", "")
    mer_id = req.get("mer_id", "")

    update_task_dict = {
        "status": 1
    }

    db.session.query(EtTask).filter(EtTask.id == tasks_id).update(update_task_dict)
    db.session.commit()
    et_task_verify_id = db.session.query(EtTasksVerify).filter(EtTasksVerify.tasks_id == tasks_id).all()
    if et_task_verify_id:
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key + str(tasks_id))
        Redis.delete(tasks_high_info_key)
        # print(EtTask.status)
        res.update(code=ResponseCode.Success, data={}, msg=f'提交审核成功')
        return jsonify(res.data)
    else:
        db.session.execute(f"INSERT INTO et_tasks_verify (tasks_id) VALUE ({tasks_id});")
        try:
            db.session.commit()
            Redis.delete(task_info_key)
            Redis.delete(task_detail_key + str(tasks_id))
            Redis.delete(tasks_high_info_key)
            # print(EtTask.status)
            res.update(code=ResponseCode.Success, data={}, msg=f'提交审核成功')
            return jsonify(res.data)
        except Exception as why:
            res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
            return jsonify(res.data)


# 上架
@bp.route("/up_shelf", methods=["POST"])
@login_required
def handle_up_shelf():
    """任务上架"""
    res = ResMsg()
    req = request.get_json(force=True)

    tasks_id = req.get("tasks_id", "")
    update_task_dict = {
        "status": 2
    }

    db.session.query(EtTask).filter(EtTask.id == tasks_id).update(update_task_dict)
    try:
        db.session.commit()
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key + str(tasks_id))
        Redis.delete(tasks_high_info_key)
        res.update(code=ResponseCode.Success, data={}, msg=f'上架成功')
        return jsonify(res.data)
    except Exception as why:
        res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
        return res.data


# 下架
@bp.route("/down_shelf", methods=["POST"])
@login_required
def handle_down_shelf():
    """任务下架"""
    res = ResMsg()
    req = request.get_json(force=True)

    tasks_id = req.get("tasks_id", "")

    select_sql = f"SELECT end_time FROM et_tasks WHERE id = {tasks_id}"
    result = db.session.execute(select_sql).first()
    dict_data = dict(result)
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    end_time = dict_data['end_time'].strftime("%Y-%m-%d %H:%M:%S")

    if end_time > now_time:
        res.update(code=ResponseCode.Fail, data={}, msg="任务尚未到截止时间")
        return jsonify(res.data)
    else:
        update_task_dict = {
            "status": 3
        }

        db.session.query(EtTask).filter(EtTask.id == tasks_id).update(update_task_dict)
        try:
            db.session.commit()
            Redis.delete(task_info_key)
            Redis.delete(task_detail_key + str(tasks_id))
            Redis.delete(tasks_high_info_key)
            res.update(code=ResponseCode.Success, data={}, msg=f'任务下架成功')
            return jsonify(res.data)
        except Exception as why:
            res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
            return res.data


# 商家工作台任务暂停
@bp.route("/task_turnoff", methods=["POST"])
@login_required
def handle_task_turnoff():
    """
    商家工作台任务暂停接口
    只有已上架的任务才有任务暂停接口
    """
    res = ResMsg()
    req = request.get_json(force=True)

    tasks_id = req.get("tasks_id", "")

    update_task_dict = {
        "status": 8
    }

    db.session.query(EtTask).filter(EtTask.id == tasks_id).update(update_task_dict)

    try:
        db.session.commit()
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key + str(tasks_id))
        Redis.delete(tasks_high_info_key)
        res.update(code=ResponseCode.Success, data={}, msg=f'任务暂停成功')
        return jsonify(res.data)
    except Exception as why:
        res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
        return res.data


# 商家工作台任务暂停取消
@bp.route("/task_turnon", methods=["POST"])
@login_required
def handle_task_turnon():
    """
    商家工作台任务暂停取消接口
    只有已上架的任务才有任务暂停接口
    :param:
    :teturn:
    """
    res = ResMsg()
    req = request.get_json(force=True)

    tasks_id = req.get("tasks_id", "")

    update_task_dict = {
        "status": 2
    }

    db.session.query(EtTask).filter(EtTask.id == tasks_id).update(update_task_dict)

    try:
        db.session.commit()
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key + str(tasks_id))
        Redis.delete(tasks_high_info_key)
        res.update(code=ResponseCode.Success, data={}, msg=f'任务取消暂停成功')
        return jsonify(res.data)
    except Exception as why:
        res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
        return res.data


# 任务加量
# @bp.route("/add_task_num", methods=["POST"])
# # @login_required
# def handle_add_task_num():
#     """任务加量"""
#     res = ResMsg()
#     req = request.get_json(force=True)
#
#     mer_id = req.get("mer_id", "")
#     tasks_id = req.get("tasks_id", "")
#     task_reward = req.get("task_reward", "")
#     tasks_counts = req.get("task_counts", "")
#     tasks_counts = req.get("task_counts", "")
#
#     add_task_num = req.get("num", "")
#     add_task_price = req.get("price", "0")
#
#     account_name = session.get("user_name")
#
#     rest_emr = db.session.query(EtMerchants.id).filter(EtMerchants.username == account_name).first()
#     add_balance = add_task_num * task_reward
#
#     if add_balance > EtMember.balance:
#         res.update(code=ResponseCode.Fail, data={}, msg='用户余额不足，添加任务失败')
#         return jsonify(res.data)
#     else:
#         total_task_counts = tasks_counts + add_task_num
#         balance = EtMember.balance - total_task_counts
#         db.session.query(EtMember).filter()
#         db.session.execute("UPDATE et_tasks SET tasks_counts={total_task_counts}")
#
#         try:
#             db.session.commit()
#             Redis.delete(task_info_key)
#             Redis.delete(task_detail_key + str(tasks_id))
#             Redis.delete(tasks_high_info_key)
#             res.update(code=ResponseCode.Success, data={}, msg=f'上架')
#             return jsonify(res.data)
#         except Exception as why:
#             res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
#             return res.data


# 资金明细
@bp.route("/detail_list", methods=["POST"])
@login_required
def handle_detail_list():
    """资金明细"""
    res = ResMsg()

    req = request.get_json(force=True)

    id = req.get("id", "")
    withdrawal_num = req.get("withdrawal_num", "")
    add_time = req.get("add_time", "")
    type_id = req.get("type_id", "")
    business_id = req.get("business_id", "")
    balance = req.get("balance", "")
    mer_id = req.get("mer_id", "")

    page_index = int(req.get("page", 1))
    page_size = int(req.get("size", 10))

    query_dict = {
        "withdrawal_num": withdrawal_num,
        "add_time": add_time,
        "business_id": business_id,
        "balance": balance
    }
    p_i, p_num = ((page_index - 1) * page_size), page_size
    filters = helpers.rmnullkeys(query_dict)
    EtRechargeWithdrawal_counts = None
    flatten_filters = ' AND '.join("{!s}={!r}".format(key, val) for (key, val) in filters.items())
    where_cond = " AND "
    if filters:
        where_cond += flatten_filters
        # withdrawal = db.session.execute(f"SELECT * FROM et_recharge_withdrawal WHERE mer_id={mer_id} {where_cond} ORDER BY add_time DESC LIMIT {p_i},{p_num};")

        withdrawal = db.session.execute(f"SELECT etm.balance AS user_balance, etw.id, etw.add_time, etw.type_id, \
        etw.business_id, etw.withdrawal_num, etw.balance \
        FROM et_recharge_withdrawal AS etw \
        LEFT JOIN et_merchants AS etm \
        ON etm.id = etw.mer_id \
        WHERE etm.id = {mer_id}").fetchall()

        withdrawal_list = [{k: v for (k, v) in row.items()} for row in withdrawal]

        EtRechargeWithdrawal_counts = db.session.execute(
            f"SELECT count(*) FROM et_recharge_withdrawal WHERE mer_id={mer_id}  {where_cond}").fetchall()

    else:
        withdrawal = db.session.execute(f"SELECT etm.balance AS user_balance, etw.id, etw.add_time, etw.type_id, \
        etw.business_id, etw.withdrawal_num, etw.balance \
        FROM et_recharge_withdrawal AS etw \
        LEFT JOIN et_merchants AS etm \
        ON etm.id = etw.mer_id \
        WHERE etm.id = {mer_id}").fetchall()

        withdrawal_list = [{k: v for (k, v) in row.items()}
                           for row in withdrawal]

        EtRechargeWithdrawal_counts = db.session.execute(
            f"SELECT count(*) FROM et_recharge_withdrawal WHERE mer_id={mer_id}").fetchall()

    if EtRechargeWithdrawal_counts:
        counts = EtRechargeWithdrawal_counts

    res_data = dict()

    if withdrawal:
        res_data['list'] = withdrawal_list
        res_data['length'] = len(counts)

        res.update(code=ResponseCode.Success, data=res_data, msg='资金明细获取成功')
        return jsonify(res.data)
    else:
        res.update(code=ResponseCode.Fail, data={}, msg='资金明细数据异常or空')
        return jsonify(res.data)


# 任务提交审核，驳回
@route(bp, '/verify_orders', methods=["POST"])
@login_required
def handle_verifytaskorder():
    """
    用户提交任务审核接口(交单)
    @todo 审核流程优化
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    mer_id = int(req.get("mer_id", ""))

    taskorder_id = int(req.get("id", 1))
    status = int(req.get("status", 4))
    verify_log = req.get("verify_log", '')

    account_name = session.get("user_name")

    if not account_name:
        res.update(code=ResponseCode.Success, data={}, msg=f'账户{account_name}数据异常')
        return res.data

    user = db.session.query(EtMerchants.id).filter(EtMerchants.username == account_name).first()

    if not status:
        res.update(code=ResponseCode.Success, data={}, msg='未提交审核数据,操作已经撤销')
        return res.data

    update_dict = {
        "status": status,
        "account_id": user.id,
        "verify_log": verify_log
    }
    task_order = db.session.query(EtTaskOrder.id, EtTaskOrder.task_id, EtTaskOrder.member_id).filter(
        EtTaskOrder.id == taskorder_id).first()

    user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, EtMember.realname,
                            EtMember.mobile, EtMember.IIUV, EtMember.balance, EtMember.balance_version,
                            EtMember.setreal, EtMember.alipayid).filter(EtMember.id == EtTaskOrder.member_id).first()
    user_info = (dict(zip(user.keys(), user)))
    memberid = EtTaskOrder.member_id
    if task_order:

        db.session.query(EtTaskOrder).filter(EtTaskOrder.id == taskorder_id).update(update_dict)
        task_order_dict = dict(zip(task_order.keys(), task_order))

        if status == 4:
            up_sql = f"UPDATE et_tasks SET tasks_fulfil = tasks_fulfil + 1 WHERE id = {task_order_dict['task_id']}"
            up_num = db.session.execute(up_sql)
            task_id = task_order.task_id
            task_data = db.session.query(EtTask.id, EtTask.task_reward).filter(EtTask.id == task_id).first()
            task_reward = task_data.task_reward * 100

            # todo zxj to change for 2020.05.02
            # 更新商户任务流水表lock_balance字段
            up_merwith_sql = f"UPDATE et_mertask_withdrawal SET lock_balance = lock_balance - {task_data.task_reward} WHERE id = {mer_id} AND task_id = {task_order_dict['task_id']}"
            up_merwith = db.session.execute(up_merwith_sql)
            db.session.commit()

            # 更新商户表lock_balance字段
            up_lock_balance_sql = f"UPDATE et_merchants SET lock_balance = lock_balance - {task_reward} WHERE id = {mer_id}"

            update_lockbalance = db.session.execute(up_lock_balance_sql)
        try:

            db.session.commit()
            res_data = dict()

            res_data.update(task_order_dict)

            u_task_key = f"user_tasks_:{task_order_dict['member_id']}"
            Redis.delete(u_task_key)
            # 驳回
            if status == 5:
                Redis.sadd(f"{task_complete_key}{task_order.task_id}", task_order.member_id)

                Redis.sadd(f"{complete_tasks_uid_key}{task_order.member_id}", task_order.task_id)

                Redis.expire(f"{task_complete_key}{task_order.task_id}", 60 * 60 * 10)
                res.update(code=ResponseCode.Success, data={}, msg='该单未通过审核')

            if status == 4:

                task_limit = 20

                counts = db.session.execute(
                    f"SELECT count(id) FROM et_task_orders WHERE status=4 AND member_id={task_order_dict['member_id']}").first()

                # update member status 2
                if int(counts[0]) == task_limit:
                    update_dict = {
                        "m_class": 2,
                    }
                    update_dict_ready = helpers.rmnullkeys(update_dict)
                    db.session.query(EtMember).filter(EtMember.id == memberid).update(update_dict_ready)
                    try:
                        db.session.commit()

                        Redis.delete(user_center_key + str(user_info['id']))
                        Redis.delete(user_info_key + str(user_info['mobile']))

                    except Exception as why:
                        res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
                        return res.data

                Redis.sadd(f"{task_verifyed_key}{task_order.task_id}", task_order.member_id)
                Redis.expire(f"{task_verifyed_key}{task_order.task_id}", 60 * 60 * 10)

                Redis.sadd(f"{task_complete_key}{task_order.task_id}", task_order.member_id)
                Redis.expire(f"{task_complete_key}{task_order.task_id}", 60 * 60 * 10)

                calculating_earnings(task_order_dict, task_order.task_id, type_set=1)

                res.update(code=ResponseCode.Success, data=res_data, msg=f'任务订单审核成功，对该用户发放收益')

            update_dict_com = {
                "status": 4,
                "account_id": user.id,
                "verify_log": verify_log
            }

            db.session.query(EtTaskOrder).filter(EtTaskOrder.id == taskorder_id).update(update_dict_com)

            return res.data
        except Exception as why:

            res.update(code=ResponseCode.Success, data={}, msg=f'任务订单审核失败,{why}')
            return res.data


# 计算该用户收益
def calculating_earnings(task_order: dict, task_id: int, type_set: int = 1):
    '''
    计算该用户收益 同时异步完成该用户 所有上级 收益更新
    #type_set 收益来源：1：任务收益 2：分销佣金 3：新手红包奖励
    '''
    res = ResMsg()
    if isinstance(task_order, dict):
        task = db.session.query(EtTask).filter(EtTask.id == task_id).first()
        logger.info('发放父亲节点收益')
        if task:
            task_dict = dict(helpers.model_to_dict(task))
            logger.info(task_dict)

            if task_dict['task_class'] == 3:
                type_set = 3

            task_earning_money = float(task_dict['task_reward'])

            earning_dict = {
                "member_id": task_order['member_id'],
                "task_id": task_id,
                "amounts": task_earning_money,
                "task_order_id": task_order['id'],
                "amount_type": type_set
            }
            logger.info(earning_dict)
            new_earning = EtMemberEarning(**earning_dict)

            isearn_sended = user = db.session.query(EtMemberEarning).filter(
                EtMemberEarning.task_order_id == task_order['id']).first()

            if isearn_sended:
                logger.info("该用户订单收益已发放")
                return "该用户订单收益已发放'"

            db.session.add(new_earning)

            user = db.session.query(EtMember).filter(
                EtMember.id == task_order['member_id']).first()

            if user.status == 2:
                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'该用户已禁用，无法获得收益'))
                return res

            if user:
                try:
                    update_dict = {
                        "balance": task_earning_money * 100 + user.balance,
                        "balance_version": int(time.time())
                    }

                    db.session.query(EtMember).filter(
                        EtMember.id == task_order['member_id'],
                        EtMember.balance_version == user.balance_version).update(update_dict)
                    db.session.commit()

                    # update user cache
                    Redis.delete(user_center_key + str(user.id))
                    Redis.delete(user_info_key + str(user.mobile))
                    Redis.delete(user_task_earnings_key + str(user.id))

                    # 缓存获取分销比例参数
                    drp_config = Redis.hgetall(redis_key_drp)
                    per_sets = json.loads(drp_config[b'profit_percentage'].decode('utf8'))

                    logger.info(per_sets)

                    # get各级分销比例
                    profit_percentage_arr = []
                    for i in range(len(per_sets)):
                        profit_percentage_arr.append(per_sets[i]['per'])

                    logger.info("比例设置：")
                    # logger.info(profit_percentage_arr)

                    # get当前用户关系树
                    rel_from_relations = db.session.execute(
                        f"SELECT * FROM et_member_relations WHERE member_id={task_order['member_id']}").first()
                    root_id = None

                    if rel_from_relations['parent_id']:
                        root_id = rel_from_relations['parent_id']

                    if rel_from_relations['top_parent_id']:
                        root_id = rel_from_relations['top_parent_id']

                    realtion_tree_key_m = realtion_tree_key + str(root_id)
                    logger.info("tree：")

                    tree_node = Redis.hget(realtion_tree_key_m, 0)
                    logger.info(str(tree_node))
                    realtion_tree_fromuser = json.loads(tree_node)

                    logger.info(str(realtion_tree_fromuser))
                    importer = DictImporter()

                    parents = []
                    realtion_tree = importer.import_(realtion_tree_fromuser)
                    cur_node_tuple = realtionlib.findall_by_attr(realtion_tree, task_order['member_id'])
                    cur_node = cur_node_tuple[0]
                    logger.info('ancestors:')
                    logger.info(str(cur_node.ancestors))

                    if cur_node.ancestors:
                        # async-task: for all parents : drp_earnings
                        for i, k in enumerate(cur_node.ancestors):
                            parents.append(k.name)
                            parentid = k.name
                            drp_level = i + 1
                            logger.info('k-name:' + str(k.name))
                            logger.info('drp_level:' + str(drp_level))
                            if drp_level < 4:
                                result = async_calculating_earnings.delay(parentid, drp_level, earning_dict, task_id,
                                                                          task_order['id'], type_set=2)

                        logger.info(parents)

                    res.update(code=ResponseCode.Success, data={}, msg=f'用户交单任务收益更新成功')
                    logger.info(res.data)
                except Exception as why:

                    res.update(code=ResponseCode.Success, data={}, msg=f'用户交单任务收益数据添加失败{why}')
                    logger.info(res.data)
            else:
                res.update(code=ResponseCode.Success, data={}, msg=f'用户信息异常{user}')


# 交单审核列表
@route(bp, '/taskorder/list', methods=["GET"])
@login_required
def handle_taskorderlist():
    """
    APP用户提交任务列表接口
    @todo 根据索引优化sql查询
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    task_id = request.args.get("task_id", '')
    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')
    mobile = request.args.get("mobile", '')
    mer_id = request.args.get("mer_id", "")

    sys_tags = request.args.get("sys_tags", '')
    tags = request.args.get("tags", '')

    order_status = request.args.get("order_status", '')

    query_dict = {
        "task_id": int(task_id) if task_id else None,
    }

    filters = helpers.rmnullkeys(query_dict)

    flatten_filters = 'and '.join("{!s}={!r}".format(key, val) for (key, val) in filters.items())
    cond_by = f'WHERE t.mer_id = {mer_id}'
    if mobile:
        cond_by = f' WHERE m.mobile={mobile} '
    # LIKE'%en%'
    cond_like = ''
    if sys_tags:
        if not mobile:
            cond_like = f" WHERE t.sys_tags LIKE'%{sys_tags}%' "
        else:
            cond_like = f" AND t.sys_tags LIKE'%{sys_tags}%' "

    if not order_status:
        where_cond = 'WHERE status> 0 '
    else:
        where_cond = f'WHERE status= {order_status} '

    if flatten_filters:
        where_cond += f" and {flatten_filters}"

        if start_time and end_time:
            where_cond += f' and add_time>{start_time} or add_time<={end_time} '
    else:
        if start_time and end_time:
            where_cond += f' and add_time>{start_time} or add_time<={end_time} '

    fetch_columns = "o.id,o.task_id,o.member_id,o.status as order_status,o.user_submit,o.add_time,o.submit_time,o.account_id,o.app_safe_info,o.safe_token,o.confidence, t.name as taskname,t.task_class, t.status as task_status, t.task_reward,t.deadline_time,m.nickname,m.realname,m.mobile,m.m_class,m.setreal,m.alipayid"

    p_i, p_num = (page_index - 1) * page_size, page_size

    task_sql = f"SELECT {fetch_columns} FROM \
                    (SELECT * FROM et_task_orders {where_cond} ) AS o \
                    LEFT JOIN et_members AS m ON o.member_id =m.id \
                    LEFT JOIN et_tasks AS t ON o.task_id =t.id {cond_by} {cond_like} ORDER BY o.submit_time DESC LIMIT {p_i},{p_num} ;"

    task_counts_sql = f"SELECT {fetch_columns} FROM \
                    (SELECT * FROM et_task_orders {where_cond}) AS o \
                    LEFT JOIN et_members AS m ON o.member_id =m.id \
                    LEFT JOIN et_tasks AS t ON o.task_id =t.id {cond_by} {cond_like};"

    task_orders = db.session.execute(task_sql).fetchall()
    task_counts = db.session.execute(task_counts_sql).fetchall()

    res_data = dict()
    # counts = db.session.execute(f"SELECT count(*) FROM et_task_orders {where_cond}").first()

    if task_orders:
        # result: RowProxy to dict
        res_data['list'] = [{key: value for (key, value) in row.items()} for row in task_orders]
        task_counts_list = [{key: value for (key, value) in row.items()} for row in task_counts]
        # logger.info(res_data['list'])
        res_data['length'] = len(task_counts_list)  # task_counts[0]

        res.update(code=ResponseCode.Success, data=res_data,
                   msg=f'{task_counts_sql}用户提交任务列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg=f'{task_sql}任务数据为空')
        return res.data


# user_info
@route(bp, '/member_info', methods=["POST"])
@login_required
def show_member_info():
    """商家工作台显示商家信息"""
    res = ResMsg()

    req = request.get_json(force=True)

    mer_id = req.get("mer_id", "")

    account_name = session.get("user_name")

    if not account_name:
        res.update(code=ResponseCode.Success, data={}, msg=f'账户{account_name}数据异常')
        return res.data

    # user = db.session.query(EtMerchants.id).filter(EtMerchants.accounts_name == account_name).first()
    u_sql = f"SELECT SUM(t1.task_verifying) as task_ver,SUM(t1.task_completes) as task_com,SUM(t1.task_refused) as task_re,\
            em.username,em.balance,em.lock_balance FROM (SELECT \
                SUM( IF ( STATUS = 4, 1, 0 ) ) AS task_completes, \
                    SUM( IF ( STATUS = 2, 1, 0 ) ) AS task_verifying, \
                        SUM( IF ( STATUS = 5, 1, 0 ) ) AS task_refused, \
                            task_id \
                                FROM \
                                et_task_orders \
                                GROUP BY \
                                 ( task_id ) \
                                ) as t1 \
                                LEFT JOIN et_tasks as et on t1.task_id=et.id \
                                LEFT JOIN et_merchants as em on em.id=et.mer_id \
                                WHERE em.id = {mer_id} \
                                GROUP BY em.username,em.balance,em.lock_balance"
    user_info_t = db.session.execute(u_sql).first()
    if user_info_t:
        user_info_t = dict(user_info_t)
    u_sql = f"SELECT username,balance,lock_balance from et_merchants where id = {mer_id}"
    # balance 商户余额
    # lock_balance 商户的冻结总额
    # 总资产 balance+ lock_balance
    user_info = db.session.execute(u_sql).first()

    # 已发布任务数
    republish_task_num = db.session.execute(
        f"SELECT COUNT(id) as task_couns from et_tasks WHERE mer_id={mer_id}").first()
    count_task = dict(republish_task_num)["task_couns"]
    user_info_s = dict(user_info)
    res_data = dict()
    if user_info:
        res_data["user_info_td"] = user_info_s
        res_data["user_info_tast"] = user_info_t
        res_data['task_count'] = count_task
        res.update(code=ResponseCode.Success, data=res_data, msg=f"{res_data}获取成功")
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
        return res.data


# 商家工作台提交定单审核
@route(bp, '/verify_order', methods=["GET"])
@login_required
def handle_verify_order():
    """
    商家工作台提交定单审核
    :param:
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    taskorder_id = int(req.get("id", 1))
    status = int(req.get("status", 1))
    verify_log = req.get("verify_log", '')

    account_name = session.get("user_name")

    if not account_name:
        res.update(code=ResponseCode.Success, data={}, msg=f'账户{account_name}数据异常')
        return res.data

    user = db.session.query(EtAccount.id).filter(EtAccount.name == account_name).first()

    if not status:
        res.update(code=ResponseCode.Success, data={}, msg='未提交审核数据,操作已经撤销')
        return res.data

    update_dict = {
        "status": status,
        "account_id": user.id,
        "verify_log": verify_log
    }
    task_order = db.session.query(EtTaskOrder.id, EtTaskOrder.task_id, EtTaskOrder.member_id).filter(
        EtTaskOrder.id == taskorder_id).first()

    user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, EtMember.realname,
                            EtMember.mobile, EtMember.IIUV, EtMember.balance, EtMember.balance_version,
                            EtMember.setreal, EtMember.alipayid).filter(EtMember.id == EtTaskOrder.member_id).first()
    user_info = (dict(zip(user.keys(), user)))

    if task_order:

        db.session.query(EtTaskOrder).filter(EtTaskOrder.id == taskorder_id).update(update_dict)
        task_order_dict = dict(zip(task_order.keys(), task_order))

        if status == 4:
            up_sql = f"UPDATE et_tasks SET tasks_fulfil = tasks_fulfil+1 WHERE id={task_order_dict['task_id']}"
            up_num = db.session.execute(up_sql)

        try:

            db.session.commit()
            res_data = dict()

            res_data.update(task_order_dict)

            u_task_key = f"user_tasks_:{task_order_dict['member_id']}"
            Redis.delete(u_task_key)

            if status == 5:
                Redis.sadd(f"{task_complete_key}{task_order.task_id}", task_order.member_id)

                Redis.sadd(f"{complete_tasks_uid_key}{task_order.member_id}", task_order.task_id)

                Redis.expire(f"{task_complete_key}{task_order.task_id}", 60 * 60 * 10)
                res.update(code=ResponseCode.Success, data={}, msg='该单未通过审核')

            if status == 4:

                task_limit = 20

                counts = db.session.execute(
                    f"SELECT count(id) FROM et_task_orders WHERE status=4 AND member_id={task_order_dict['member_id']}").first()

                # update member status 2
                if int(counts[0]) == task_limit:
                    update_dict = {
                        "m_class": 2,
                    }
                    update_dict_ready = helpers.rmnullkeys(update_dict)
                    db.session.query(EtMember).filter(EtMember.id == task_order.member_id).update(update_dict_ready)
                    try:
                        db.session.commit()

                        Redis.delete(user_center_key + str(user_info['id']))
                        Redis.delete(user_info_key + str(user_info['mobile']))

                    except Exception as why:
                        res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
                        return res.data

                Redis.sadd(f"{task_verifyed_key}{task_order.task_id}", task_order.member_id)
                Redis.expire(f"{task_verifyed_key}{task_order.task_id}", 60 * 60 * 10)

                Redis.sadd(f"{task_complete_key}{task_order.task_id}", task_order.member_id)
                Redis.expire(f"{task_complete_key}{task_order.task_id}", 60 * 60 * 10)

                calculating_earnings(task_order_dict, task_order.task_id, type_set=1)

                res.update(code=ResponseCode.Success, data=res_data, msg=f'任务订单审核成功，对该用户发放收益')

            update_dict_com = {
                "status": 4,
                "account_id": user.id,
                "verify_log": verify_log
            }

            db.session.query(EtTaskOrder).filter(EtTaskOrder.id == taskorder_id).update(update_dict_com)

            return res.data
        except Exception as why:

            res.update(code=ResponseCode.Success, data={}, msg=f'任务订单审核失败,{why}')
            return res.data


# 商家工作台资金明细
@bp.route('/detail', methods=["GET"])
# @login_required
def detail_accounts():
    """资金明细接口
    :param:
    :return:
    """
    # pass
    res = ResMsg()
    req = request.get_json(force=True)

    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    id = req.get("id", "")
    accounts_name = req.get("accounts_name", "")
    withdrawal_num = req.get("withdrawal_num", "")
    add_time = req.get("add_time", "")
    mer_id = req.get("mer_id", "")
    balance = req.get("balance", "")
    business_id = req.get("business_id", "")
    type_id = req.get("type_id", "")

    start_time = req.get("start_time", "")
    end_time = req.get("end_time", "")

    account_name = session.get("user_name")

    if not account_name:
        res.update(code=ResponseCode.Success, data={}, msg=f'账户{account_name}数据异常')
        return res.data

    user = db.session.query(EtRechargeWithdrawal.id).filter(EtRechargeWithdrawal.accounts_name == account_name).first()

    query_dict = {
        "id": id,
        "accounts_name": accounts_name,
        "withdrawal_num": withdrawal_num,
        "add_time": add_time,
        "mer_id": mer_id,
        "balance": balance,
        "business_id": business_id,
        "type_id": type_id
    }

    filters = helpers.rmnullkeys(query_dict)
    recharge_withdrawal = None

    if start_time and end_time:
        recharge_withdrawal = db.session.query(EtRechargeWithdrawal).filter(EtRechargeWithdrawal.add_time >= start_time,
                                                                            EtRechargeWithdrawal.add_time <= end_time,
                                                                            EtRechargeWithdrawal.id > 1).filter_by(
            **filters).order_by(
            EtRechargeWithdrawal.add_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()

    else:
        if not filters:
            recharge_withdrawal = db.session.query(EtRechargeWithdrawal).filter(EtRechargeWithdrawal.type_id < 2,
                                                                                EtRechargeWithdrawal.business_id < 3).filter_by(
                **filters).order_by(
                EtRechargeWithdrawal.add_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()
        # else:
        #     recharge_withdrawal = db.session.query(EtRechargeWithdrawal).filter(EtRechargeWithdrawal.type_id > 1).filter_by(**filters).order_by(
        #         EtRechargeWithdrawal.add_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()

    if recharge_withdrawal:
        counts = (len(recharge_withdrawal), 0)
    else:
        counts = db.session.execute("SELECT count(*) FROM et_recharge_withdrawal").first()

    res_data = dict()

    if recharge_withdrawal:
        res_data['list'] = helpers.model_to_dict(recharge_withdrawal)
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data=res_data, msg='数据获取成功')
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='资金明细数据异常or空')
        return res.data



# 任务列表中任务删除
@bp.route('/remove_task', methods=["POST"])
@login_required
def handle_remove_task():
    """任务删除"""
    res = ResMsg()
    req = request.get_json(force=True)

    # id = req.get("id", "")
    task_id = req.get("id", "")
    # task_name = req.get("name", "")
    task_status = req.get("status", "")
    # task_reward = req.get("task_reward", "")
    # tasks_counts = req.get("task_counts", "")
    # count_tasks = req.get("count_tasks", "")
    mer_id = req.get("mer_id", "")

    query_dict = {
        # "id": id,
        "task_id": task_id,
        "mer_id": mer_id,
        # "task_name": task_name,
        "task_status": task_status,
        # "task_reward": task_reward,
        # "tasks_counts": tasks_counts,
        # "count_tasks": count_tasks,
    }

    filters = helpers.rmnullkeys(query_dict)

    update_status_dict = {
        "status": 4,
    }
    account_name = session.get("user_name")
    # account_name = "测试一号"
    # 过滤掉正在审核的任务和已经删除的任务
    if task_status != 4 and task_status != 2:
        # 前端传递数据过来
        if filters:
            lock_balance = db.session.execute(f"SELECT lock_balance FROM et_mertask_withdrawal WHERE mer_id={mer_id} AND task_id = {task_id}").first()

            # etmer_data = db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).first()
            res_data = {}
            if account_name:
                # task = db.session.execute(f"SELECT * FROM et_tasks WHERE id={task_id}")
                task = db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).first()

                # print(task.balance)

                # 删除任务，逻辑删除，只修改任务状态，同时返还商户的消费金额到冻结金额中
                # 计算返还的金额：任务数量*任务奖励-已发放的任务奖励
                # back_task_balance = int(task.tasks_counts) * int(task.task_reward) - int(task.count_tasks) * int(task.task_reward)
                # back_task_balance = task.tasks_counts * task.task_reward

                # 冻结金额
                update_lock_balance = lock_balance[0]
                # 将未完成任务的金额从冻结资金中返还到商户可用余额
                balance = task.balance + update_lock_balance
                update_lock_balance_ready = task.lock_balance - update_lock_balance
                update_lock_balance_dict = {
                    "balance": balance,
                    "lock_balance": update_lock_balance_ready,
                }
                # 更新任务状态：任务删除状态为4
                db.session.query(EtTask).filter(EtTask.id == task_id).update(update_status_dict)

                # 更新商户冻结资金
                db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).update(update_lock_balance_dict)

                # 加入流水表记录：资金流水为删除，收入
                t = time.time()
                add_w_sql = f"INSERT INTO et_recharge_withdrawal (withdrawal_num, mer_id, balance, type_id, business_id) VALUE ({int(t)}, {mer_id}, {update_lock_balance}, 0, 1)"
                db.session.execute(add_w_sql)

                try:
                    db.session.commit()
                    # 删除redis缓存
                    Redis.delete(task_info_key)
                    Redis.delete(task_detail_key + str(task_id))
                    Redis.delete(tasks_high_info_key)
                    res.update(code=ResponseCode.Success, data={}, msg="删除任务成功")
                    return jsonify(res.data)
                except Exception as e:
                    res.update(code=ResponseCode.Fail, data={}, msg=f"删除任务失败{e}")
                    return jsonify(res.data)
            else:
                res.update(code=ResponseCode.Fail, data={}, msg="请先登录")
                return jsonify(res.data)
        else:
            res.update(code=ResponseCode.Fail, data={}, msg="数据获取异常")
            return jsonify(res.data)
    else:
        res.update(code=ResponseCode.Fail, data={}, msg="操作异常")
        return jsonify(res.data)



# 任务加量
@bp.route("/add_task_num", methods=["POST"])
@login_required
def handle_add_task_num():
    """任务加量"""
    res = ResMsg()
    req = request.get_json(force=True)

    task_id = req.get("id", "")
    task_reward = req.get("task_reward","")
    tasks_counts = req.get("task_counts", "")
    task_balance = req.get("task_balance", "")
    task_status = req.get("status", "")
    mer_id = req.get("mer_id", "")

    add_task_num = int(req.get("task_counts", ""))
    add_task_price = int(req.get("task_money", "0"))


    query_dict = {
        "id": task_id,
        "status": task_status,
        "mer_id": mer_id,
        "add_task_num": add_task_num,
        "add_task_price": add_task_price
    }

    filters = helpers.rmnullkeys(query_dict)

    account_name = session.get("user_name")
    # account_name = "测试二号"
    if account_name:
        user = db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).first()
        # 只有上架任务才有加量status:2
        if task_status == 2 or task_status == 8:
            if filters:
                task = db.session.query(EtTask).filter(EtTask.id == task_id).first()
                # 加价后的单个任务奖励
                added_task_price = task.task_balance

                # 加价总额
                add_balance = add_task_num * (added_task_price * 100)

                if add_balance > user.balance:
                    res.update(code=ResponseCode.Fail, data={}, msg='用户余额不足，任务加量失败')
                    return jsonify(res.data)
                else:
                    update_tasks_counts = task.tasks_counts + add_task_num
                    # total_cost_balance = task.task_balance + add_balance
                    # 更新任务表：任务数量，任务价格，任务总金额
                    update_task_dict = {
                        "status": task_status,
                        # "task_balance": total_cost_balance,
                        "tasks_counts": update_tasks_counts,
                    }
                    db.session.query(EtTask).filter(EtTask.id == task_id).update(update_task_dict)

                    etm_data = db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).first()

                    update_balance = etm_data.balance - add_balance
                    update_lock_balance = etm_data.lock_balance + add_balance
                    # 更新商户表记录：余额，冻结金额
                    update_et_merchants_dict = {
                        "balance": update_balance,
                        "lock_balance": update_lock_balance,
                    }
                    db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).update(update_et_merchants_dict)

                    # 加入流水表记录：资金流水为加量，支出
                    t = time.time()
                    add_w_sql = f"INSERT INTO et_recharge_withdrawal (withdrawal_num, mer_id, balance, type_id, business_id) VALUE ({int(t)}, {mer_id}, {add_balance}, 4, 0)"
                    db.session.execute(add_w_sql)

                    try:
                        db.session.commit()
                        Redis.delete(task_info_key)
                        Redis.delete(task_detail_key + str(task_id))
                        Redis.delete(tasks_high_info_key)
                        res.update(code=ResponseCode.Success, data={}, msg="任务加量成功")
                        return jsonify(res.data)
                    except Exception as why:
                        res.update(code=ResponseCode.Fail, data={}, msg=f'任务数据异常{why}')
                        return jsonify(res.data)
            else:
                res.update(code=ResponseCode.Fail, data={}, msg="任务数据异常")
                return jsonify(res.data)
        else:
            res.update(code=ResponseCode.Fail, data={}, msg="任务状态异常")
            return jsonify(res.data)
    else:
        res.update(code=ResponseCode.Fail, data={}, msg="请登录")
        return jsonify(res.data)


# 商户工作台提交结算
@bp.route("/task_settleaccount", methods=["POST"])
@login_required
def handle_task_settle_account():
    """
    商户工作台任务提交结算
    :param:
    :return:
    """
    res = ResMsg()
    req = request.get_json(force=True)

    task_id = req.get("task_id", "")
    task_status = req.get("status", "")
    mer_id = req.get("mer_id", "")

    query_dict = {
        "task_id": task_id,
        "mer_id": mer_id,
        "status": task_status,
    }

    filters = helpers.rmnullkeys(query_dict)

    account_name = session.get("user_name")
    # account_name = "测试二号"
    if not account_name:
        res.update(code=ResponseCode.Fail, data={}, msg="请登录")
        return jsonify(res.data)
    else:
        if filters:
            # select_sql = f"SELECT end_time FROM et_tasks WHERE id = {task_id}"
            # result = db.session.execute(select_sql).first()
            # dict_data = dict(result)
            # now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # end_time = dict_data['end_time'].strftime("%Y-%m-%d %H:%M:%S")
            # if end_time > now_time:
            #     res.update(code=ResponseCode.Fail, data={}, msg="任务尚未到截止时间")
            #     return jsonify(res.data)
            # else:
            if task_status == 3:
                update_status_dict = {
                    "status": 9
                }
                db.session.query(EtTask).filter(EtTask.id == task_id).update(update_status_dict)
                lock_balance = db.session.execute(f"SELECT lock_balance FROM et_mertask_withdrawal WHERE mer_id={mer_id} AND task_id={task_id}").first()
                task_balance, task_lock_balance = db.session.execute(f"SELECT balance, lock_balance FROM et_merchants WHERE id={mer_id}").first()
                update_balance = task_balance + lock_balance[0]
                update_lock_balance = task_lock_balance - lock_balance[0]
                # updat_etm_dict = {
                #     "balance": update_balance,
                #     "lock_balance": update_lock_balance,
                # }
                # 更新商户表
                # db.session.query(EtMerchants).filter(EtMerchants.id == mer_id).update(updat_etm_dict)
                db.session.execute(f"UPDATE et_merchants SET balance={update_balance}, lock_balance={update_lock_balance} WHERE id={mer_id}")

                # 加入商户流水表记录：资金流水为结算，收入
                t = time.time()
                add_w_sql = f"INSERT INTO et_recharge_withdrawal (withdrawal_num, mer_id, balance, type_id, business_id) VALUE ({int(t)}, {mer_id}, {lock_balance[0]}, 3, 1)"
                db.session.execute(add_w_sql)

                try:
                    db.session.commit()
                    Redis.delete(task_info_key)
                    Redis.delete(task_detail_key + str(task_id))
                    Redis.delete(tasks_high_info_key)
                    res.update(code=ResponseCode.Success, data={}, msg="任务结算成功")
                    return jsonify(res.data)
                except Exception as why:
                    res.update(code=ResponseCode.Fail, data={}, msg=f"结算失败{why}")
                    return jsonify(res.data)
            else:
                res.update(code=ResponseCode.Fail, data={}, msg="任务状态异常")
                return jsonify(res.data)
        else:
            res.update(code=ResponseCode.Fail, data={}, msg="数据异常")
            return jsonify(res.data)

