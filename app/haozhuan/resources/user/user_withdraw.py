from flask_restplus import Resource, Namespace, fields
from cache.user_withdraw_recore import UserWithdrawRecodeCache
from haozhuan.resources.user import user_api
from utils.decorators import verify_required, login_required
from utils.http_status import HttpStatus

# 用户提现记录
user_withdraw = Namespace('user_withdraw_record',description='获取用户提现记录列表 请求方式:直接携带token请求')
user_api.add_namespace(user_withdraw)

user_withdraw_model = user_api.model('user_withdraw_model', {
        '返回信息': fields.String(description='提现流水[列表]'),
        '提示': fields.String(description='此接口必须携带token'),
})

@user_withdraw.route('')
class UserWithdrawRecordView(Resource):
    method_decorators = [
        login_required
    ]

    @user_withdraw.expect(user_withdraw_model)
    def get(self):
        """用户提现记录获取"""
        res = UserWithdrawRecodeCache().get()
        if res is False:
            return {'error': '用户没有提现信息'}, HttpStatus.OK.value
        else:
            return {'data': res}, HttpStatus.OK.value