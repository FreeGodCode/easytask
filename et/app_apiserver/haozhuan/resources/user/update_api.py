from flask_limiter.util import get_remote_address
from flask_restplus import Resource, reqparse
from utils import constants
from utils.http_status import HttpStatus
from utils.mysql_cli import MysqlWrite, MysqlSearch
from utils.constants import MEMBERS_TABLE,ET_APPS_PUB_HISTORY
from flask import g
from utils.limiter import limiter as lmt

class UpdateView(Resource):
    # 接口限流
    error_message = 'Too many requests.'

    decorators = [
        lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
                  key_func=get_remote_address,
                  error_message=error_message)
    ]

    def post(self):
        """更新版本"""
        parser = reqparse.RequestParser()
        parser.add_argument('app_version', type=str, required=True, location='json')
        args = parser.parse_args()
        up = MysqlWrite().write(f"UPDATE {MEMBERS_TABLE} SET app_version='{args.app_version}' WHERE ID='{g.user_id}'")
        return HttpStatus.OK.value

    def get(self):
        """返回当前app版本号"""
        parser = reqparse.RequestParser()
        parser.add_argument('app_version', type=str, location='args')
        args = parser.parse_args()
        if args.app_version:
            up = MysqlSearch().get_more(f"SELECT version,down_url,update_time,up_logs,update_status FROM {ET_APPS_PUB_HISTORY} WHERE osversion='{args.appversion}'")
            app_version = dict()
            if up[-1]:
                for i in up:
                    app_version['app版本号'] = i['version'],
                    app_version['app下载url'] = i['down_url'],
                    app_version['更新日期'] = i['update_time'].strftime("%Y-%m-%d-%H-%M-%S")
                    app_version['更新日志'] = i['up_logs']
                    app_version['更新状态'] = i['update_status']
            return {'data': app_version}, HttpStatus.OK.value
        else:
            ios = MysqlSearch().get_more(f"SELECT version,down_url,update_time,up_logs,update_status FROM {ET_APPS_PUB_HISTORY} WHERE osversion='ios'")
            android = MysqlSearch().get_more(f"SELECT version,down_url,update_time,up_logs,update_status FROM {ET_APPS_PUB_HISTORY} WHERE osversion='android'")
            app_version_ios = dict()
            app_version = dict()
            app_version_list = list()
            for i in ios:
                app_version_ios['app版本号'] = i['version'],
                app_version_ios['app下载url'] = i['down_url'],
                app_version_ios['更新日期'] = i['update_time'].strftime("%Y-%m-%d-%H-%M-%S")
                app_version_ios['更新日志'] = i['up_logs']
                app_version_ios['更新状态'] = i['update_status']
            app_version_list.append(app_version_ios)
            for k in android:
                app_version['app版本号'] = k['version'],
                app_version['app下载url'] = k['down_url'],
                app_version['更新日期'] = k['update_time'].strftime("%Y-%m-%d-%H-%M-%S")
                app_version['更新日志'] = k['up_logs']
                app_version['更新状态'] = k['update_status']
            json_data = {
                'ios': app_version_ios,
                'android': app_version
            }
            return {'data': json_data}, HttpStatus.OK.value