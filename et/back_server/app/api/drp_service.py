import hashlib
import time
import logging
from app.models.drp import EtMemberDrp
from app.models.drp import EtMemberRelation
from app.models.drp import EtDrpConfig
from app.models.task import EtTask
from app.models.task import EtTaskOrder
from app.models.accounts import EtAccount
from app.models.orders import EtMemberEarning
from app.models.orders import EtMemberWithdrawal


from flask import Blueprint, jsonify, session, request, current_app
from app.utils.util import route, Redis, helpers
from app.utils.core import db, realtionlib
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.response import ResMsg

bp = Blueprint("drp", __name__, url_prefix='/drps')

# 运营平台用户 分销or收徒 服务
logger = logging.getLogger(__name__)

redis_key_drp= "drpconfig"

@route(bp, '/configs', methods=["GET"])
def handle_drpconfigs():
    """
    获取系统分销配置信息接口
    :return: json
    """
    res = ResMsg()
    sysid= 1
    drp_configs = db.session.query(EtDrpConfig).filter(EtDrpConfig.id==sysid).first()
    res_data= dict()
    if drp_configs:
        res_data['data'] =  helpers.model_to_dict(drp_configs)

        
        del res_data['data']['update_time']
        Redis.hmset(redis_key_drp, res_data['data'])

        res.update(code=ResponseCode.Success, data= res_data, msg=f'分销信息获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='分销信息数据异常')
        return res.data

@route(bp, '/edit_configs', methods=["POST","OPTIONS"])
@login_required
def handle_drpconfig_edit():
    """
    分销设置修改接口
    :return: json 
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    sysid = 1

    drp_layers = req.get("drp_layers", 1)
    profit_percentage = req.get("profit_percentage",'')
    need_setreal = req.get("need_setreal", 1)
    daily_max = int(req.get("daily_max", 1))
    handling_fee = req.get("handling_fee",1)
    min_money = int(req.get("min_money",1))
    withdrawal_condition=  req.get("withdrawal_condition",'')
    daily_withdrawal= req.get("daily_withdrawal",9)

    update_dict = {
        "drp_layers": drp_layers,
        "profit_percentage": profit_percentage,
        "need_setreal": need_setreal,
        "daily_max": daily_max,
        "handling_fee": handling_fee,
        "min_money": min_money,
        "withdrawal_condition": withdrawal_condition,
        "daily_withdrawal": daily_withdrawal,
        "update_time": now_timestr
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    drpconfigs = db.session.query(EtDrpConfig).filter(EtDrpConfig.id == sysid).first() 
    
    if drpconfigs:
        db.session.query(EtDrpConfig).filter(EtDrpConfig.id == sysid).update(update_dict_ready)
        try:
            db.session.commit()
            Redis.delete(redis_key_drp)
            
            r_data =  helpers.model_to_dict(drpconfigs)
            del r_data['update_time']
            Redis.hmset(redis_key_drp, r_data)
            
            res.update(code=ResponseCode.Success, data={},msg=f'分销设置配置成功')
            return res.data
            
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
            return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='修改失败，请稍后再试')

        return res.data

@route(bp, '/drplist', methods=["GET"])
def handle_drplists():
    """
    分销收益流水列表接口
    @todo 根据索引优化sql查询
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    
    member_id = request.args.get("member_id", '')
    task_id = request.args.get("id",'')
    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')

    query_dict = {
        "member_id": int(member_id) if member_id else member_id,
        "task_id": int(task_id) if task_id else task_id,
    }
    filters = helpers.rmnullkeys( query_dict )

    flatten_filters= 'and '.join("{!s}={!r}".format(key,val) for (key,val) in filters.items())

    fetch_columns = "d.id, m1.nickname as username, m2.nickname as from_user, m1.IIUV,m2.IIUV as from_IIUV, t.name as taskname,t.task_class, d.amounts, d.add_time"
    p_i, p_num = (page_index-1) * page_size, page_size

    where_cond = ''
    if flatten_filters:
        where_cond = f"WHERE {flatten_filters} "
        
        if start_time and end_time:
            where_cond +=f" AND add_time>'{start_time}' AND add_time<='{end_time}' "
    else:
        if start_time and end_time:
            where_cond =f" WHERE add_time>'{start_time}' AND add_time<='{end_time}' "

    drp_sql = f"SELECT {fetch_columns} FROM \
                   (SELECT * FROM et_member_drps {where_cond} ORDER BY add_time DESC limit {p_i}, {p_num} ) AS d \
                    LEFT JOIN et_members AS m1 ON d.member_id = m1.id \
                     LEFT JOIN et_members AS m2 ON d.from_member_id = m2.id \
                      LEFT JOIN et_tasks AS t ON d.from_task_id = t.id ;"
    count_drp_sql = f"SELECT {fetch_columns} FROM \
                   (SELECT * FROM et_member_drps {where_cond} ) AS d \
                    LEFT JOIN et_members AS m1 ON d.member_id = m1.id \
                     LEFT JOIN et_members AS m2 ON d.from_member_id = m2.id \
                      LEFT JOIN et_tasks AS t ON d.from_task_id = t.id ;"
    drp_lists = db.session.execute(drp_sql).fetchall()
    count_drp_lists = db.session.execute(count_drp_sql).fetchall()

    res_data= dict()
    
    # counts = db.session.execute("SELECT count(*) FROM et_member_drps").first()
    if drp_lists:
        res_data['list'] =  [{k: v for (k, v) in row.items()} for row in drp_lists]
        res_data['length'] = len(count_drp_lists)
        res.update(code=ResponseCode.Success, data= res_data, msg=f'{len(count_drp_lists)}分销收益流水列表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='用户收益数据为空')
        return res.data

@route(bp, '/member_drplist', methods=["GET"])
def handle_memdrplists():
    """
    用户分销总收益列表接口
    @todo 根据索引优化sql查询
    :return: json
    """
    res = ResMsg()
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')


    query_dict = {
        
    }
    filters = helpers.rmnullkeys( query_dict )

    flatten_filters= 'and '.join("{!s}={!r}".format(key,val) for (key,val) in filters.items())
    
    
    if flatten_filters:
        where_cond = f"WHERE {flatten_filters} "
        
        if start_time and end_time:
            where_cond +=f" AND add_time>'{start_time}' AND add_time<='{end_time}' "
    else:
        where_cond = "WHERE DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(add_time) "
        if start_time and end_time:
            where_cond =f" WHERE add_time>'{start_time}' or add_time<='{end_time}' "

    fetch_columns = "d.amounts,m.nickname,m.IIUV,m.m_class,m.alipay_id,m.mobile,m.realname,m.status as mstatus,m.reg_time"
    
    p_i, p_num = (page_index-1) * page_size, page_size

    drp_sql = f"SELECT {fetch_columns} FROM (SELECT sum(amounts) as amounts,member_id FROM et_member_drps {where_cond} GROUP BY(member_id) ) AS d LEFT JOIN et_members AS m ON d.member_id =m.id LIMIT {p_i},{p_num};"

    count_drp_sql = f"SELECT {fetch_columns} FROM (SELECT sum(amounts) as amounts,member_id FROM et_member_drps {where_cond} GROUP BY(member_id) ) AS d LEFT JOIN et_members AS m ON d.member_id =m.id;"

    member_drplist = db.session.execute(drp_sql).fetchall()
    count_member_drplist = db.session.execute(count_drp_sql).fetchall()
    
    res_data= dict()
    
    counts = db.session.execute("SELECT count(*) FROM et_member_drps").first()
    if member_drplist:
        res_data['list'] =  [{k: v for (k, v) in row.items()} for row in member_drplist]
        res_data['length'] = len(count_member_drplist)
        res.update(code=ResponseCode.Success, data= res_data, msg='用户分销收益列表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='用户收益数据异常')
        return res.data

@route(bp, '/drplist_members', methods=["GET"])
def handle_mdrplists():
    """
    某用户分销收益流水列表接口
    @todo 根据索引优化sql查询
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')
    task_id = request.args.get("task_id", '')
    member_id = int(request.args.get("member_id", 1))

    query_dict = {
        "task_id": int(task_id) if task_id else None,
    }
    filters = helpers.rmnullkeys(query_dict)

    flatten_filters = 'and '.join("{!s}={!r}".format(key, val)
                                for (key, val) in filters.items())
    where_cond = ''
    if flatten_filters:
        where_cond = f" and {flatten_filters}"
        
        if start_time and end_time:
            where_cond +=f" AND add_time>'{start_time}' AND add_time<='{end_time}' "
    else:
        if start_time and end_time:
            where_cond =f" AND add_time>'{start_time}' AND add_time<='{end_time}' "

    fetch_columns = "d.id,m1.realname, m1.nickname as nickname, m2.nickname as from_user,m2.realname as from_userreal, m1.IIUV, t.name as taskname, d.amounts, d.add_time, m1.status, m1.m_class, m2.IIUV as from_IIUV"
    p_i, p_num = (page_index-1) * page_size, page_size

    drp_sql = f"SELECT {fetch_columns} FROM \
                   (SELECT * FROM et_member_drps WHERE member_id ={member_id} {where_cond} ORDER BY add_time DESC limit {p_i}, {p_num} ) AS d \
                    LEFT JOIN et_members AS m1 ON d.member_id = m1.id \
                     LEFT JOIN et_members AS m2 ON d.from_member_id = m2.id \
                      LEFT JOIN et_tasks AS t ON d.from_task_id = t.id ;"
    count_drp_sql = f"SELECT {fetch_columns} FROM \
                   (SELECT * FROM et_member_drps WHERE member_id ={member_id} {where_cond} ) AS d \
                    LEFT JOIN et_members AS m1 ON d.member_id = m1.id \
                     LEFT JOIN et_members AS m2 ON d.from_member_id = m2.id \
                      LEFT JOIN et_tasks AS t ON d.from_task_id = t.id ;"

    drp_lists = db.session.execute(drp_sql).fetchall()
    count_drp_lists = db.session.execute(drp_sql).fetchall()

    res_data= dict()
    counts = db.session.execute("SELECT count(*) FROM et_member_drps").first()
    
    if drp_lists:
        res_data['list'] =  [{k: v for (k, v) in row.items()} for row in drp_lists]
        res_data['length'] = len(count_drp_lists)

        res.update(code=ResponseCode.Success, data= res_data, msg=f'用户:{member_id}分销收益流水列表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg=f'用户{member_id}收益数据为空')
        return res.data



