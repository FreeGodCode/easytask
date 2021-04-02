import json
import logging
import time

# from app.models.drp import EtMemberDrp
from flask import Blueprint, request

# from app.models.task import EtTask
# from app.models.task import EtTaskOrder
# from app.models.task import EtTasksVerify
# from app.models.accounts import EtAccount
# from app.models.member import EtMember
# from app.models.orders import EtMemberEarning
from app.models.activity import EtActivity, ActivityRewards
from app.utils.auth import login_required
from app.utils.code import ResponseCode
from app.utils.core import db
from app.utils.response import ResMsg
from app.utils.util import route, helpers

# from app.celery import flask_app_context, async_calculating_earnings
# from anytree.importer import DictImporter


bp = Blueprint("activity", __name__, url_prefix='/activity')
# 运营平台管理运营活动服务

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


@route(bp, '/liststat', methods=["GET"])
@login_required
def handle_list_stat():
    """
    活动数据统计列表接口
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))
    name = request.args.get("act_name", '')
    act_id = 1

    if name:
        the_act = db.session.execute(f"SELECT id FROM et_activity WHERE act_name='{name}'").first()
        if the_act:
            act_id = the_act[0]
        else:

            res.update(code=ResponseCode.Success, data={}, msg='活动数据统计数据为空or异常')
            return res.data

    p_i, p_num = (page_index - 1) * page_size, page_size

    feedlist = db.session.execute(
        f"SELECT a.id, a.member_id, a.invite_count, a.activity_id, a.rank_num, a.avatar, a.bonus, a.pay_status, a.fake, m.avatar as avatar2,m.status,m.IIUV,m.realname,m.mobile,act.act_name,act.act_type,act.status as act_status FROM activity_rewards as a LEFT JOIN et_members as m on a.member_id =m.id LEFT JOIN et_activity as act on act.id=a.activity_id WHERE a.activity_id={act_id} ORDER BY a.rank_num ASC LIMIT {p_i},{p_num}").fetchall()

    counts = db.session.execute(
        "SELECT count(*) FROM activity_rewards").first()
    res_data = dict()

    if feedlist:
        res_data['list'] = [{key: value for (key, value) in row.items()} for row in feedlist]
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data=res_data, msg='活动数据统计列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='活动数据统计数据为空or异常')
        return res.data


@route(bp, '/list', methods=["GET"])
@login_required
def handle_list():
    """
    活动列表接口
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    p_i, p_num = (page_index - 1) * page_size, page_size

    feedlist = db.session.execute(f"SELECT * FROM et_activity ORDER BY create_time DESC LIMIT {p_i},{p_num}").fetchall()

    counts = db.session.execute(
        "SELECT count(*) FROM et_activity").first()
    res_data = dict()

    if feedlist:
        res_data['list'] = [{key: value for (key, value) in row.items()} for row in feedlist]
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data=res_data, msg='活动列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='活动列表数据为空or异常')
        return res.data


@route(bp, '/getinfo', methods=["GET"])
@login_required
def handle_info():
    """
    查询任务详情
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))
    act_id = int(request.args.get("id", 10))
    p_i, p_num = (page_index - 1) * page_size, page_size

    act_info = db.session.query(EtActivity).filter(EtActivity.id == act_id).first()

    res_data = dict()

    if feedlist:
        res_data['data'] = helpers.model_to_dict(act_info)
        res.update(code=ResponseCode.Success, data=res_data, msg='活动获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='活动数据为空or异常')
        return res.data


@route(bp, '/add_act', methods=["POST", "OPTIONS"])
@login_required
def handle_add_act():
    """
    新增活动接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    act_name = req.get("act_name", 'tasktest1')
    act_type = int(req.get("act_type", 1))
    status = req.get("status", 1)
    create_time = req.get("create_time", now_timestr)

    round_num = req.get("round_num", '')
    limits = req.get("limits", 10)
    act_duration = req.get("act_duration", 2)
    rules = req.get("rules", '')

    update_dict = {
        "act_name": act_name,
        "act_type": act_type,
        "status": status,
        "create_time": create_time,
        "round_num": round_num,
        "act_duration": act_duration,
        "rules": rules,
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)

    new_act = EtActivity(**update_dict_ready)
    db.session.add(new_act)
    try:
        db.session.commit()
        act_id = new_act.id
        config = {"page_show": limits}
        configs = json.dumps(config)
        insert_sql = f"INSERT INTO et_activity_configs (act_id, act_configs) VALUES ({act_id}, '{configs}')"
        db.session.execute(insert_sql)
        db.session.commit()
        res_data = dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'新增活动成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={}, msg=f'活动数据异常{why}')
        return res.data


@route(bp, '/edit_act', methods=["POST", "OPTIONS"])
@login_required
def handle_edit_act():
    """
    活动修改编辑接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    act_id = req.get("id", 1)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    act_name = req.get("name", '')
    act_type = req.get("act_type", '')
    status = req.get("status", '')
    create_time = req.get("create_time", now_timestr)

    round_num = req.get("round_num", '')
    act_duration = req.get("act_duration", 2)
    rules = req.get("rules", '')

    update_dict = {
        "act_name": act_name,
        "act_type": act_type,
        "status": status,
        "create_time": create_time,
        "round_num": round_num,
        "act_duration": act_duration,
        "rules": rules,
    }

    update_dict_ready = helpers.rmnullkeys(update_dict)
    db.session.query(EtActivity).filter(EtActivity.id == act_id).update(update_dict_ready)
    try:
        db.session.commit()

        res_data = dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'活动修改成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={}, msg=f'活动修改失败，数据异常{why}')
        return res.data


@route(bp, '/up_status', methods=["POST", "OPTIONS"])
@login_required
def handle_upstatus():
    """
    活动更新状态信息
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    act_id = req.get("id", '')
    status = req.get("status", '')

    update_dict = {
        "status": status,
    }
    db.session.query(EtActivity).filter(EtActivity.id == act_id).update(update_dict)
    try:
        db.session.commit()

        res_data = dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'活动状态更新成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={}, msg=f'活动状态修改失败，数据异常{why}')
        return res.data


@route(bp, '/set_reward', methods=["POST"])
@login_required
def handle_reward_setting():
    """
    发放排行榜活动奖励
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    rank_id = req.get("id", '')
    bonus = req.get("bonus", '')
    member_id = req.get("member_id", '')
    invite_count = req.get("invite_count", '')
    rank_num = req.get("rank_num", '')
    activity_id = req.get("activity_id", '')
    avatar = req.get("avatar", '')

    update_dict = {
        "invite_count": invite_count,
        "bonus": int(bonus),
        "rank_num": rank_num,
        "activity_id": activity_id,
        "avatar": avatar,
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)

    db.session.query(ActivityRewards).filter(ActivityRewards.id == rank_id).update(update_dict_ready)

    try:
        db.session.commit()

        res_data = dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'奖励更新成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={}, msg=f'奖励修改失败，数据异常{why}')
        return res.data


@route(bp, '/add_faker', methods=["POST"])
@login_required
def handle_reward_faker():
    """
    排行榜添加虚拟用户数据
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    # rank_id= req.get("id", '')
    bonus = req.get("bonus", 1)
    member_id = req.get("member_id", 1)
    invite_count = req.get("invite_count", 1)
    rank_num = req.get("rank_num", '')
    activity_id = req.get("activity_id", 1)
    avatar = req.get("avatar", 1)

    update_dict = {
        "member_id": 1,
        "invite_count": invite_count,
        "bonus": int(bonus),
        "fake": 1,
        "rank_num": rank_num,
        "activity_id": activity_id,
        "avatar": avatar,
        "pay_status": 0,
    }

    # db.session.query(ActivityRewards).filter(ActivityRewards.id == rank_id).update(update_dict)
    new_ActivityRewards = ActivityRewards(**update_dict)
    db.session.add(new_ActivityRewards)

    try:
        db.session.commit()

        res_data = dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'虚拟用户数据添加成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={}, msg=f'虚拟用户数据添加失败，数据异常{why}')
        return res.data
