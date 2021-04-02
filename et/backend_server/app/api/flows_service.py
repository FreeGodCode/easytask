# import hashlib
import json
import time
import logging
# from app.models.system import EtGlobalConfig
# from app.models.system import EtAppConfig
# from app.models.system import EtAppsPubHistory
# from app.models.drp import EtMemberDrp
# from app.models.drp import EtMemberRelation
# from app.models.drp import EtDrpConfig
# from app.models.task import EtTask
# from app.models.task import EtTaskOrder
# from app.models.accounts import EtAccount
# from app.models.orders import EtMemberEarning
# from app.models.orders import EtMemberWithdrawal

from flask import Blueprint, jsonify, session, request, current_app
from app.utils.util import route, Redis, helpers
from app.utils.core import db
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.response import ResMsg

bp = Blueprint("flows", __name__, url_prefix='/flows')
# 运营平台统计报表服务
logger = logging.getLogger(__name__)
redis_key_sys= "sysconfig"
blacklist_key= "blacklist_member"
redis_key_drp= "drpconfig"

@route(bp, '/totals_lists', methods=["GET"])
@login_required
def handle_totals_list():
    """
    总报表：
    新用户数据
    任务交单数据
    提现数据
    任务总赏金
    邀请分成
    邀请人数
    @params data: 1今日 -1 昨日
    :return: json
    """
    res = ResMsg()
    
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    date = request.args.get("date", 1)
    stats = dict()
    
    date_cond= "="
    if date == '-1':
        date_cond= "+ 1 >="

    newuser_sql=f"SELECT SUM(IF(to_days(reg_time) {date_cond} to_days(now()), 1 ,0)) AS counts FROM et_members"

    #新手红包奖励
    newuser_reward_sql = f"SELECT COUNT(er.id) as newreward_counts,SUM(er.amounts) as newreward_sums FROM (SELECT * FROM et_members WHERE to_days(reg_time) {date_cond} to_days(now())) AS m LEFT JOIN et_member_earnings AS er on m.id= er.member_id WHERE er.amounts=1 AND er.task_order_id < 1;"
    #新手提现奖励
    newuser_wd_sql = f"SELECT COUNT(et.id) as wd_counts, SUM(et.amounts) as wd_amounts FROM (SELECT * FROM et_members WHERE to_days(reg_time) {date_cond} to_days(now())) AS m LEFT JOIN et_member_withdrawal AS et on m.id=et.member_id"
    #老用户提现奖励
    olduser_wd_sql = f"SELECT COUNT(et.id) as wd_counts, SUM(et.amounts) as wd_amounts FROM (SELECT * FROM et_members WHERE to_days(reg_time) < to_days(now())) AS m LEFT JOIN et_member_withdrawal AS et on m.id=et.member_id WHERE to_days(et.start_time) {date_cond} to_days(now())"
    #新用户任务
    newuser_orders_sql= f"SELECT COUNT(td.id),SUM(IF(td.status= 1, 1 ,0)),SUM(IF(td.status= 2, 1 ,0)),SUM(IF(td.status= 4, 1 ,0)),SUM(IF(td.status= 5, 1 ,0)) FROM (SELECT * FROM et_members WHERE to_days(reg_time) {date_cond} to_days(now())) AS m LEFT JOIN et_task_orders AS td ON td.member_id = m.id"
    #老用户任务
    olduser_orders_sql= f"SELECT COUNT(td.id),SUM(IF(td.status= 1, 1 ,0)),SUM(IF(td.status= 2, 1 ,0)),SUM(IF(td.status= 4, 1 ,0)),SUM(IF(td.status= 5, 1 ,0)) FROM (SELECT * FROM et_members WHERE to_days(reg_time) < to_days(now())) AS m LEFT JOIN et_task_orders AS td ON td.member_id = m.id WHERE to_days(td.add_time) {date_cond} to_days(now())"
    #新老用户任务收益
    newuser_earnings_sql = f"SELECT SUM(er.amounts) FROM (SELECT * FROM et_members WHERE to_days(reg_time) {date_cond} to_days(now())) AS m LEFT JOIN et_member_earnings AS er ON er.member_id = m.id WHERE er.task_order_id>1"
    olduser_earnings_sql = f"SELECT SUM(er.amounts) FROM (SELECT * FROM et_members WHERE to_days(reg_time) < to_days(now())) AS m LEFT JOIN et_member_earnings AS er ON er.member_id = m.id WHERE er.task_order_id>1  AND to_days(er.add_time) {date_cond} to_days(now())"
    #每日邀请分成和邀请收徒总计
    drp_earnings_sql= f"SELECT SUM(IF(to_days(add_time) {date_cond} to_days(now()), amounts ,0)) AS today, SUM(IF(to_days(add_time) < to_days(now()), amounts ,0)) AS history FROM et_member_drps"
    
    drp_newuser_earnings_sql=f"SELECT SUM(dr.amounts) as amounts FROM (SELECT * FROM et_members WHERE to_days(reg_time) {date_cond} to_days(now())) AS m LEFT JOIN et_member_drps AS dr ON dr.from_member_id = m.id"

    drp_counts_sql= f"SELECT SUM(IF(to_days(create_time) {date_cond} to_days(now()), 1 ,0)) AS todays,SUM(IF(to_days(create_time)<to_days(now()), 1 ,0)) AS history FROM et_member_relations WHERE levels!=1;"

    newuser_data= db.session.execute(newuser_sql).first()
    newuser_reward_data= db.session.execute(newuser_reward_sql).first()
    newuser_wd_data= db.session.execute(newuser_wd_sql).first()
    olduser_wd_data= db.session.execute(olduser_wd_sql).first()
    newuser_orders_data= db.session.execute(newuser_orders_sql).first()
    olduser_orders_data= db.session.execute(olduser_orders_sql).first()

    newuser_earnings_data= db.session.execute(newuser_earnings_sql).first()
    olduser_earnings_data= db.session.execute(olduser_earnings_sql).first()

    drp_earnings_data= db.session.execute(drp_earnings_sql).first()
    drp_newuser_earnings_data= db.session.execute(drp_newuser_earnings_sql).first()
    drp_counts_data= db.session.execute(drp_counts_sql).first()


    stats['id']=1
    stats['new_users']= int(newuser_data[0]) or 0
    stats['newuser_reward_counts'] = int(newuser_reward_data[0]) or 0
    stats['newuser_reward_amounts'] = newuser_reward_data[1] or 0
    stats['newuser_wd_counts'] = int(newuser_wd_data[0]) or 0
    stats['newuser_wd_amounts'] = newuser_wd_data[1] or 0
    stats['olduser_wd_counts'] = int(olduser_wd_data[0]) or 0
    stats['olduser_wd_amounts'] = olduser_wd_data[1] or 0

    stats['newuser_getorder_counts'] = int(newuser_orders_data[0]) or 0
    stats['newuser_uporder_counts'] = newuser_orders_data[1] or 0
    stats['newuser_comporder_counts'] = newuser_orders_data[2] or 0
    stats['newuser_refuseorder_counts'] = newuser_orders_data[3] or 0

    stats['olduser_getorder_counts'] = olduser_orders_data[0] or 0
    stats['olduser_uporder_counts'] = olduser_orders_data[1] or 0
    stats['olduser_comporder_counts'] = olduser_orders_data[2] or 0
    stats['olduser_refuseorder_counts'] = olduser_orders_data[3] or 0

    stats['newuser_earnings_amounts'] = newuser_earnings_data[0] or 0
    stats['olduser_earnings_amounts'] = olduser_earnings_data[0] or 0

    stats['total_drp_earnings'] = drp_earnings_data[0] or 0
    stats['totalhistory_drp_earnings'] = drp_earnings_data[1] or 0
    stats['drp_newuser_earnings'] = drp_newuser_earnings_data[0] or 0
    stats['total_drp_counts'] = int(drp_counts_data[0]) or 0
    stats['totalhistory_drp_counts'] = int(drp_counts_data[1]) or 0

    res_data= dict()
    if stats:
        res_data['list'] =  [stats]
        res_data['length'] = 1
        res.update(code=ResponseCode.Success, data= res_data, msg=f'总报表数据获取成功')
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='总报表数据为空or异常')
        return res.data

@route(bp, '/tasks_lists', methods=["GET"])
@login_required
def handle_tasks_lists():
    """
    任务统计报表
    :return: json
    """
    res = ResMsg()
    
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    date = int(request.args.get("date", 1))

    p_i, p_num = (page_index-1) * page_size, page_size

    tasks_sql= f"SELECT t.name,t.id,t.task_reward, t.id AS task_id,t.task_class,t.sys_tags,t.tasks_counts,t.count_tasks, \
    COUNT(o.id) AS totals, \
    SUM(IF(o.status=4, 1 ,0)) AS completes,\
    SUM(IF(o.status=5, 1 ,0)) AS refuse, \
    SUM(IF(o.status=2, 1 ,0)) AS verifying,\
    SUM(IF(o.status=3, 1 ,0)) AS cancles,\
    SUM(IF(o.status=1, 1 ,0)) AS waiting \
    FROM et_tasks AS t,et_task_orders AS o \
    WHERE t.id=o.task_id AND to_days(t.begin_task_time) = to_days(now()) AND t.status!=4 \
    GROUP BY o.task_id"

    tasks_data= db.session.execute(tasks_sql).fetchall()
    counts = db.session.execute(
        "SELECT count(id) FROM et_tasks WHERE to_days(begin_task_time) = to_days(now())").first()
    res_data= dict()

    if tasks_data:
        res_data['list'] =  [{key: value for (key, value) in row.items()} for row in tasks_data]
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data= res_data, msg='任务报表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='任务报表数据数据为空or异常')
        return res.data


@route(bp, '/members_lists', methods=["GET"])
@login_required
def handle_members_lists():
    """
    用户统计报表
    """
    res = ResMsg()
    
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    date = int(request.args.get("date", 1))

    stats = dict()
    
    newuser_sql=f"SELECT SUM(IF(to_days(reg_time) = to_days(now()), 1 ,0)) AS counts FROM et_members"

    #新手红包奖励
    newuser_reward_sql = f"SELECT COUNT(er.id) as newreward_counts,SUM(er.amounts) as newreward_sums FROM (SELECT * FROM et_members WHERE to_days(reg_time) = to_days(now())) AS m LEFT JOIN et_member_earnings AS er on m.id= er.member_id WHERE er.amounts=1 AND er.task_order_id < 1;"
    #新手提现奖励
    newuser_wd_sql = f"SELECT COUNT(et.id) as wd_counts, SUM(et.amounts) as wd_amounts FROM (SELECT * FROM et_members WHERE to_days(reg_time) = to_days(now())) AS m LEFT JOIN et_member_withdrawal AS et on m.id=et.member_id"
    
    #老用户今日提现奖励
    olduser_wd_sql = f"SELECT COUNT(et.id) as wd_counts, SUM(et.amounts) as wd_amounts FROM (SELECT * FROM et_members WHERE to_days(reg_time) < to_days(now())) AS m LEFT JOIN et_member_withdrawal AS et on m.id=et.member_id WHERE to_days( et.end_time ) = to_days( now())"
    
    #新用户任务
    newuser_orders_sql= f"SELECT COUNT(td.id),SUM(IF(td.status= 1, 1 ,0)),SUM(IF(td.status= 2, 1 ,0)),SUM(IF(td.status= 4, 1 ,0)),SUM(IF(td.status= 5, 1 ,0)) FROM (SELECT * FROM et_members WHERE to_days(reg_time) = to_days(now())) AS m LEFT JOIN et_task_orders AS td ON td.member_id = m.id"

    #老用户今日任务
    olduser_orders_sql= f"SELECT COUNT(td.id),SUM(IF(td.status= 1, 1 ,0)),SUM(IF(td.status= 2, 1 ,0)),SUM(IF(td.status= 4, 1 ,0)),SUM(IF(td.status= 5, 1 ,0)) FROM (SELECT * FROM et_members WHERE to_days(reg_time) < to_days(now())) AS m LEFT JOIN et_task_orders AS td ON td.member_id = m.id WHERE to_days( td.add_time ) = to_days( now())"
    #今日任务收益
    today_earnings_sql = f"SELECT SUM( er.amounts ) FROM ( SELECT * FROM et_members ) AS m LEFT JOIN et_member_earnings AS er ON er.member_id = m.id WHERE er.task_order_id >1 AND  to_days( er.add_time ) = to_days( now())"
    history_earnings_sql = f"SELECT SUM( er.amounts ) FROM ( SELECT * FROM et_members ) AS m LEFT JOIN et_member_earnings AS er ON er.member_id = m.id WHERE er.task_order_id >1"
    

    newuser_data= db.session.execute(newuser_sql).first()
    newuser_reward_data= db.session.execute(newuser_reward_sql).first()
    newuser_wd_data= db.session.execute(newuser_wd_sql).first()
    olduser_wd_data= db.session.execute(olduser_wd_sql).first()
    newuser_orders_data= db.session.execute(newuser_orders_sql).first()
    olduser_orders_data= db.session.execute(olduser_orders_sql).first()

    users_earnings_data= db.session.execute(today_earnings_sql).first()
    historyuser_earnings_data= db.session.execute(history_earnings_sql).first()

    stats['id']=1
    stats['new_users']= int(newuser_data[0]) or 0
    stats['newuser_reward_counts'] = int(newuser_reward_data[0]) or 0
    stats['newuser_reward_amounts'] = newuser_reward_data[1] or 0
    stats['newuser_wd_counts'] = int(newuser_wd_data[0]) or 0
    stats['newuser_wd_amounts'] = newuser_wd_data[1] or 0
    stats['olduser_wd_counts'] = int(olduser_wd_data[0]) or 0
    stats['olduser_wd_amounts'] = olduser_wd_data[1] or 0

    stats['newuser_getorder_counts'] = newuser_orders_data[0] or 0
    stats['newuser_uporder_counts'] = newuser_orders_data[1] or 0
    stats['newuser_comporder_counts'] = newuser_orders_data[2] or 0
    stats['newuser_refuseorder_counts'] = newuser_orders_data[3] or 0

    stats['olduser_getorder_counts'] = olduser_orders_data[0] or 0
    stats['olduser_uporder_counts'] = olduser_orders_data[1] or 0
    stats['olduser_comporder_counts'] = olduser_orders_data[2] or 0
    stats['olduser_refuseorder_counts'] = olduser_orders_data[3] or 0

    stats['users_earnings_amounts'] = users_earnings_data[0] or 0
    stats['historyusers_earnings_amounts'] = historyuser_earnings_data[0] or 0


    res_data= dict()

    if stats:
        res_data['list'] =  [stats]
        res_data['length'] = 1
        res.update(code=ResponseCode.Success, data= res_data, msg='用户报表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='用户报表数据数据为空or异常')
        return res.data
    
@route(bp, '/orders_lists', methods=["GET"])
@login_required
def handle_orders_lists():
    """
    流水统计报表
    """
    res = ResMsg()
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    date = int(request.args.get("date", 1))

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
    flatten_filters = ' AND '.join("{!s}={!r}".format(key, val)
                                for (key, val) in filters.items())
    p_i, p_num = (page_index-1) * page_size, page_size
    
    where_cond = ''
    if flatten_filters:
        where_cond = f" AND {flatten_filters} "
        
        if start_time and end_time:
            where_cond +=f" AND add_time>'{start_time}' AND add_time<='{end_time}' "
    else:
        if start_time and end_time:
            where_cond =f" AND add_time>'{start_time}' AND add_time<='{end_time}' "

    fetch_columns = "e.id,e.add_time,t.name AS task_name,t.task_reward,t.id as task_id,e.member_id,mr.parent_id as lv1_id,mr1.parent_id as lv2_id,mr2.parent_id as lv3_id"

    earning_sql= f"SELECT {fetch_columns} FROM ( SELECT id, amounts, member_id, task_order_id, task_id, amount_type, add_time FROM et_member_earnings WHERE task_order_id>0 {where_cond} ) AS e LEFT JOIN et_tasks AS t ON e.task_id = t.id \
    LEFT JOIN et_member_relations as mr ON mr.member_id=e.member_id \
    LEFT JOIN et_member_relations as mr1 ON mr.parent_id=mr1.member_id \
    LEFT JOIN et_member_relations as mr2 ON mr1.parent_id=mr2.member_id \
    WHERE  mr.top_parent_id IS NOT NULL LIMIT {p_i},{p_num}"
    
    count_earning_sql= f"SELECT {fetch_columns} FROM ( SELECT id, amounts, member_id, task_order_id, task_id, amount_type, add_time FROM et_member_earnings WHERE task_order_id>0 ) AS e LEFT JOIN et_tasks AS t ON e.task_id = t.id \
    LEFT JOIN et_member_relations as mr ON mr.member_id=e.member_id \
    LEFT JOIN et_member_relations as mr1 ON mr.parent_id=mr1.member_id \
    LEFT JOIN et_member_relations as mr2 ON mr1.parent_id=mr2.member_id \
    WHERE  mr.top_parent_id IS NOT NULL"

    earnings = db.session.execute(earning_sql).fetchall()
    
    counts = db.session.execute(count_earning_sql).fetchall()

    drp_config = Redis.hgetall(redis_key_drp)
    per_sets = json.loads(drp_config[b'profit_percentage'].decode('utf8'))
    
    logger.info(per_sets)
    
    profit_percentage_arr=[]
    for i in range(len(per_sets)):
        profit_percentage_arr.append (per_sets[i]['per'])

    res_data = dict()

    if earnings:
        res_data['list'] = [{k: v for (k, v) in row.items()}
                                       for row in earnings]
        res_data['length'] = len(counts)
        res_data['drpconfig'] = profit_percentage_arr

        res.update(code=ResponseCode.Success, data= res_data, msg='流水报表数据获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='流水报表数据数据为空or异常')
        return res.data

@route(bp, '/drplist', methods=["GET"])
def handle_drp_lists():
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