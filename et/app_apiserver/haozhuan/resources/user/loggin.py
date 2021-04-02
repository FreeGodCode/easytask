import json
import random
import re
from flask import current_app, g
from flask_restplus import Resource, reqparse, Namespace, fields
from datetime import datetime, timedelta
from cache.user import UserCache
from cache.relation_tree import MemberRelationTreeCache
from haozhuan.resources.user import user_api
from utils.hashids_iiuv import hashids_iivu_encode
from utils.jwt_util import generate_jwt
from utils.constants import MEMBERS_TABLE
from utils.mysql_cli import MysqlSearch,MysqlWrite
from utils.snowflake.id_worker import IdWorker
from utils.http_status import HttpStatus
from utils.short_link import get_short_link


login = Namespace('login',description='手机登录 请求方式:json')
user_api.add_namespace(login)

register_model = user_api.model('Register', {
        'mobile': fields.Integer(required=True, description='手机号码'),
        'code': fields.Integer(required=True, description='手机验证码'),
        'iiuv': fields.String(description='是否通过二维码过来注册,是就要携带,不是可以为空'),
        '返回内容': fields.String(description='当前接口返回一个token'),
})

@login.route('')
class LoginView(Resource):
    def _generate_tokens(self, user_id, setreal, mobile, with_refresh_token=True):
        """
        生成token
        :param user_id: 用户id
        :return: token, refresh_token
        """
        # 颁发JWT
        now = datetime.utcnow()
        # expiry = now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS'])
        expiry = now + timedelta(hours=current_app.config['JWT_REFRESH_DAYS'])
        token = generate_jwt({'user_id': user_id, 'setreal': setreal, 'mobile': mobile,'refresh': False}, expiry)
        refresh_token = None
        if with_refresh_token:
            refresh_expiry = now + timedelta(days=current_app.config['JWT_REFRESH_DAYS'])
            refresh_token = generate_jwt({'user_id': user_id, 'refresh': True, 'setreal': setreal, 'mobile': mobile,}, refresh_expiry)
        return token, refresh_token

    @login.expect(register_model)
    def post(self):
        parser_form = reqparse.RequestParser()
        parser_form.add_argument('mobile', type=str, required=True, location='json')
        parser_form.add_argument('code', type=str, required=True, location='json')
        parser_form.add_argument('iiuv', type=str, location='json')
        args = parser_form.parse_args()
        mobile = args.mobile
        code = args.code
        iiuv_data = args.iiuv
        if not re.match(r'^\d{6}$', code):
            return {'error': '验证码格式错误'}, HttpStatus.OK.value
        if iiuv_data:
            cx = MysqlSearch().get_one(f"SELECT id FROM {MEMBERS_TABLE} WHERE IIUV='{iiuv_data}'")
            if cx is False:
                iiuv_data = None
        # 从redis中获取验证码
        key = 'app:code:{}'.format(mobile)
        try:
            real_code = current_app.redis_cli.get(key)
            if not real_code or real_code.decode() != code:
                return {'error': '验证码错误.'}, HttpStatus.OK.value
        except ConnectionError as e:
            current_app.logger.error(e)
        # 查询,保存用户
        user_cache = current_app.redis_cli.hget('user_info_:{}'.format(mobile),0)
        if user_cache:
            dict_user_cache = json.loads(user_cache.decode())
            if dict_user_cache['mobile'] == mobile:
                token, refresh_token = self._generate_tokens(dict_user_cache['id'], dict_user_cache['setreal'],dict_user_cache['mobile'])
                token_data = [
                    token,
                    refresh_token
                ]
                return {'token': token_data, "手机号码": int(mobile), 'data': '欢迎登陆', }, HttpStatus.OK.value
        if user_cache is None:
            sql = f"SELECT id,setreal,mobile FROM {MEMBERS_TABLE} WHERE mobile='{args.mobile}';"
            user_info = MysqlSearch().get_one(sql)
            if user_info and user_info['mobile'] == mobile:
                user_info = UserCache(mobile).get()
                token, refresh_token = self._generate_tokens(user_info['id'], user_info['setreal'],user_info['mobile'])
                token_data = [
                    token,
                    refresh_token
                ]
                return {'token': token_data, "手机号码": int(mobile)}, HttpStatus.OK.value
            else:
                # 新用户数据入库
                # 生成uuid
                nickname = IdWorker(1, 2, 0).get_id()
                user_mobile = mobile
                # 随机头像生成
                ran_data = random.randint(1,12)
                txx = f"http://static.hfj447.com/avatars/{ran_data}.jpg"
                sql = f"INSERT INTO {MEMBERS_TABLE} (nickname,mobile,avatar) VALUE ('{nickname}','{user_mobile}','{txx}')"
                res = MysqlWrite().write(sql)
                # 查询新用户id,生成iiuv邀请码
                ii = MysqlSearch().get_one(f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile='{user_mobile}'")
                member_iiuv = hashids_iivu_encode(ii['id'])
                # 生成邀请dwz入库
                short_link = get_short_link(member_iiuv)
                # 生成iiuv入库
                iiu = MysqlWrite().write(f"UPDATE {MEMBERS_TABLE} SET IIUV='{member_iiuv},short_link='{short_link}' WHERE id='{ii['id']}'")
                if res == 1 and iiuv_data == None:
                    user_info = UserCache(mobile).get()
                    MemberRelationTreeCache().tree(args.mobile, None)
                    # 返回token
                    token, refresh_token = self._generate_tokens(user_info['id'], user_info['setreal'],
                                                                 user_info['mobile'])
                    token_data = [
                        token,
                        refresh_token
                    ]
                    return {'token': token_data, "手机号码": int(mobile)}, HttpStatus.OK.value

                elif res == 1 and iiuv_data:
                    MemberRelationTreeCache().tree(args.mobile, iiuv_data)
                    # 返回token
                    user_info = UserCache(mobile).get()
                    token, refresh_token = self._generate_tokens(user_info['id'], user_info['setreal'],
                                                                 user_info['mobile'])
                    token_data = [
                        token,
                        refresh_token
                    ]
                    return {'token': token_data, "手机号码": int(mobile)}, HttpStatus.OK.value

    def get(self):
        """刷新token"""
        user_id = g.user_id
        setreal = g.setreal
        mobile = g.mobile
        if user_id:
            # 判断用户状态
            user_enable = UserCache(g.mobile).get()
            if user_enable['status'] == 2:
                return {'error': '用户禁用.'}, HttpStatus.OK.value
            token, refresh_token = self._generate_tokens(user_id, setreal, mobile, with_refresh_token=False)
            return {'token': token}, HttpStatus.OK.value
        else:
            return {'error': '错误刷新token', 'error_code': 4005}, HttpStatus.OK.value






