from flask import Blueprint, jsonify, session, request, current_app
import logging
import hashlib
import time
import random
import string
from app.utils.response import ResMsg
from app.models.mercharnt import ETMerchants
from app.models.task import EtTask
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.core import db
from app.utils.auth import Auth, login_required
from app.utils.util import helpers
from app.utils.util import Redis

bp = Blueprint("merchants", __name__, url_prefix='/merchants')
# 商户管理服务
logger = logging.getLogger(__name__)

task_info_key= "tasks_info"
task_info_u_key= "tasks_info_"
task_detail_key= "tasks_detail_:"
task_complete_key = "complete_tasks_:"
complete_tasks_uid_key = "complete_tasks_"
task_verifyed_key = "verifyed_tasks_:"
tasks_high_info_key= "tasks_high_info"


# 哈希md5密码加密
def hash_password(password):
    m= hashlib.md5()
    b = password.encode(encoding='utf-8')
    m.update(b)
    return m.hexdigest()

@bp.route('/registered', methods=["POST"])
@login_required
def registered():
    """
    商户注册接口
    :return:json
    """
    res = ResMsg()
    req = request.get_json(force=True)
    username = req.get("username")
    password = req.get("password")
    mobile = req.get("mobile")
    industry = req.get("industry")
    account_name= session.get("user_name")
    if not all([username, password, mobile, industry]):
        res.update(code=ResponseCode.Success, data={}, msg="参数异常")
        return res.data
    password_hash = hash_password(password)
    # 获取用户ip信息,todo反向代理可能要设置X-Forwarded-For这个Key才能拿到
    # ip = request.headers.get('X-Forwarded-For').split(',')[0]
    ip = request.remote_addr
    user = db.session.query(ETMerchants).filter(ETMerchants.username == username).first()
    if user:
        res.update(code=ResponseCode.Success, data={}, msg="账户已存在,无需重复注册")
        return res.data
    else:
        new_user = ETMerchants(username=username, password=password_hash, mobile=mobile, industry=industry, ip=ip, accounts_name=account_name)
        db.session.add(new_user)
        try:
            db_res = db.session.commit()
            res.update(code=ResponseCode.Success, data={}, msg='账户注册成功')
            return res.data
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f"数据添加失败{why}")
            return res.data

@bp.route('/login', methods=["POST"])
def login():
    """
    商户登录接口
    :return:
    """
    res = ResMsg()
    req = request.get_json(force=True)

    username = req.get("username")
    password = req.get("password")
    password_hash = hash_password(password)
    noew_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    user = db.session.query(ETMerchants).filter(ETMerchants.username == username, ETMerchants.password == password_hash).first()

    res_data = dict()
    if user:
        user = db.session.query(ETMerchants.username).first()
        res_data.update(dict(zip(user.keys(), user)))

        db.session.query(ETMerchants).filter(ETMerchants.username == username).update({"last_login": noew_timestr})

        access_token, refresh_token = Auth.encode_auth_token(user_id=username)
        res_data.update({"access_token": access_token.decode("utf-8"), "refresh_token": refresh_token.decode("utf-8")})
        res.update(code=ResponseCode.LoginSuccess, data=res_data, msg=ResponseMessage.LoginSuccess)

        return res.data
    else:
        res.update(code=ResponseCode.LoginFail, data={}, msg=ResponseMessage.LoginFail)
        return res.data

@bp.route('/lists', methods=["GET"])
@login_required
def mercharnt_list():
    """
    获取商户列表
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    p_i, p_num = (page_index - 1) * page_size, page_size

    k = 'id, nickname, user_type, industry, status, last_login, ip, password, username, mobile'
    oem_sql = f"SELECT {k} FROM et_merchants ORDER BY last_login DESC LIMIT {p_i}, {p_num}"
    oem = db.session.execute(oem_sql).fetchall()
    res_data = dict()
    if oem:
        olists = [{k: v for (k, v) in row.items()} for row in oem]
        count_oem = olists
        res_data['list'] = olists
        res_data['length'] = len(count_oem)
        res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_oem)}获取成功")
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
        return res.data

@bp.route('/merlists', methods=["GET"])
def merlists():
    """
    商户管理列表
    :retrun: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    p_i, p_num = (page_index - 1) * page_size, page_size

    username = request.args.get('username', '')

    if username == '':
        us_sql = f"SELECT SUM(t1.TASK_VERIFYING) as task_ver,SUM(t1.TASK_COMPLETES) as task_com,em.username,em.balance,em.addtime,em.lock_balance,em.industry,em.id,em.status FROM (SELECT \
                SUM( IF ( STATUS = 4, 1, 0 ) ) AS TASK_COMPLETES,\
                SUM( IF ( STATUS = 2, 1, 0 ) ) AS TASK_VERIFYING,\
                task_id \
                FROM \
                 et_task_orders \
                GROUP BY \
                 ( task_id ) \
                ) as t1 \
                LEFT JOIN et_tasks as et on t1.task_id=et.id \
                LEFT JOIN et_merchants as em on em.id=et.mer_id \
                WHERE em.id is not null \
                GROUP BY em.username,em.balance,em.addtime,em.lock_balance,em.industry,em.id,em.status \
                ORDER BY addtime DESC LIMIT {p_i}, {p_num}"

        u_lists = db.session.execute(us_sql).fetchall()
        res_data = dict()
        if u_lists:
            wi_list = [{k: v for (k, v) in row.items()} for row in u_lists]
            count_wi = wi_list
            res_data['list'] = wi_list
            res_data['length'] = len(count_wi)
            res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_wi)}获取成功")
            return res.data
        else:
            res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
            return res.data

    else:
        us_sql = f"SELECT SUM(t1.TASK_VERIFYING) as task_ver,SUM(t1.TASK_COMPLETES) as task_com,em.username,em.balance,em.addtime,em.lock_balance,em.industry,em.id,em.status FROM (SELECT \
                SUM( IF ( STATUS = 4, 1, 0 ) ) AS TASK_COMPLETES,\
                SUM( IF ( STATUS = 2, 1, 0 ) ) AS TASK_VERIFYING,\
                task_id \
                FROM \
                 et_task_orders \
                GROUP BY \
                 ( task_id ) \
                ) as t1 \
                LEFT JOIN et_tasks as et on t1.task_id=et.id \
                LEFT JOIN et_merchants as em on em.id=et.mer_id \
                WHERE em.id is not null and em.username = '{username}'\
                GROUP BY em.username,em.balance,em.addtime,em.lock_balance,em.industry,em.id,em.status \
                ORDER BY addtime DESC LIMIT {p_i}, {p_num}"
        u_data = db.session.execute(us_sql).first()
        if u_data:
            json_data = {k: v for k, v in u_data.items()}
            res.update(code=ResponseCode.Success, data=json_data, msg="获取成功!")
            return res.data
        else:
            res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
            return res.data


@bp.route('/mertasks', methods=["GET"])
def mertasks():
    """
    商户任务明细接口
    :retrun: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    p_i, p_num = (page_index - 1) * page_size, page_size

    mer_id = request.args.get('id',)
    if mer_id:
        m = f'SELECT t1.TASK_COMPLETES, t1.task_id, t1.TASK_VERIFYING, t1.TASK_REJECTED, et.NAME, et.task_reward, em.id \
                FROM ( SELECT SUM( IF ( STATUS = 4, 1, 0 ) ) AS TASK_COMPLETES,\
                    SUM( IF ( STATUS = 2, 1, 0 ) ) AS TASK_VERIFYING, \
                        SUM( IF ( STATUS = 5, 1, 0 ) ) AS TASK_REJECTED,\
                            task_id FROM et_task_orders GROUP BY ( task_id ) ) AS t1 \
                                LEFT JOIN et_tasks AS et ON t1.task_id = et.id \
                                    LEFT JOIN et_merchants AS em ON em.id = et.mer_id \
                                        WHERE em.`status` = 1 AND em.id = {mer_id} \
                                            ORDER BY addtime DESC LIMIT {p_i}, {p_num}'
        us_sql = f"SELECT id,username,industry,balance,lock_balance,addtime FROM et_merchants \
                        ORDER BY addtime DESC LIMIT {p_i}, {p_num}"
        u_lists = db.session.execute(us_sql).fetchall()
        res_data = dict()
        if u_lists:
            wi_list = [{k: v for (k, v) in row.items()} for row in u_lists]
            count_wi = wi_list
            res_data['list'] = wi_list
            res_data['length'] = len(count_wi)
            res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_wi)}获取成功")
            return res.data
        else:
            res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
            return res.data

@bp.route('/recharge', methods=["POST"])
@login_required
def merrecharge():
    """
    商户充值
    :retrun: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    money = req.get("money")
    user_id = req.get("id")
    account_name = session.get("user_name")
    # 使用乐观锁修改用户余额
    user_sql = f"SELECT balance,balance_version FROM et_merchants WHERE id={user_id}"
    user = db.session.execute(user_sql).first()
    user_data  = dict(user)
    # 生成20位随机字符串
    salt = ''.join(random.sample(string.ascii_letters + string.digits, 20))
    version_time = str(time.time()) + salt
    amount = money * 100
    all_amount = user_data['balance'] + amount
    logging.error(user_data)
    try:
        add_sql = f"UPDATE et_merchants SET balance={all_amount}, balance_version='{version_time}' WHERE balance_version='{user_data['balance_version']}' and id={user_id}"
        db.session.execute(add_sql)
        db.session.commit()
        # 生成时间戳流水号
        t = time.time()
        # 加入流水表
        add_w_sql = f"INSERT INTO et_recharge_withdrawal (accounts_name, withdrawal_num, mer_id, balance) VALUE ('{account_name}', {int(t)}, {user_id}, {money})"
        db.session.execute(add_w_sql)
        db.session.commit()
        res.update(code=ResponseCode.Success, data={}, msg=f"充值成功!")
        return res.data
    except Exception as why:
        res.update(code=ResponseCode.Success, data={}, msg=f"充值失败{why},请稍后再试")
        return res.data

@bp.route('/ban_mer', methods=["POST"])
def ban_mer():
    """
    封禁商户
    :return json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    mar_id = req.get("id")
    status= req.get("status")

    update_dict = {
        'status': status
    }
    update_dict_ready = helpers.rmnullkeys( update_dict )
    user = db.session.query(ETMerchants).filter(ETMerchants.id == mar_id).first() 
    if user:
        db.session.query(ETMerchants).filter(ETMerchants.id == mar_id).update(update_dict_ready)
        try:
            db.session.commit()
            res.update(code=ResponseCode.Success, data={}, msg="完成封禁用户")
            return res.data
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f"修改失败,请稍后再试{why}")
            return res.data

@bp.route('/edit_mer', methods=["POST"])
def editmer():
    """
    商户信息修改接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    mer_id = req.get("id")
    status = req.get("status")
    password = req.get("password")
    password_hash = hash_password(password)

    update_dict = {
        "password": password_hash,
        "status": status
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)
    user = db.session.query(ETMerchants).filter(ETMerchants.id == mer_id).first()

    if user:
        db.session.query(ETMerchants).filter(ETMerchants.id == mer_id).update(update_dict_ready)
        try:
            db.session.commit()
            res.update(code=ResponseCode.Success, data={}, msg="修改成功")
            return res.data
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f"修改失败,请稍后再试{why}")
            return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg=f"修改失败,请稍后再试")
        return res.data

@bp.route('/mer_with', methods=["GET"])
def mer_with():
    """
    商户资金流水接口
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    p_i, p_num = (page_index - 1) * page_size, page_size

    username = request.args.get("username", '')
    s_time = str(request.args.get("s_time", ''))
    e_time = str(request.args.get("e_time", ''))

    if username == '' and s_time == '' and e_time == '':
        w_sql = f"SELECT e.id, e.withdrawal_num, e.add_time, e.balance, e.accounts_name, etm.username \
                    FROM et_recharge_withdrawal as e \
                        LEFT JOIN et_merchants as etm on etm.id = e.mer_id \
                                ORDER BY e.add_time DESC LIMIT {p_i}, {p_num}"
        w_list = db.session.execute(w_sql).fetchall()
        res_data = dict()
        if w_list:
            wi_list = [{k: v for (k, v) in row.items()} for row in w_list]
            count_wi = wi_list
            res_data['list'] = wi_list
            res_data['length'] = len(count_wi)
            res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_wi)}获取成功")
            return res.data
        else:
            res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
            return res.data

    elif username != '':
        w_sql = f"SELECT e.id, e.withdrawal_num, e.add_time, e.balance, e.accounts_name, etm.username \
                    FROM et_recharge_withdrawal as e \
                        LEFT JOIN et_merchants as etm on etm.id = e.mer_id \
                            WHERE etm.username = '{username}'"
        w_data = db.session.execute(w_sql).first()
        if w_data:
            json_data = {k: v for k, v in w_data.items()}
            res.update(code=ResponseCode.Success, data=json_data, msg="获取成功!")
            return res.data
        else:
            res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
            return res.data

    elif s_time != '' and e_time != '':
        w_sql = f"SELECT e.id, e.withdrawal_num, e.add_time, e.balance, e.accounts_name, etm.username \
            FROM et_recharge_withdrawal as e \
                LEFT JOIN et_merchants as etm on etm.id = e.mer_id \
                    where e.add_time >= '{s_time}' and e.add_time <= '{e_time}'\
                        ORDER BY e.add_time DESC LIMIT {p_i}, {p_num}"
        w_list = db.session.execute(w_sql).fetchall()
        res_data = dict()
        if w_list:
            wi_list = [{k: v for (k, v) in row.items()} for row in w_list]
            count_wi = wi_list
            res_data['list'] = wi_list
            res_data['length'] = len(count_wi)
            res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_wi)}获取成功")
            return res.data
        else:
            res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
            return res.data

@bp.route('/changes_tasks', methods=["GET"])
def changes_tasks():
    """
    商户任务状态修改接口
    """
    res = ResMsg()
    task_id = request.args.get('task_id', '')
    u_pass = request.args.get('u_pass', '')
    rejected = request.args.get('rejected', '')
    preview = request.args.get('preview', '')
    shelves = request.args.get('shelves', '')
    comment = request.args.get('comment', '')

    where_cond = ''
    if u_pass != '':
        where_cond = 2
    elif rejected != '':
        where_cond = 5
        l_sql = f"UPDATA et_tasks_verify set comment={comment} where task_id={task_id}"
        db.session.execute(l_sql)
        db.session.commit()
    elif shelves != '':
        where_cond = 1
    task_sql = f"UPDATE et_tasks set status={where_cond} WHERE id={task_id}"
    db.session.execute(task_sql)
    res = db.session.commit()
    if res == 1:
        res.update(code=ResponseCode.Success, data={}, msg="修改成功")
        return res.data
    else:
        res.updata(code=ResponseCode, data={}, msg="修改失败,请稍后再试")
        return res.data


@bp.route('/audit_lists', methods=["GET"])
def audit():
    """
    商户任务审核
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page",  1))
    page_size = int(request.args.get("limit", 10))
    p_i, p_num = (page_index - 1) * page_size, page_size

    username = request.args.get("username", '')
    s_time = str(request.args.get("s_time", ''))
    e_time = str(request.args.get("e_time", ''))
    task_name = request.args.get("task_name", '')
    mer_name = request.args.get("mer_name", '')
    account_name = request.args.get("account_name", '')
    task_class = request.args.get("task_class", '')
    task_status = request.args.get("task_status", '')

    where_cond = ''
    if task_name != '':
        logging.error(111)
        where_cond = f"WHERE (et.status = 1 or et.status = 5) and et.name like '%{task_name}%'"
    elif account_name != '':
        logging.error(222)
        where_cond = f"WHERE (et.status = 1 or et.status = 5) and e.account_name like '%{account_name}%' "
    elif task_class != '':
        logging.error(333)
        where_cond = f"WHERE (et.status = 1 or et.status = 5) and et.task_class = {task_class} "
    elif task_status != '':
        logging.error(444)
        where_cond = f"WHERE et.status = {task_status} "
    elif s_time != '' and e_time != '':
        logging.error(555)
        where_cond = f"WHERE (et.status = 1 or et.status = 5) and e.add_time >= '{s_time}' and e.add_time <= '{e_time}'"
    elif username != '':
        where_cond = f"WHERE (et.status = 1 or et.status = 5) and etm.username like '%{username}%'"
    else:
        logging.error(666)
        where_cond = f"WHERE et.status = 1 or et.status = 5"

    task_c = 'e.tasks_id,e.account_name,e.verify_time,e.add_time,e.comment,et.name,et.task_reward,et.`status`,et.task_class,etm.username,et.tasks_counts'
    task_sql = f"SELECT {task_c} FROM et_tasks_verify as e \
                                    LEFT JOIN et_tasks as et on et.id=e.tasks_id \
                                        LEFT JOIN et_merchants as etm on etm.id = et.mer_id \
                                            {where_cond} \
                                                ORDER BY e.add_time DESC;"

    t_lists = db.session.execute(task_sql).fetchall()
    res_data = dict()
    list_data = list()
    if t_lists:
        for k in t_lists:
            data = dict(k)
            dic = {
                'tasks_id': data['tasks_id'],
                'account_name': data['account_name'],
                'verify_time': data['verify_time'],
                'add_time': data['add_time'],
                'name': data['name'],
                'task_reward': data['task_reward'],
                'status': data['status'],
                'task_class': data['task_class'],
                'username': data['username'],
                'tasks_counts': data['tasks_counts'],
                'all': data['tasks_counts'] * data['task_reward'],
                'comment': data['comment']
            }
            list_data.append(dic)
        count_wi = list_data
        res_data['list'] = list_data
        res_data['length'] = len(count_wi)
        res.update(code=ResponseCode.Success, data=res_data, msg=f"{len(count_wi)}获取成功")
        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg="数据获取异常")
        return res.data

@bp.route('/getinfo', methods=["GET"])
@login_required
def handle_info():
    """
    账号详情
    :return: json
    """
    res = ResMsg()
    
    token = request.args.get("token")
    payload = Auth.decode_auth_token(token)
    userid= payload['user_id']

    res_data= dict()
    
    user = db.session.query(ETMerchants.id, ETMerchants.username, ETMerchants.mobile, ETMerchants.status).filter(ETMerchants.username == userid).first()
    if user:
        res_data.update(dict(zip(user.keys(), user)))
        if res_data['status']== 1:
            res_data['roles']= ['admin']
            res_data['avatar']= 'https://qiniu.staticfile.org/user_avatar.jpg'
        res.update(code=ResponseCode.Success, data=res_data, msg='账号获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={},msg='账户异常')
        return res.data


@bp.route('/refresh_token', methods=["GET"])
# @login_required
def refresh_token():
    """
    刷新token，获取新的数据获取token
    :return: json
    """
    res = ResMsg()
    refresh_token = request.args.get("refresh_token")
    if not refresh_token:
        res.update(code=ResponseCode.InvalidParameter)
        return res.data
    payload = Auth.decode_auth_token(refresh_token)
    # token被串改或过期
    if not payload:
        res.update(code=ResponseCode.PleaseSignIn)
        return res.data

    # 判断token正确性
    if "user_id" not in payload:
        res.update(code=ResponseCode.PleaseSignIn)
        return res.data
    # 获取新的token
    access_token = Auth.generate_access_token(user_id=payload["user_id"])
    data = {"access_token": access_token.decode("utf-8"), "refresh_token": refresh_token}
    res.update(code=ResponseCode.Success, data=data, msg='refresh success!')

    return res.data

@bp.route('/logout', methods=["GET"])
def handle_loginout():
    """
    账号登出接口
    :return:
    """
    res = ResMsg()
    header_token = request.headers.get("xtoken")
    access_token = request.args.get("token",header_token)
    if not access_token:
        res.update(code=ResponseCode.InvalidParameter)
        return res.data
    payload = Auth.decode_auth_token(access_token)
    if not payload:
        res.update(code=ResponseCode.PleaseSignIn)
        return res.data
    if "user_id" not in payload:
        res.update(code=ResponseCode.PleaseSignIn)
        return res.data
    # @todo 移除accesstoken
    access_token = None
    data = {"access_token": None}
    res.update(code=ResponseCode.Success, data=data, msg='logout success!')
    
    return res.data

















