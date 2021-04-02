import re

from flask_restplus import Resource, reqparse, Namespace, fields
from haozhuan.resources.user import user_api
from utils.decorators import login_required, verify_required
from utils.mysql_cli import MysqlWrite
from utils.constants import MEMBERS_TABLE
from utils.http_status import HttpStatus
from flask import g, current_app

bind = Namespace('bind_aliplay',description='绑定支付宝 请求方式:json')
user_api.add_namespace(bind)

bind_model = user_api.model('bind_aliplay', {
        'account': fields.Integer(required=True, description='支付宝账号'),
        'name': fields.Integer(required=True, description='姓名'),
        '提示': fields.String(description='此接口必须携带token'),
})

@bind.route('')
class Bind_aliplayView(Resource):
    method_decorators = [
        verify_required, login_required
    ]
    @bind.expect(bind_model)
    def post(self):
        """绑定支付宝"""
        parser = reqparse.RequestParser()
        parser.add_argument('account', type=str, required=True, location='json')
        args = parser.parse_args()
        sm = current_app.redis_cli.sismember('bind_aliplay', args.account)
        if sm is True:
            return {'error': '此支付宝已绑定,无法重复绑定'}, HttpStatus.OK.value
        if re.match(r'^1([34589][0-9]{9}|(6[01234689]{1})[0-9]{8}|(7[2-9]{1})[0-9]{8})$', args.account) or \
                re.match(r'^([A-Za-z0-9_\-\.\u4e00-\u9fa5])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,8})$', args.account):
            sql = f"UPDATE {MEMBERS_TABLE} SET alipayid='{args.account}' WHERE ID='{g.user_id}'"
            res = MysqlWrite().write(sql)
            # 把支付宝添加进set
            rc = current_app.redis_cli
            rc.sadd('bind_aliplay', args.account)
            # 删除用户中心缓存
            rc.delete(f'user_center:{g.user_id}')
            # 删除任务列表缓存
            rc.delete('tasks_info')
            return {'data': '绑定成功!'}, HttpStatus.OK.value
        else:
            return {'error': '输入格式有误,请从新输入'}, HttpStatus.OK.value