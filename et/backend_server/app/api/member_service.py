# import hashlib
# import time
import logging

# from app.models.member import EtMemberExtend
from flask import Blueprint, request

from app.models.member import EtMember
from app.utils.auth import login_required
from app.utils.code import ResponseCode
from app.utils.core import db
from app.utils.response import ResMsg
from app.utils.util import Redis, helpers

bp = Blueprint("members", __name__, url_prefix='/members')
# 运营平台app用户服务
logger = logging.getLogger(__name__)
user_center_key = "user_center:"
user_info_key = "user_info:"
balck_list_key = "balck_list"


@bp.route('/getusers', methods=["GET"])
@login_required
def handle_getusers():
    """
    获取账号详情
    :return: json
    """
    res = ResMsg()
    memberid = int(request.args.get("id"))

    res_data = dict()

    user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, \
                            EtMember.realname, EtMember.mobile, EtMember.IIUV, EtMember.setreal).filter(
        EtMember.id == memberid).first()

    if user:
        res_data.update(dict(zip(user.keys(), user)))
        res.update(code=ResponseCode.Success, data=res_data, msg='获取成功')
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='账户异常')
        return res.data


@bp.route('/list', methods=["GET"])
@login_required
def handle_getuserlists():
    """
    获取用户列表
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')

    nickname = request.args.get("nickname", '')
    realname = request.args.get("realname", '')
    mobile = request.args.get("mobile", '')
    id_numbers = request.args.get("id_numbers", '')
    status = request.args.get("status", '')
    IIUV = request.args.get("IIUV", '')
    setreal = request.args.get("setreal", '')
    alipay_id = request.args.get("alipay_id", '')
    m_class = request.args.get("m_class", '')

    query_dict = {
        "nickname": nickname,
        "realname": realname,
        "mobile": mobile,
        "status": status,
        "m_class": m_class,
        "IIUV": IIUV,
        'setreal': setreal,
        'alipay_id': alipay_id
    }
    filters = helpers.rmnullkeys(query_dict)
    p_i, p_num = (page_index - 1) * page_size, page_size

    if start_time and end_time:
        if not IIUV:
            members = db.session.query(EtMember).filter(EtMember.reg_time >= start_time,
                                                        EtMember.reg_time <= end_time).filter_by(**filters).order_by(
                EtMember.reg_time.desc()).limit(page_size).offset((page_index - 1) * page_size).all()

            count_members = db.session.query(EtMember).filter(EtMember.reg_time >= start_time,
                                                              EtMember.reg_time <= end_time).filter_by(**filters).all()
            mlists = helpers.model_to_dict(members)
        else:
            del filters['IIUV']
            where_cond = ''
            if filters:
                where_cond += 'AND '
                where_cond += 'AND '.join("m.{!s}={!r}".format(key, val)
                                          for (key, val) in filters.items())

            where_cond += f' AND m.reg_time>{start_time} AND m.reg_time<={end_time} '

            members = db.session.query(EtMember).filter(EtMember.IIUV == IIUV).first()
            mem_sql = f'SELECT * FROM `et_member_relations` as dr LEFT JOIN et_members as m on dr.member_id=m.id WHERE dr.parent_id={members.id} {where_cond} ORDER BY m.reg_time DESC  LIMIT {p_i},{p_num}'

            members_more = db.session.execute(mem_sql).fetchall()
            mlists = [{k: v for (k, v) in row.items()} for row in members_more]
            count_members = mlists

    else:
        if not IIUV:
            members = db.session.query(EtMember).filter_by(**filters).order_by(EtMember.reg_time.desc()).limit(
                page_size).offset((page_index - 1) * page_size).all()

            count_members = db.session.query(EtMember).filter_by(**filters).all()
            mlists = helpers.model_to_dict(members)
        else:
            del filters['IIUV']
            where_cond = ''
            if filters:
                where_cond += 'AND '
                where_cond += 'AND '.join("m.{!s}={!r}".format(key, val)
                                          for (key, val) in filters.items())

            members = db.session.query(EtMember).filter(EtMember.IIUV == IIUV).first()

            if not members:
                res.update(code=ResponseCode.Success, data={}, msg='数据获取异常')
                return res.data

            mem_sql = f'SELECT * FROM `et_member_relations` as dr LEFT JOIN et_members as m on dr.member_id=m.id WHERE dr.parent_id={members.id} {where_cond} ORDER BY m.reg_time DESC LIMIT {p_i},{p_num}'

            members_more = db.session.execute(mem_sql).fetchall()
            mlists = [{k: v for (k, v) in row.items()} for row in members_more]
            count_members = mlists

    res_data = dict()
    if members:
        res_data['list'] = mlists
        res_data['length'] = len(count_members)
        res.update(code=ResponseCode.Success, data=res_data, msg=f'{len(count_members)}获取成功')
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='数据获取异常')
        return res.data


@bp.route('/edit_user', methods=["POST", "OPTIONS"])
@login_required
def handle_edituser():
    """
    用户信息修改接口
    :return: json 
    """
    res = ResMsg()
    req = request.get_json(force=True)
    memberid = req.get("id")
    status = req.get("status")
    username = req.get("username")

    update_dict = {
        "name": username,
        "status": status,
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)
    user = db.session.query(EtMember).filter(EtMember.id == memberid).first()
    if user:
        db.session.query(EtMember).filter(EtMember.id == memberid).update(update_dict_ready)
        try:
            db.session.commit()
            Redis.delete(user_center_key + str(user.id))
            Redis.delete(user_info_key + str(user.mobile))
            res.update(code=ResponseCode.Success, data={}, msg='修改成功')
            return res.data
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
            return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='修改失败，请稍后再试')
        return res.data


@bp.route('/ban_user', methods=["POST", "OPTIONS"])
@login_required
def handle_banuser():
    """
    封禁用户
    :return: json 
    """
    res = ResMsg()
    req = request.get_json(force=True)

    memberid = req.get("id")
    status = req.get("status")

    update_dict = {
        "status": status,
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)
    user = db.session.query(EtMember).filter(EtMember.id == memberid).first()

    if user:
        db.session.query(EtMember).filter(EtMember.id == memberid).update(update_dict_ready)
        try:
            db.session.commit()
            Redis.delete(user_center_key + str(user.id))
            Redis.delete(user_info_key + str(user.mobile))
            Redis.lpush(balck_list_key, user.mobile)
            res.update(code=ResponseCode.Success, data={}, msg='完成封禁用户')
            return res.data
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
            return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='修改失败，请稍后再试')
        return res.data
