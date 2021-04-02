from flask_restplus import Resource
from utils.constants import ET_GLOBAL_CONFIG
from utils.mysql_cli import MysqlSearch
from utils.http_status import HttpStatus

class AppConfigView(Resource):
    def get(self):
        config = MysqlSearch().get_more(f"SELECT banners,rules,helpers FROM {ET_GLOBAL_CONFIG}")
        if config:
            new_config = config[-1]
            config_data = dict()
            config_data['广告'] = new_config['banners']
            config_data['提现规则'] = new_config['rules']
            config_data['帮助中心'] = new_config['helpers']
            return {'data': config_data}, HttpStatus.OK.value

