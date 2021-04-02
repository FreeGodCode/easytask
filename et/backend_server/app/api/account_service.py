import hashlib
# import json
import logging
import time

# from app.models.accounts import EtAccountRole
from flask import Blueprint, session, request

from app.models.accounts import EtAccount
from app.utils.auth import Auth, login_required
from app.utils.code import ResponseCode, ResponseMessage
from app.utils.core import db, scheduler
from app.utils.response import ResMsg
from app.utils.util import route, helpers

bp = Blueprint("account", __name__, url_prefix='/account')
# 运营平台账号服务
logger = logging.getLogger(__name__)


def hash_password(password):
    m = hashlib.md5()
    b = password.encode(encoding='utf-8')
    m.update(b)
    return m.hexdigest()


@bp.route( '/act', methods=["GET"])
def test_packed_response():
    """
    测试响应封装
    :return: json
    """
    res = ResMsg()
    sched = scheduler
    task_state = str(sched.state)
    if task_state != None:
        logger.info(task_state)
        logger.info(dir(sched))
        logger.info(sched.get_jobs())
        
    test_dict = {}
    test_dict['st'] = sched.state
    res.update(code=ResponseCode.LoginSuccess, data=test_dict)
    return res.data


@bp.route( '/reg', methods=["POST", "OPTIONS"])
def handle_reg():
    """
    账号注册接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    username = req.get("username")
    password = req.get("password")
    password_hash = hash_password(password)

    user = db.session.query(EtAccount).filter(EtAccount.name == username).first()

    if user:
        res.update(code=ResponseCode.Success, data={}, msg='账户已存在,无需重复注册')
        return res.data
    else:

        new_user = EtAccount(name=username, password=password_hash, role_id=1)
        db.session.add(new_user)
        try:
            db.session.commit()
            res.update(code=ResponseCode.Success, data={}, msg='账户注册成功')
            return res.data
        except Exception as why:

            res.update(code=ResponseCode.Success, data={}, msg=f'数据添加失败{why}')
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
    userid = payload['user_id']

    res_data = dict()

    user = db.session.query(EtAccount.id, EtAccount.name, EtAccount.role_id, EtAccount.status).filter(
        EtAccount.name == userid).first()
    if user:
        res_data.update(dict(zip(user.keys(), user)))
        if res_data['role_id'] == 1:
            res_data['roles'] = ['admin']
            res_data['avatar'] = 'https://qiniu.staticfile.org/user_avatar.jpg'
            del res_data['role_id']
        res.update(code=ResponseCode.Success, data=res_data, msg='账号获取成功')
        return res.data
    else:

        res.update(code=ResponseCode.Success, data={}, msg='账户异常')
        return res.data


@bp.route('/login', methods=["POST"])
def handle_login():
    """
    登录接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    username = req.get("username")
    password = req.get("password")
    password_hash = hash_password(password)
    now_timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    user = db.session.query(EtAccount).filter(EtAccount.name == username,
                                              EtAccount.password == password_hash).first()

    res_data = dict()
    if user:
        user = db.session.query(EtAccount.name).first()
        res_data.update(dict(zip(user.keys(), user)))

        db.session.query(EtAccount).filter(EtAccount.name == username).update({"last_login": now_timestr})

        access_token, refresh_token = Auth.encode_auth_token(user_id=username)

        res_data.update({"access_token": access_token.decode("utf-8"),
                         "refresh_token": refresh_token.decode("utf-8")})

        res.update(code=ResponseCode.LoginSuccess, data=res_data, msg=ResponseMessage.LoginSuccess)

        return res.data
    else:
        res.update(code=ResponseCode.LoginFail, data={}, msg=ResponseMessage.LoginFail)

        return res.data


@bp.route('/edit_account', methods=["POST", "OPTIONS"])
@login_required
def handle_account_edit():
    """
    账户修改接口
    :return: json 
    """
    res = ResMsg()
    req = request.get_json(force=True)

    userid = req.get("userid")
    username = req.get("username")
    password = req.get("password")
    password_hash = hash_password(password)
    role_id = req.get("role")
    status = req.get("status")
    update_dict = {
        "name": username,
        "password": password_hash,
        "role_id": role_id,
        "status": status
    }
    update_dict_ready = helpers.rmnullkeys(update_dict)
    user = db.session.query(EtAccount).filter(EtAccount.id == userid).first()

    if user:
        db.session.query(EtAccount).filter(EtAccount.id == userid).update(update_dict_ready)
        try:
            db.session.commit()
            res.update(code=ResponseCode.Success, data={}, msg='修改成功')
            return res.data
        except Exception as why:
            res.update(code=ResponseCode.Success, data={}, msg=f'修改失败，请稍后再试{why}')
            return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='修改失败，请稍后再试')

        return res.data


@bp.route('/lists', methods=["GET"])
@login_required
def handle_lists():
    """
    获取用户列表
    :return: json
    """
    res = ResMsg()
    page_index = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    users = db.session.query(EtAccount).limit(page_size).offset((page_index - 1) * page_size).all()
    counts = db.session.execute("SELECT count(*) FROM et_accounts").first()
    res_data = dict()
    if users:
        res_data['list'] = helpers.model_to_dict(users)
        res_data['length'] = counts[0]
        res.update(code=ResponseCode.Success, data=res_data, msg=f'{type(users)}获取成功')

        return res.data
    else:
        res.update(code=ResponseCode.Success, data={}, msg='数据获取异常')

        return res.data


@bp.route('/refresh_token', methods=["GET"])
# @login_required
def refresh_token():
    """
    刷新token，获取新的数据获取token
    :return:
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
    access_token = request.args.get("token", header_token)
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


@bp.route('/channel_list', methods=["GET"])
def heandel_channels():
    """
    渠道列表数据接口
    :return: json
    """
    res = ResMsg()
    res_data = {}

    list_sql = "SELECT * FROM et_channels"
    ch_lists = db.session.execute(list_sql).fetchall()

    res_data['list'] = [{key: value for (key, value) in row.items()} for row in ch_lists]
    res_data['length'] = len(res_data['list'])

    res.update(code=ResponseCode.Success, data=res_data, msg="列表数据获取成功")
    return res.data


@bp.route('/channel_add', methods=["POST"])
def heandel_add_channel():
    """
    渠道数据添加接口
    :return: json
    """
    res = ResMsg()
    req = request.get_json(force=True)

    ch_name = req.get("ch_name")

    if not ch_name:
        res.update(code=ResponseCode.Success, data={}, msg="渠道名称不能为空")
        return res.data

    account_name = session.get("user_name")

    insert_sql = f"INSERT INTO et_channels (`ch_name`, `ch_type` `account`) VALUES ('{ch_name}', 1,  '{account_name}');"

    db.session.execute(insert_sql)
    db.session.commit()

    res.update(code=ResponseCode.Success, data={}, msg="列表数据添加成功")
    return res.data
