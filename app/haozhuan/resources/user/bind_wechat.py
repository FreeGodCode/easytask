from flask_restplus import Resource, reqparse

from utils.constants import MEMBERS_TABLE
from utils.http_status import HttpStatus
from utils.mysql_cli import MysqlWrite, MysqlSearch


class BindWechatView(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('iiuv', type=str, required=True, location='json')
        parser.add_argument('open_id', type=int, required=True, location='json')
        args = parser.parse_args()
        member_id = MysqlSearch().get_one(f"SELECT id, nickname FROM {MEMBERS_TABLE} WHERE IIUV='{args.iiuv}'")
        res = MysqlWrite().write(f"UPDATE {MEMBERS_TABLE} SET open_id={args.open_id} WHERE ID={member_id['id']}")
        if res == 1:
            return {'data': member_id['nickname']}, HttpStatus.OK.value
