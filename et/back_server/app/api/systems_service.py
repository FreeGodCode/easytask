import hashlib
import time
import logging
from app.models.system import EtGlobalConfig
from app.models.system import EtAppConfig
from app.models.system import EtAppsPubHistory
from app.models.accounts import EtAccount
import json
from flask import Blueprint, jsonify, session, request, current_app
from app.utils.util import route, Redis, helpers
from app.utils.core import db
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.response import ResMsg

bp = Blueprint("systems", __name__, url_prefix='/sys')
# 运营平台管理系统设置服务
logger = logging.getLogger(__name__)
redis_key_sys= "sysconfig"
blacklist_key= "blacklist_member"
system_logging = "system_logging"


@route(bp, '/configs', methods=["GET"])
@login_required
def handle_configs():
    """
    获取系统信息接口
    :return: json
    """
    res = ResMsg()
    id = request.args.get("id", 1)
    sysid= 1
    sys_configs = db.session.query(EtGlobalConfig).filter(EtGlobalConfig.id==sysid).first()
    res_data= dict()
    if sys_configs:
        res_data['data'] =  helpers.model_to_dict(sys_configs)
        # logger.error(Redis.hgetall(redis_key_sys))
        if Redis.hgetall(redis_key_sys) =={}:
            del res_data['data']['update_time']
            cache_data = helpers.rmnullkeys( res_data['data'] )
            logger.error(res_data['data'])
            ret=Redis.hmset(redis_key_sys, cache_data)
            logger.error(ret)

        res.update(code=ResponseCode.Success, data= res_data, msg='系统信息获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='系统信息数据异常')
        return res.data

@route(bp, '/edit_configs', methods=["POST","OPTIONS"])
@login_required
def handle_sysconfig_edit():
    """
    系统全局设置修改
    :return: json 
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    sysid = 1
    notice = req.get("notice",'')
    domains = req.get("domains",'')
    share_domains= req.get("share_domains",'')
    task_limit = req.get("task_limit",20)
    banners=  req.get("banners",'')
    limit_withdrawal= req.get("limit_withdrawal",'')
    sys_status = int(req.get("status",1))
    rules = req.get("rules",1)
    helper = req.get("helpers",1)
    start_page = req.get("start_page",1)
    upgrade = int(req.get("upgrade",10))

    update_dict = {
        "notice": notice,
        "domains": domains,
        "share_domains":share_domains,
        "task_limit": task_limit,
        "banners": banners,
        "limit_withdrawal": limit_withdrawal,
        "sys_status": sys_status,
        "rules": rules,
        "helpers": helper,
        "start_page": start_page,
        "upgrade": upgrade,
        "update_time": now_timestr
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    sysdata = db.session.query(EtGlobalConfig).filter(EtGlobalConfig.id == sysid).first()
    
    if sysdata:
        db.session.query(EtGlobalConfig).filter(EtGlobalConfig.id == sysid).update(update_dict_ready)
        if notice:
            data = {
                'content': notice,
                'time': now_timestr
            }
            json_data = json.dumps(data)
            redis_res = Redis.lpush(system_logging, json_data)
        try:
            db.session.commit()
            Redis.delete(redis_key_sys)
            res_data =  helpers.queryToDict(sysdata)
            
            del res_data['update_time']
            
            Redis.hmset(redis_key_sys, res_data)
            res.update(code=ResponseCode.Success, data={},msg='系统全局配置成功')
            return res.data
            
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
            return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='修改失败，请稍后再试')

        return res.data

@route(bp, '/applist', methods=["GET"])
@login_required
def handle_applist():
    """
    获取app发布列表
    :return: json
    """
    res = ResMsg()
    
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))

    applist = db.session.query(EtAppsPubHistory).limit(
        page_size).offset((page_index-1)*page_size).all()
    counts = db.session.execute("SELECT count(*) FROM et_apps_pub_history").first()
    res_data= dict()

    if applist:
        res_data['list'] =  helpers.model_to_dict(applist)
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data= res_data, msg='app发布列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='app发布列信息数据为空or异常')
        return res.data

@route(bp, '/feedlist', methods=["GET"])
@login_required
def handle_feedlist():
    """
    获取app反馈信息列表
    :return: json
    """
    res = ResMsg()
    
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))

    p_i, p_num = (page_index-1) * page_size, page_size

    feedlist = db.session.execute(f"SELECT * FROM et_feedbacks ORDER BY add_time DESC LIMIT {p_i},{p_num}").fetchall()

    counts = db.session.execute(
        "SELECT count(*) FROM et_feedbacks").first()
    res_data= dict()

    if feedlist:
        res_data['list'] =  [{key: value for (key, value) in row.items()} for row in feedlist]
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data= res_data, msg='app用户反馈列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='app用户反馈信息数据为空or异常')
        return res.data

@route(bp, '/gen_blacklist', methods=["GET"])
# @login_required
def handle_gen_blacklist():
    """
    设置黑名单用户 blacklists列表 到redis集合
    :@param: phone 如果设置phone，则在set中新增一个phone
    :return: json
    """
    res = ResMsg()
    phone = request.args.get("phone", '')

    if phone:
        p.sadd(blacklist_key, phone)

    blacklist = db.session.execute("SELECT phone FROM et_blacklists").fetchall()

    counts = db.session.execute(
        "SELECT count(*) FROM et_blacklists").first()
    res_data= dict()
    blacklists= [{key: value for (key, value) in row.items()} for row in blacklist]
    
    # pipeline multi-set
    
    r = Redis._get_r()
    with r.pipeline(transaction=False) as p:
       for value in blacklists:
           p.sadd(blacklist_key, value['phone'])
       p.execute()

    Redis.expire(blacklist_key, 60 * 60 * 10 * 90)

    if blacklist:
        # res_data['list'] =  blacklists
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data= res_data, msg='app用户blacklist列表获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='app用户blacklist数据为空or异常')
        return res.data

@route(bp, '/addapp_pubs', methods=["POST","OPTIONS"])
@login_required
def handle_addappubs():
    """
    新增发布APP信息
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    version= req.get("version",'1.0')
    osversion = req.get("osversion", 'android')
    update_status= int(req.get("update_status", 1))
    down_url= req.get("down_url", 'XXXX')
    up_logs= req.get("up_logs", '')

    account_name= session.get("user_name")

    update_dict = {
        "version": version,
        "osversion": osversion,
        "update_status": update_status,
        "down_url": down_url,
        "up_logs": up_logs,
        "update_time": now_timestr,
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    
    new_user = EtAppsPubHistory(**update_dict_ready)
    db.session.add(new_user)
    try:
        db.session.commit()
        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'新增APP成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'任务数据异常{why}')
        return res.data

@route(bp, '/appconfigs', methods=["GET"])
def handle_appconfigs():
    """
    获取APP信息接口
    :return: json
    """
    res = ResMsg()
    sysid= 1
    sys_configs = db.session.query(EtAppConfig).filter().first()
    res_data= dict()
    if sys_configs:
        res_data['data'] =  helpers.model_to_dict(sys_configs)
        res.update(code=ResponseCode.Success, data= res_data, msg='APP信息获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='APP信息数据为空or异常')
        return res.data


@route(bp, '/edit_appconfigs', methods=["POST","OPTIONS"])
@login_required
def handle_edit_appconfigs():
    """
    编辑当前平台绑定app信息
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    cur_version= req.get("cur_version",'tasktest1')
    update_status= int(req.get("update_status", 1))
   

    account_name= session.get("user_name")
    update_dict = {
        "cur_version": cur_version,
        "update_status": update_status,
        "update_time": now_timestr,
    }
    
    update_dict_ready = helpers.rmnullkeys( update_dict )
    db.session.query(EtAppConfig).filter().update(update_dict_ready)
    try:
        db.session.commit()
        res_data= dict()
        res.update(code=ResponseCode.Success, data=res_data, msg=f'绑定APP成功')
        return res.data
    except Exception as why:

        res.update(code=ResponseCode.Success, data={},msg=f'绑定app失败，数据异常{why}')
        return res.data

@route(bp, '/dash_stats', methods=["GET"])
@login_required
def handle_stats_dashborad():
    """
    基本业务统计
    今日新用户 et_members
    今日任务提交 et_task_orders
    今日分销数 et_member_drps
    今日提现 et_member_withdrawal
    DAU -7days 
    :return: json
    """
    res = ResMsg()
    id = request.args.get("id", 1)
    
    member_sql= 'select count(id) as num from et_members  where DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(reg_time);'
    task_orders_sql=  'select count(id) as num from et_task_orders where status>1 and DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(add_time);'
    member_drps_sql= 'select count(id) as num from et_member_drps where DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(add_time);'
    member_wd_sql= 'select count(id) as num from et_member_withdrawal where DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(start_time);'

    new_mems = db.session.execute(member_sql).first()
    new_task_orders = db.session.execute(task_orders_sql).first()
    member_drps= db.session.execute(member_drps_sql).first()
    member_wds= db.session.execute(member_wd_sql).first()

    res_data= dict()
    
    stats={}
    stats['m']= new_mems[0]
    stats['o']= new_task_orders[0]
    stats['d']= member_drps[0]
    stats['w']= member_wds[0]
    res_data['infos'] =  stats
    
    res.update(code=ResponseCode.Success, data= res_data, msg=f'获取成功')
    return res.data

@bp.route('/cre_banners', methods=["POST"])
@login_required
def cre_banners():
    """
    创建banners
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    name = req.get('name')
    b_type = int(req.get('type'))
    d_link = req.get('link')
    img_url = req.get('img_url')
    show_time = str(req.get('show_time'))
    end_time = str(req.get('end_time'))
    sort = int(req.get('sort'))

    if not all([name ,b_type, d_link, img_url, show_time, sort]):
        res.update(code=ResponseCode.InvalidParameter, data={}, msg="缺少参数")
        return res.data

    # 添加数据入库
    add_sql = f"INSERT INTO et_banner (banner_name, banner_type, banner_jumplink, banner_url, show_time, end_time, sorting) \
                    VALUE ('{name}', {b_type}, '{d_link}', '{img_url}', '{show_time}', '{end_time}', {sort})"
    db.session.execute(add_sql)
    try:
        db.session.commit()
        res.update(code=ResponseCode.Success, data={}, msg="添加成功!")
        return res.data
    except Exception as why:
        res.update(code=ResponseCode.Success, data={}, msg=f"数据添加失败{why}")
        return res.data

@bp.route('/banners_lists', methods=["GET"])
@login_required
def banners_lists():
    """
    banners列表
    :return: json
    """

    res = ResMsg()

    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    
    p_i, p_num = (page_index - 1) * page_size, page_size

    data_sql = f"SELECT * FROM et_banner WHERE status != 1 ORDER BY show_time ASC LIMIT {p_i}, {p_num}"

    data_list = db.session.execute(data_sql)
    res_data = dict()

    if data_list:
        b_lists = [{k: v for (k, v) in row.items()} for row in data_list]
        count_b = b_lists
        res_data['list'] = b_lists
        res_data['length'] = len(count_b)
        res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_b)}banner获取成功")
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
        return res.data

@bp.route('/d_banner', methods=["POST"])
@login_required
def d_banner():
    """
    删除banner
    :return: json
    """

    res = ResMsg()
    req = request.get_json(force=True)

    banner_id = req.get('id')
    status = req.get('status')

    d_sql = f"UPDATE et_banner set status={status} WHERE id={int(banner_id)}"

    d_ex = db.session.execute(d_sql)

    try:
        db.session.commit()
        if status == 1:
            msg = "删除成功!"
        else:
            msg = "更改成功!"
        res.update(code=ResponseCode.Success, data={}, msg=msg)
        return res.data
    except Exception as why:
        res.update(code=ResponseCode.Success, data={}, msg=f"删除异常{why}")
        return res.data

@bp.route('/c_banner', methods=["POST"])
@login_required
def c_banner():
    """
    编辑banner
    :return: json
    """

    res = ResMsg()
    req = request.get_json(force=True)

    b_id = req.get('id')
    name = req.get('name')
    b_type = int(req.get('type'))
    d_link = req.get('link')
    img_url = req.get('img_url')
    show_time = str(req.get('show_time'))
    end_time = str(req.get('end_time'))
    sort = int(req.get('sort'))

    if not all([name ,b_type, d_link, img_url, show_time, sort]):
        res.update(code=ResponseCode.InvalidParameter, data={}, msg="缺少参数")
        return res.data

    # 添加数据入库
    add_sql = f"UPDATE et_banner SET banner_name='{name}', banner_type={b_type}, banner_jumplink = '{d_link}', banner_url = '{img_url}', show_time = '{show_time}', end_time = '{end_time}', sorting = {sort} WHERE id={b_id}"
    db.session.execute(add_sql)
    try:
        db.session.commit()
        res.update(code=ResponseCode.Success, data={}, msg="修改成功!")
        return res.data
    except Exception as why:
        res.update(code=ResponseCode.Success, data={}, msg=f"数据修改失败{why}")
        return res.data















