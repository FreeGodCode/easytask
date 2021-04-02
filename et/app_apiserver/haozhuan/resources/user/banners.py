from flask_restplus import Resource,reqparse
from utils.mysql_cli import MysqlSearch
from utils.http_status import HttpStatus

class BannerView(Resource):
    """
    获取banner
    :return: json
    """
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=int, required=True, location='args')
        args = parser.parse_args()

        b_sql = f"SELECT banner_url, banner_name, banner_jumplink, show_time, sorting, end_time, banner_type FROM et_banner WHERE banner_type = {args.type} AND status = 2"
        b_ex = MysqlSearch().get_more(b_sql)
        b_list = list()

        if b_ex:
            for i in b_ex:
                b_list.append({
                    'name': i['banner_name'],
                    'url': i['banner_url'],
                    'j_link': i['banner_jumplink'],
                    's_time': i['show_time'],
                    'sort': i['sorting'],
                    'e_time': i['end_time'],
                    'b_type': i['banner_type']
                    })
            return {'data':b_list}, HttpStatus.OK.value
        else:
            return {'error_code': 4007, 'msg': '暂无数据'}, HttpStatus.OK.value



