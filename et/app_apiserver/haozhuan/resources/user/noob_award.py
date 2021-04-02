import json
from flask_restplus import Resource
from utils.decorators import login_required
from utils.mysql_cli import MysqlWrite,MysqlSearch
from utils.constants import ET_TASK_ORDERS, ET_MEMBER_EARNINGS, MEMBERS_TABLE
from utils.http_status import HttpStatus
from flask import g, current_app
from common.cache.user import UserCache
import time
import datetime

class NoobAwardView(Resource):
    method_decorators = [
        login_required
    ]
    def get(self):
        # 查询当前用户是否已领取开屏红包
        w = MysqlSearch().get_one(f"SELECT task_id FROM {ET_MEMBER_EARNINGS} WHERE task_id=1 and member_id={g.user_id}")
        if w:
            return {'error_code': 4003, "msg": "当前用户已领取开屏红包"},200
        # 乐观锁解决修改用户余额
        l = MysqlSearch().get_one(f"SELECT balance,balance_version,mobile FROM {MEMBERS_TABLE} WHERE id='{g.user_id}'")
        version_time = time.time()
        try:
            u = MysqlWrite().write(
                f"UPDATE {MEMBERS_TABLE} SET balance=balance+100,balance_version='{version_time}' WHERE balance_version='{l['balance_version']}' and id='{g.user_id}'")
        except Exception:
            return {'error': '请稍后重试'}, HttpStatus.OK.value
        # 删除个人中心和用户信息缓存
        rc = current_app.redis_cli
        rc.delete(f"user_info_:{l['mobile']}")
        rc.delete(f"user_center:{g.user_id}")
        rc.delete(f"user_task_earnings_:{g.user_id}")
        UserCache(l["mobile"]).get()
        # 增加实名1元收益明细
        # 添加时间
        add_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        smsy = MysqlWrite().write(f"INSERT INTO {ET_MEMBER_EARNINGS} (member_id,task_id,add_time,amounts) VALUE ('{g.user_id}',1,'{add_time}',1)")
        return {"code": 2001}, 200
