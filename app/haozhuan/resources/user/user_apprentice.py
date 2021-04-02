from flask_restplus import Resource, reqparse, Namespace, fields
from cache.user_apprentice_cache import UserApprenticeCache
from cache.user_apprenticedetail_cache import UserApprenticeDetailCache
from haozhuan.resources.user import user_api
from utils.decorators import verify_required, login_required
from utils.http_status import HttpStatus

user_apprentice_page = Namespace('user_apprentice',description='用户收徒页信息 请求方式:直接携带token过来请求就行')
user_api.add_namespace(user_apprentice_page)
user_apprentice_detail = Namespace('user_apprentice_detail',description='用户收徒收益明细 请求方式:关键字')
user_api.add_namespace(user_apprentice_detail)

user_apprentice_page_model = user_api.model('user_apprentice_page', {
        '提示': fields.String(description='此接口必须携带token'),
        '返回信息': fields.String(description='收徒页面内容'),
})

user_apprentice_detail_model = user_api.model('user_apprentice_model', {
        'page_index': fields.Integer(description='页数'),
        'page_size': fields.Integer(description='内容总数'),
        '提示': fields.String(description='此接口必须携带token'),
        '返回信息': fields.String(description='收徒详情[列表]'),
})


@user_apprentice_page.route('')
class UserApprenticeView(Resource):
    method_decorators = [
        login_required
    ]
    @user_apprentice_page.expect(user_apprentice_page_model)
    def get(self):
        """用户收徒页面"""
        res = UserApprenticeCache().get()
        if res:
            return {'data': res}, HttpStatus.OK.value
        else:
            return {'请求错误,请重试'}, HttpStatus.OK.value

@user_apprentice_detail.route('')
class UserApprenticeDetailView(Resource):
    method_decorators = [
        login_required
    ]
    @user_apprentice_detail.expect(user_apprentice_detail_model)
    def get(self):
        """用户收徒明细"""
        parser = reqparse.RequestParser()
        parser.add_argument('page_index', type=int, required=True, location='args')
        parser.add_argument('page_size', type=str, required=True, location='args')
        args = parser.parse_args()
        p_i, p_num = (args.page_index - 1), args.page_size
        res = UserApprenticeDetailCache().get(p_i, p_num)
        if res:
            return {'data': res}, HttpStatus.OK.value
        else:
            return {'error': None}, HttpStatus.OK.value