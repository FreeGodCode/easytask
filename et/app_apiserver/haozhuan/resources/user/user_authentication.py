import datetime
import re
import time
from flask_restplus import Resource, reqparse, fields, Namespace
from flask import current_app, g
from cache.user import UserCache
from cache.user_center import UserCentreCache
from haozhuan.resources.user import user_api
from utils.alicloud_authentication import ali_authentication
from utils.http_status import HttpStatus
from utils.constants import ET_MEMBER_EXTEND,MEMBERS_TABLE, ET_MEMBER_EXTEND, ET_MEMBER_EARNINGS
from utils.mysql_cli import MysqlWrite,MysqlSearch
from common.cache.user_extend import UserExtendCache
from utils.parser import id_car, name_str
from utils.card import checkIdcard, verifid_card_1

auth = Namespace('authentication', description='实名认证 请求方式:表单')
user_api.add_namespace(auth)

authentication_model = user_api.model('authentication', {
        'idNo': fields.Integer(required=True, description='身份证'),
        'name': fields.Integer(required=True, description='姓名'),
        '返回内容': fields.String(description='当前接口返回验证回调'),
})

@auth.route('')
class User_AuthenticationView(Resource):
    @auth.expect(authentication_model)
    def post(self):
        """用户实名认证"""
        parser = reqparse.RequestParser()
        parser.add_argument('mobile', type=int, required=True, location='json')
        parser.add_argument('idNo', type=str, required=True, location='json')
        parser.add_argument('name', type=str, required=True, location='json')
        args = parser.parse_args()
        mobile = str(args.mobile)
        # 检验身份证格式
        if not re.match(r'[\u4e00-\u9fa5]', args.name) or not re.match(r'[^\u4e00-\u9fa5]', args.idNo):
            return {'error': '请输入正确格式'}, HttpStatus.OK.value
        # 查询身份证是否已经使用过
        try:
            sm = current_app.redis_cli.sismember('id_num',args.idNo)
            if sm is True:
                return {'error': '此身份证已实名,无法重复使用'}, HttpStatus.OK.value
        except TypeError as e:
            current_app.logger.error(f"TypeError{e}")
        # 再次检验身份证是否正常
        try:
            ic_check = checkIdcard(args.idNo)
        except Exception as e:
            current_app.logger.error(f"Exception: {e}")
            return {'error': '请检查身份证号码是否正确'} ,HttpStatus.OK.value
        # # 获取用户扩展缓存 #todo 缓存查询出现问题,想办法加上登录装饰器并跳过阿里屏蔽
        # res = UserExtendCache(us['id']).get()
        # if res:
        #     return {'error': '此身份证已实名,无法重复实名'}, HttpStatus.OK.value
        # 前往实名
        mes = verifid_card_1(args.name, args.idNo)
        if mes is False:
            return {'error': '系统繁忙,请稍后尝试.'}, HttpStatus.OK.value
        # todo 判断验证信息状态
        if mes['status'] != '01':
            return {'error': '错误身份证信息'}, HttpStatus.OK.value
        if mes['sex'] == '男':
            sex = 1
        else:
            sex = 2
        # 查询用户user_id
        us = MysqlSearch().get_one(f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile={args.mobile}")
        # 入库实名信息
        sql_w = f"INSERT INTO {ET_MEMBER_EXTEND} (`name`,member_id,id_num,sex,province,city,age) VALUE ('{args.name}','{us['id']}','{mes['idCard']}','{sex}','{mes['province']}','{mes['city']}','{mes['birthday'][: 4]}')"
        MysqlWrite().write(sql_w)
        user_extend = {
            'member_id': us['id'],
            'id_number': mes['idCard'],
            'sex': sex,
            'province': mes['province'],
            'city': mes['city'],
            'age': mes['birthday'][: 4],
            'name': args.name
        }
        # 写入用户扩展信息缓存
        # UserExtendCache(us['id']).save(user_extend)
        if mes['status'] == "01":
            # 修改实名状态,入库用户真实姓名
            sql_update = f"UPDATE {MEMBERS_TABLE} SET setreal=1,realname='{args.name}' WHERE ID='{us['id']}'"
            res = MysqlWrite().write(sql_update)
            if res == 1:
                rc = current_app.redis_cli
                rc.delete('user_info_:{}'.format(args.mobile))
                rc.delete('user_center:{}'.format(us['id']))
                # 添加身份证到set
                rc.sadd('id_num',args.idNo)
                UserCache(args.mobile).get()
                return {'data': mes['status']}, HttpStatus.OK.value
        else:
            return {'error': mes['status']}, HttpStatus.OK.value