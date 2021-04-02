from flask_restplus import Resource, fields, Namespace
from cache.user_earnings import UserEarningsCache
from haozhuan.resources.user import user_api
from utils.decorators import verify_required, login_required
from utils.http_status import HttpStatus


# 用户个人收益
user_earnings = Namespace('user_earnings',description='获取用户个人收益列表 请求方式:直接携带token请求')
user_api.add_namespace(user_earnings)

user_earnings_model = user_api.model('user_earnings_model', {
        '返回信息': fields.String(description='收益流水[列表]'),
        '提示': fields.String(description='此接口必须携带token'),
})

@user_earnings.route('')
class UserEarningsView(Resource):
    method_decorators = [
        login_required
    ]
    @user_earnings.expect(user_earnings_model)
    def get(self):
        """用户个人收益获取"""
        res = UserEarningsCache().get()
        if res:
            return {'data': res[0:4]}, HttpStatus.OK.value
        else:
            return {'error''次用户没有流水记录'}, HttpStatus.OK.value
