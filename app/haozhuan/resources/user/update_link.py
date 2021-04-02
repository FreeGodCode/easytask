import time
from flask_restplus import Resource
from cache.user_center import UserCentreCache
from utils.decorators import verify_required, login_required
from utils.mysql_cli import MysqlSearch, MysqlWrite
from utils.constants import MEMBERS_TABLE,ET_GLOBAL_CONFIG,ET_MEMBER_EARNINGS
from flask import g, current_app
from utils.http_status import HttpStatus

class UpdateLinkView(Resource):
    method_decorators = [
        login_required
    ]
    def get(self):
        # 获取当前用户iiuv
        m = MysqlSearch().get_one(f"SELECT iiuv FROM {MEMBERS_TABLE} WHERE ID='{g.user_id}'")
        # 获取风险域名
        y = MysqlSearch().get_one(f"SELECT domains FROM {ET_GLOBAL_CONFIG}")
        if y['domains'] is not None:
            ym = y['domains'].split(',')[0]
            # 拼接url返回
            res = ym + "/" + m['iiuv']
            # 查询当前用户余额/点击更换链接的费用/乐观锁解决修改用户余额
            version_time = time.time()
            m = MysqlSearch().get_one(f"SELECT balance,balance_version FROM {MEMBERS_TABLE} WHERE id='{g.user_id}'")
            if m['balance'] < 10:
                return {'error': '无法切换,切换费用不足'}, HttpStatus.OK.value
            try:
                u = MysqlWrite().write(
                    f"UPDATE {MEMBERS_TABLE} SET balance=balance - 10,balance_version='{version_time}' WHERE balance_version='{m['balance_version']}' and id='{g.user_id}'")
            except Exception:
                return {'error': '请稍后重试'}, HttpStatus.OK.value
            if u == 1:
                # 更新出账表信息
                MysqlWrite().write(f"INSERT INTO {ET_MEMBER_EARNINGS} (out_amounts,member_id) VALUE ('{10}','{g.user_id}')")
                rc = current_app.redis_cli
                rc.delete('user_center:{}'.format(g.user_id))
                # 生成用户个人中心缓存信息
                UserCentreCache().get()
                return {'data': res}, HttpStatus.OK.value
            else:
                return {'error': '请稍后尝试'}, HttpStatus.OK.value