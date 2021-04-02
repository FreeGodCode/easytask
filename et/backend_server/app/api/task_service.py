import hashlib
import time
import json
import logging

from app.models.task import EtTask
from app.models.task import EtTaskOrder
from app.models.task import EtTasksVerify
from app.models.accounts import EtAccount
from app.models.member import EtMember
from app.models.orders import EtMemberEarning
from app.models.drp import EtMemberDrp
from flask import Blueprint, jsonify, session, request, current_app
from app.utils.util import route, Redis, helpers
from app.utils.core import db, realtionlib
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode,ResponseMessage
from app.utils.response import ResMsg
from app.celery import flask_app_context, async_calculating_earnings
from anytree.importer import DictImporter


bp = Blueprint("tasks", __name__, url_prefix='/tasks')
# 运营平台管理任务服务
logger = logging.getLogger(__name__)

redis_key_drp= "drpconfig"
realtion_tree_key= "drp_relation_member_"

task_info_key= "tasks_info"
task_info_u_key= "tasks_info_"
task_detail_key= "tasks_detail_:"
task_complete_key = "complete_tasks_:"
complete_tasks_uid_key = "complete_tasks_"
task_verifyed_key = "verifyed_tasks_:"
tasks_high_info_key= "tasks_high_info"

user_center_key = "user_center:"
user_info_key= "user_info:"

user_withdraw_recode_key= "user_withdraw_recode:"
user_task_earnings_key=  "user_task_earnings_:"

@route(bp, '/list', methods=["GET"])
@login_required
def handle_list():
    """
    任务列表接口
    :return: json
    """
    res = ResMsg()

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))

    task_id = request.args.get("id",'')
    taskname = request.args.get("name",'')
    status = request.args.get("status",'')
    task_class = request.args.get("task_class", '')

    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')
    task_cats= request.args.get("task_cats", '')
    sys_tags= request.args.get("sys_tags", '')
    tags= request.args.get("tags", '')

    query_dict = {
        "id": task_id,
        "name": taskname,
        "status": status,
        "task_class": task_class,
        "task_cats": task_cats,
    }
    filters = helpers.rmnullkeys( query_dict )
    tasks_counts = None
    
    if start_time and end_time:
        
        tasks = db.session.query(EtTask).filter(EtTask.edit_time >= start_time, EtTask.edit_time <= end_time, EtTask.id>1, EtTask.mer_id==None).filter_by(**filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index-1)*page_size).all()
        tasks_counts=db.session.query(EtTask).filter(EtTask.edit_time >= start_time, EtTask.edit_time <= end_time, EtTask.mer_id==None).filter_by(**filters).all()
    else:
        if not filters:
            tasks = db.session.query(EtTask).filter(EtTask.status<3, EtTask.id>1, EtTask.mer_id==None).filter_by(**filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index-1)*page_size).all()

            tasks_counts= db.session.query(EtTask).filter(EtTask.status<3, EtTask.mer_id==None).filter_by(**filters).all()
        else:
            tasks = db.session.query(EtTask).filter(EtTask.id>1, EtTask.mer_id==None).filter_by(**filters).order_by(EtTask.edit_time.desc()).limit(page_size).offset((page_index-1)*page_size).all()

            tasks_counts= db.session.query(EtTask).filter(EtTask.status<3, EtTask.mer_id==None).filter_by(**filters).all()
    
    if tasks_counts:
        counts= (len(tasks_counts), 0)

    else:
        counts = db.session.execute("SELECT count(*) FROM et_tasks").first()


    res_data= dict()
    
    if tasks:
        res_data['list'] =  helpers.model_to_dict(tasks)
        res_data['length']= counts[0]
        res.update(code=ResponseCode.Success, data= res_data, msg=f'任务获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg=f'任务数据异常or空')
        return res.data

@route(bp, '/getinfo', methods=["GET"])
@login_required
def handle_info():
    """
    查询任务详情
    :return: json
    """
    res = ResMsg()
    
    taskid = request.args.get("id")

    res_data= dict()
    
    task = db.session.query(EtTask).filter(EtTask.id == taskid).first()
    if task:
        res_data.update(dict(helpers.model_to_dict(task)))
        res.update(code=ResponseCode.Success, data=res_data, msg=f'任务详情获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={},msg='任务数据异常')
        return res.data


@route(bp, '/copytask', methods=["GET"])
@login_required
def handle_copytask():
    """
    复制一条任务
    :return: json
    """
    res = ResMsg()
    
    taskid = request.args.get("id")

    res_data = dict()

    task = db.session.query(EtTask).filter(EtTask.id == taskid).first()

    if task:
        
        task_dict = dict(helpers.model_to_dict(task))
        del task_dict["id"]
        copy_task = EtTask(**task_dict)
        copy_task.count_tasks=0
        copy_task.edit_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        db.session.add(copy_task)
        try:
            db.session.commit()
            Redis.delete(task_info_key)
            Redis.delete(task_detail_key+str(taskid))
            Redis.delete(tasks_high_info_key)
            res_data = dict()
            res.update(code=ResponseCode.Success, data=res_data, msg=f'复制任务成功')
            return res.data
        except Exception as why:

            res.update(code=ResponseCode.Success, data={}, msg=f'任务数据异常{why}')
            return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='任务数据异常')
        return res.data

@route(bp, '/taskorder_stats', methods=["GET"])
@login_required
def handle_task_order_stat():
    """
    获取每个订单的二维码推广效果数据
    :return: json
    """
    res = ResMsg()

    order_id = request.args.get("id")
    res_data = dict()

    task_order = db.session.query(EtTaskOrder).filter(EtTaskOrder.id==order_id).first()

    if task_order:

        task_order_dict = dict(helpers.model_to_dict(task_order))

        task_id= task_order_dict['task_id']
        member_id= task_order_dict['member_id']
        ipcounts_redis_key= f'enterip_from_task_{member_id}_{task_id}'

        try:
            stats= Redis.zrange(ipcounts_redis_key, 0, -1, desc=True, withscores=True)
            res_data['stats_list']= stats
            res_data['stats_len']= len(stats)
            res_data['order_info']= task_order_dict
            
            res.update(code=ResponseCode.Success, data=res_data, msg=f'数据获取成功')
            return res.data
        except Exception as why:

            res.update(code=ResponseCode.Success, data={}, msg=f'二维码数据异常{why}')
            return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='订单数据异常')
        return res.data

@route(bp, '/addtask', methods=["POST","OPTIONS"])
@login_required
def handle_addtask():
    """
    新增任务接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    taskname= req.get("name",'tasktest1')
    status= int(req.get("status", 1))
    task_class= int(req.get("task_class", 1))
    end_time= req.get("end_time", now_timestr)
    
    if req.get("task_reward")== None:
        res.update(code=ResponseCode.Fail, data=res_data, msg=f'任务奖励请正确输入')
        return res.data

    begin_task_time= req.get("begin_task_time",now_timestr)
    count_tasks= req.get("count_tasks", 0)
    allow_nums= int(req.get("allow_nums", 99))
    allow_member_nums= int(req.get("allow_member_nums", 99))
    virtual_nums= int(req.get("virtual_nums", 99))
    tasks_counts= int(req.get("tasks_counts", 0))
    task_reward= float(req.get("task_reward", 99))
    task_info= req.get("task_info", '请根据任务步骤完成任务')
    task_steps= req.get("task_steps", '{"name":1}')
    tags= req.get("tags", '')
    poster_img= req.get("poster_img", 'https://qiniu.staticfile.org/user_avatar.jpg')
    sys_tags = req.get("sys_tags", '')
    task_cats = req.get("task_cats", '')
    recommend= int(req.get("recommend", 1))
    deadline_time= int(req.get("deadline_time", 99))
    check_router = req.get("check_router", '')

    account_name= session.get("user_name")
    user = db.session.query(EtAccount.id).filter(EtAccount.name == account_name).first()

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(end_time)/1000))

    begin_task_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(begin_task_time)/1000))

    update_dict = {
        "name": taskname,
        "account_id": user.id,
        "status": status,
        "task_class": task_class,
        "end_time": end_time,
        "begin_task_time": begin_task_time,
        "count_tasks": count_tasks,
        "allow_nums": allow_nums,
        "allow_member_nums": allow_member_nums,
        "virtual_nums": virtual_nums,
        "tasks_counts": tasks_counts,
        "task_reward": task_reward,
        "task_info": task_info,
        "task_steps": task_steps,
        "poster_img": poster_img,
        "tags": tags,
        "sys_tags": sys_tags,
        "task_cats": task_cats,
        "recommend": recommend,
        "deadline_time": deadline_time,
        "check_router": check_router,
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    
    new_user = EtTask(**update_dict_ready)
    db.session.add(new_user)
    try:
        db.session.commit()
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key+str(taskid))
        Redis.delete(tasks_high_info_key)
        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'新增任务成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'任务数据异常{why}')
        return res.data

@route(bp, '/edit_task', methods=["POST","OPTIONS"])
@login_required
def handle_edittask():
    """
    任务修改编辑接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    taskid= int(req.get("id", 1))
    taskname= req.get("name",'tasktest1-new')
    status= int(req.get("status", 1))
    task_class= int(req.get("task_class", 1))
    
    end_time= req.get("end_time", '')
    begin_task_time= req.get("begin_task_time",'')
    
    poster_img= req.get("poster_img", 'https://qiniu.staticfile.org/user_avatar.jpg')
    count_tasks= req.get("count_tasks",'')
    allow_nums= req.get("allow_nums", '')
    allow_member_nums= req.get("allow_member_nums", '')
    virtual_nums= req.get("virtual_nums", '')
    tasks_counts= req.get("tasks_counts", '')
    task_reward= req.get("task_reward", '')
    task_info= req.get("task_info", '请根据任务步骤完成任务')
    task_steps= req.get("task_steps", '')
    tags= req.get("tags", '')
    sys_tags = req.get("sys_tags", '')
    task_cats= req.get("task_cats", '')
    recommend= req.get("recommend", 1)
    deadline_time = req.get("deadline_time", '')
    check_router = req.get("check_router", '')

    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(end_time)/1000))
    begin_task_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(begin_task_time)/1000))

    account_name= session.get("user_name")

    update_dict = {
        "name": taskname,
        "status": status,
        "task_class": task_class,
        "end_time": end_time,
        "begin_task_time": begin_task_time,
        "count_tasks": count_tasks,
        "allow_nums": allow_nums,
        "allow_member_nums": allow_member_nums,
        "virtual_nums": virtual_nums,
        "tasks_counts": tasks_counts,
        "task_reward": task_reward,
        "task_info": task_info,
        "task_steps": task_steps,
        "tags": tags,
        "poster_img":poster_img,
        "sys_tags": sys_tags,
        "task_cats": task_cats,
        "recommend": recommend,
        "deadline_time": deadline_time,
        "check_router": check_router,
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    db.session.query(EtTask).filter(EtTask.id == taskid).update(update_dict_ready)
    try:
        db.session.commit()
        
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key+str(taskid))
        Redis.delete(tasks_high_info_key)

        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'任务修改成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'修改失败，数据异常{why}')
        return res.data

@route(bp, '/del_task', methods=["POST","OPTIONS"])
@login_required
def handle_deltask():
    """
    任务软删除
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    
    taskid= int(req.get("id", 1))
    status= int(req.get("status", 3))

    update_dict = {
        "status": status,
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    db.session.query(EtTask).filter(EtTask.id == taskid).update(update_dict_ready)
    try:
        db.session.commit()

        Redis.delete(task_info_key)
        Redis.delete(task_detail_key+str(taskid))

        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'任务删除成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'修改失败，数据异常{why}')
        return res.data

@route(bp, '/sort_task', methods=["POST","OPTIONS"])
@login_required
def handle_sorttask():
    """
    任务推荐排序
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    
    taskid= int(req.get("id", 1))
    recommend= int(req.get("recommend", 3))

    update_dict = {
        "recommend": recommend,
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    db.session.query(EtTask).filter(EtTask.id == taskid).update(update_dict_ready)
    try:
        db.session.commit()
        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'任务排序成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'排序失败，数据异常{why}')
        return res.data


@route(bp, '/verify_task', methods=["POST","OPTIONS"])
@login_required
def handle_verifytask():
    """
    新增任务审核
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    
    taskid= int(req.get("id", 1))
    status= int(req.get("status", 2))

    update_dict = {
        "status": status,
        "check_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    db.session.query(EtTask).filter(EtTask.id == taskid).update(update_dict_ready)
    try:
        db.session.commit()
        
        Redis.delete(task_info_key)
        Redis.delete(task_detail_key+str(taskid))

        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'任务状态变更成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'修改失败，数据异常{why}')
        return res.data

@route(bp, '/taskorder/list', methods=["GET"])
@login_required
def handle_taskorderlist():
    """
    APP用户提交任务列表接口
    @todo 根据索引优化sql查询
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    
    task_id = request.args.get("task_id", '')
    start_time = request.args.get("tstart", '')
    end_time = request.args.get("end", '')
    mobile = request.args.get("mobile", '')
    
    sys_tags= request.args.get("sys_tags", '')
    tags= request.args.get("tags", '')

    order_status = request.args.get("order_status", '')

    query_dict = {
        "task_id": int(task_id) if task_id else None,
    }
    

    filters = helpers.rmnullkeys(query_dict)

    flatten_filters = 'and '.join("{!s}={!r}".format(key, val)
                                for (key, val) in filters.items())
    cond_by= ''
    if mobile:
       cond_by= f' WHERE m.mobile={mobile} '
    # LIKE'%en%'
    cond_like= ''
    if sys_tags:
        if not mobile:
            cond_like=f"WHERE t.sys_tags LIKE'%{sys_tags}%' "
        else:
            cond_like=f" AND t.sys_tags LIKE'%{sys_tags}%' "

    if not order_status:
        where_cond = 'WHERE status> 0 '
    else:
        where_cond = f'WHERE status= {order_status} '
        
    if flatten_filters:
        where_cond += f" and {flatten_filters}"
        
        if start_time and end_time:
            where_cond +=f' and add_time>{start_time} or add_time<={end_time} '
    else:
        if start_time and end_time:
            where_cond +=f' and add_time>{start_time} or add_time<={end_time} '

    fetch_columns = "o.id,o.task_id,o.member_id,o.status as order_status,o.user_submit,o.add_time,o.submit_time,o.account_id,o.app_safe_info,o.safe_token,o.confidence, t.name as taskname,t.task_class, t.status as task_status, t.task_reward,t.deadline_time,m.nickname,m.realname,m.mobile,m.m_class,m.setreal,m.alipayid"
    
    p_i, p_num = (page_index-1) * page_size, page_size

    task_sql =f"SELECT {fetch_columns} FROM \
                    (SELECT * FROM et_task_orders {where_cond} ) AS o \
                    LEFT JOIN et_members AS m ON o.member_id =m.id \
                    LEFT JOIN et_tasks AS t ON o.task_id =t.id {cond_by} {cond_like} ORDER BY o.submit_time DESC LIMIT {p_i},{p_num} ;"
    
    task_counts_sql= f"SELECT {fetch_columns} FROM \
                    (SELECT * FROM et_task_orders {where_cond}) AS o \
                    LEFT JOIN et_members AS m ON o.member_id =m.id \
                    LEFT JOIN et_tasks AS t ON o.task_id =t.id {cond_by} {cond_like};"
    
    task_orders = db.session.execute(task_sql).fetchall()
    task_counts= db.session.execute(task_counts_sql).fetchall()

    res_data= dict()
    counts = db.session.execute(f"SELECT count(*) FROM et_task_orders {where_cond}").first()
    
    if task_orders:
        # result: RowProxy to dict 
        res_data['list'] =  [{key: value for (key, value) in row.items()} for row in task_orders]
        # logger.info(res_data['list'])      
        res_data['length'] = counts[0]

        res.update(code=ResponseCode.Success, data=res_data,
                   msg=f'{task_counts_sql}用户提交任务列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg=f'{task_sql}任务数据为空')
        return res.data

@route(bp, '/taskorder/verify_task', methods=["POST","OPTIONS"])
@login_required
def handle_verifytaskorder():
    """
    用户提交任务审核接口(交单)
    @todo 审核流程优化
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    
    taskorder_id= int(req.get("id", 1))
    status= int(req.get("status", 1))
    verify_log = req.get("verify_log", '')

    account_name= session.get("user_name")

    if not account_name:
        res.update(code=ResponseCode.Success, data={},msg=f'账户{account_name}数据异常')
        return res.data
    
    user = db.session.query(EtAccount.id).filter(EtAccount.name == account_name).first()
    
    if not status:
        res.update(code=ResponseCode.Success, data={},msg='未提交审核数据,操作已经撤销')
        return res.data

    update_dict = {
        "status": status,
        "account_id": user.id,
        "verify_log":verify_log
    }
    task_order= db.session.query(EtTaskOrder.id,EtTaskOrder.task_id,EtTaskOrder.member_id).filter(EtTaskOrder.id == taskorder_id).first()
    
    user = db.session.query(EtMember.id, EtMember.nickname, EtMember.status, EtMember.m_class, EtMember.realname, EtMember.mobile, EtMember.IIUV,EtMember.balance,EtMember.balance_version, EtMember.setreal, EtMember.alipayid).filter(EtMember.id == EtTaskOrder.member_id).first()
    user_info = (dict(zip(user.keys(), user)))

    if task_order:

        db.session.query(EtTaskOrder).filter(EtTaskOrder.id == taskorder_id).update(update_dict)
        task_order_dict= dict(zip(task_order.keys(), task_order))
        
        if status == 4:

            up_sql= f"UPDATE et_tasks SET tasks_fulfil = tasks_fulfil+1 WHERE id ={task_order_dict['task_id']}"
            up_num= db.session.execute(up_sql)

        try:


            db.session.commit()
            res_data= dict()
            
            res_data.update(task_order_dict)
            
            u_task_key=f"user_tasks_:{task_order_dict['member_id']}"
            Redis.delete(u_task_key)

            if status == 5:
                Redis.sadd(f"{task_complete_key}{task_order.task_id}", task_order.member_id)
                
                Redis.sadd(f"{complete_tasks_uid_key}{task_order.member_id}", task_order.task_id)
                
                Redis.expire(f"{task_complete_key}{task_order.task_id}", 60 * 60 * 10)
                res.update(code=ResponseCode.Success, data={}, msg='该单未通过审核')
            
            if status == 4:

                task_limit=20

                counts = db.session.execute(f"SELECT count(id) FROM et_task_orders WHERE status=4 AND member_id={task_order_dict['member_id']}").first()
                
                # update member status 2
                if int(counts[0]) == task_limit:
                    update_dict = {
                        "m_class": 2,
                    }
                    update_dict_ready = helpers.rmnullkeys( update_dict )
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
                
                calculating_earnings(task_order_dict, task_order.task_id, type_set=1 )
                
                res.update(code=ResponseCode.Success, data=res_data, msg=f'任务订单审核成功，对该用户发放收益')
            
            update_dict_com = {
                "status": 4,
                "account_id": user.id,
                "verify_log":verify_log
            }

            db.session.query(EtTaskOrder).filter(EtTaskOrder.id == taskorder_id).update(update_dict_com)

            return res.data
        except Exception as why:

            res.update(code=ResponseCode.Success, data={},msg=f'任务订单审核失败,{why}')
            return res.data
    
def calculating_earnings(task_order:dict, task_id:int, type_set:int =1):
    '''
    计算该用户收益 同时异步完成该用户 所有上级 收益更新
    #type_set 收益来源：1：任务收益 2：分销佣金3：新手红包奖励
    '''
    res = ResMsg()
    if isinstance(task_order, dict):
        task = db.session.query(EtTask).filter(EtTask.id == task_id).first()
        logger.info('发放父亲节点收益')
        if task:
            task_dict= dict(helpers.model_to_dict(task))
            logger.info(task_dict)

            if task_dict['task_class']==3:
                type_set = 3
            

            task_earning_money= float(task_dict['task_reward'])
            
            earning_dict ={
                "member_id": task_order['member_id'],
                "task_id": task_id,
                "amounts": task_earning_money,
                "task_order_id": task_order['id'],
                "amount_type": type_set
            }
            logger.info(earning_dict)
            new_earning = EtMemberEarning(**earning_dict)

            isearn_sended= user = db.session.query(EtMemberEarning).filter(
                EtMemberEarning.task_order_id == task_order['id']).first()

            if isearn_sended:
                logger.info("该用户订单收益已发放")
                return "该用户订单收益已发放'"

            db.session.add(new_earning)

            user = db.session.query(EtMember).filter(
                EtMember.id == task_order['member_id']).first()

            if user.status==2:
                res.update(dict(code=ResponseCode.Success, data={},
                                msg=f'该用户已禁用，无法获得收益'))
                return res
                
            if user:
                try:
                    update_dict = {
                        "balance": task_earning_money*100 + user.balance,
                        "balance_version": int(time.time())
                    }

                    db.session.query(EtMember).filter(
                        EtMember.id == task_order['member_id'], EtMember.balance_version == user.balance_version).update(update_dict)
                    db.session.commit()

                    # update user cache
                    Redis.delete(user_center_key + str(user.id))
                    Redis.delete(user_info_key + str(user.mobile))
                    Redis.delete(user_task_earnings_key + str(user.id))

                    #缓存获取分销比例参数
                    drp_config = Redis.hgetall(redis_key_drp)
                    per_sets = json.loads(drp_config[b'profit_percentage'].decode('utf8'))
                    
                    logger.info(per_sets)
                    
                    # get各级分销比例
                    profit_percentage_arr=[]
                    for i in range(len(per_sets)):
                        profit_percentage_arr.append (per_sets[i]['per'])
                    
                    logger.info("比例设置：")
                    # logger.info(profit_percentage_arr) 
                    
                    # get当前用户关系树
                    rel_from_relations = db.session.execute(f"SELECT * FROM et_member_relations WHERE member_id={task_order['member_id']}").first()
                    root_id= None

                    if rel_from_relations['parent_id']:
                        root_id= rel_from_relations['parent_id']

                    if rel_from_relations['top_parent_id']:
                        root_id= rel_from_relations['top_parent_id']

                    realtion_tree_key_m = realtion_tree_key + str(root_id)
                    logger.info("tree：")
                    
                    tree_node = Redis.hget(realtion_tree_key_m, 0)
                    logger.info(str(tree_node))
                    realtion_tree_fromuser = json.loads(tree_node)

                    logger.info(str(realtion_tree_fromuser))
                    importer = DictImporter()
                    
                    parents=[]
                    realtion_tree = importer.import_(realtion_tree_fromuser)
                    cur_node_tuple  = realtionlib.findall_by_attr(realtion_tree, task_order['member_id'])
                    cur_node = cur_node_tuple[0]
                    logger.info('ancestors:')
                    logger.info(str(cur_node.ancestors)) 
                    
                    if cur_node.ancestors:
                        # async-task: for all parents : drp_earnings
                        for i,k in enumerate(cur_node.ancestors):
                            parents.append(k.name)
                            parentid= k.name
                            drp_level = i+1
                            logger.info('k-name:'+str(k.name))
                            logger.info('drp_level:'+str(drp_level))
                            if drp_level<4:
                                result = async_calculating_earnings.delay(parentid, drp_level, earning_dict, task_id, task_order['id'], type_set=2 )
                    
                        logger.info(parents) 

                    res.update(code=ResponseCode.Success, data={},msg=f'用户交单任务收益更新成功')
                    logger.info(res.data)
                except Exception as why:

                    res.update(code=ResponseCode.Success, data={},msg=f'用户交单任务收益数据添加失败{why}')
                    logger.info(res.data)
            else:
                res.update(code=ResponseCode.Success, data={},msg=f'用户信息异常{user}')


@route(bp, '/testasyncAdd', methods=["GET"])
def test_add(task_order:dict, task_id:int, type_set:int =1):
    # ce_calculating_earnings.delay(task_order_dict, task_order.task_id, type_set=1 )
    # result = add.delay(1, 2)
    # return result.get(timeout=1)
    pass


@route(bp, '/testasync', methods=["GET"])
def test_flask_app_context():
    
    result = flask_app_context.delay()
    return result.get(timeout=1)






