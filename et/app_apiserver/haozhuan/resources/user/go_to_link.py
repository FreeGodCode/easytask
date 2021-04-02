from flask_restplus import Resource, reqparse
from utils.mysql_cli import MysqlSearch
from utils.short_link import get_short_link
from flask import redirect, g, url_for,current_app
from utils.constants import MEMBERS_TABLE, ET_GLOBAL_CONFIG

class GoToLinkView(Resource):
    def get(self):
        # 查询iiuv邀请码
        parser_data = reqparse.RequestParser()
        parser_data.add_argument('iiuv', type=str, required=True)
        args = parser_data.parse_args()
        # 查询风险域名 http://share.hfj447.com/h5/index.html
        fx = MysqlSearch().get_one(f"SELECT domains FROM {ET_GLOBAL_CONFIG}")
        jump_link='/h5/index.html'
        ym = fx['domains'].split(',')[0]
        code = '?invite_code=+haozhuan+' + args.iiuv
        url = 'http://' + ym + jump_link + code
        return redirect(url, 302)
