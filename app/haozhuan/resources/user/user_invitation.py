from flask_restplus import Resource, reqparse
from cache.relation_tree import MemberRelationTreeCache
from utils.invite_intercept import intercept
from utils.mysql_cli import MysqlSearch
from utils.constants import ET_MEMBER_RELATIONS, MEMBERS_TABLE
from flask import g, current_app
from utils.http_status import HttpStatus


class UserInvitationView(Resource):
    def post(self):
        """单独邀请接口"""
        parser = reqparse.RequestParser()
        parser.add_argument('iiuv', type=str, required=True, location='json')
        args = parser.parse_args()
        iiuv = args.iiuv
        if iiuv:
            # 查询当前iiuv是否正确
            ii = MysqlSearch().get_one(f"SELECT ID FROM {MEMBERS_TABLE} WHERE IIUV='{args.iiuv}'")
            if ii is False:
                return {'error': '无此用户,请重新输入'}, HttpStatus.OK.value
            # todo 判断当前用户是否顶级用户
            res = intercept()
            if res >= 1:
                return {'error': '此用户已到达邀请限制,无法进行邀请绑定'}
            # 查询当前用户是否有父级或者子级
            u = MysqlSearch().get_one(f"SELECT top_parent_id,parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id={g.user_id}")
            if u['parent_id'] != g.user_id:
                return {'error': '已绑定过邀请人,无法重复绑定'}, HttpStatus.OK.value
            # 否则正常绑定
            res = MemberRelationTreeCache().tree(g.mobile, iiuv)
            if res is True:
                # 删除缓存
                rc = current_app.redis_cli
                rc.delete(f'user_center:{g.user_id}')
                return {'data': '绑定成功'}, HttpStatus.OK.value
            else:
                return {'error': '绑定邀请网络繁忙,请稍后再试'}, HttpStatus.OK.value