from flask_restplus import Resource, Namespace, fields
from flask import current_app
from haozhuan.resources.user import user_api
from utils.http_status import HttpStatus
from cache.user_center import UserCentreCache
from utils.decorators import verify_required, login_required

# 用户个人中心
user_center = Namespace('user_center',description='获取用户所有任务列表 请求方式:直接带token请求')
user_api.add_namespace(user_center)

user_center_model = user_api.model('user_center_model', {
        '返回信息': fields.String(description='首页信息data'),
        '提示': fields.String(description='此接口必须携带token'),
})

@user_center.route('')
class UserCenterView(Resource):
    method_decorators = [
        login_required
    ]
    @user_center.expect(user_center_model)
    def get(self):
        """用户个人中心"""
        res = UserCentreCache().get()
        if res:
            return {'data': res}, HttpStatus.OK.value
        else:
            return {'error': '暂无记录'}, HttpStatus.OK.value
