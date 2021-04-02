import datetime
import json

from flask_restplus import Resource, reqparse, Namespace, fields
from flask import current_app, g

from haozhuan.config import global_config
from haozhuan.resources.user import user_api
from haozhuan.resources.user.tasks import TasksDetailsView
from utils.http_status import HttpStatus
from utils.decorators import verify_required, login_required, withdrawal, bind_aliplay
from utils.mysql_cli import MysqlWrite, MysqlSearch
from utils.constants import ET_TASK_ORDERS, TASKS_TABLE, ET_MEMBER_WITHDRAWAL
from utils.limiter import limiter as lmt
from utils import constants
from flask_limiter.util import get_remote_address

# 用户领取任务
user_draw_tasks = Namespace('user_draw_task',description='获取用户所有任务列表 请求方式:关键字')
user_api.add_namespace(user_draw_tasks)

draw_tasks_model = user_api.model('draw_tasks_model', {
        'task_id': fields.String(required=True, description='携带任务id'),
        '返回信息': fields.String(description='添加任务的状态回调'),
        '提示': fields.String(description='此接口必须携带token'),
})

@user_draw_tasks.route('')
class UserDrawTaskView(Resource):
    method_decorators = [
        verify_required, login_required
        # , withdrawal
    ]

    error_message = 'Too many requests.'

    decorators = [
        lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
                  key_func=get_remote_address,
                  error_message=error_message)
    ]

    @user_draw_tasks.expect(draw_tasks_model)
    def post(self):
        """用户接任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('task_id', type=int, required=True, location='json')
        parser.add_argument('app_safe_info', type=dict, required=True, location='json')
        args = parser.parse_args()
        # 要json数据入库,接收的类型必须是dict然后转str,不然会一直报错.可能需要flask的json,
        new_data = json.dumps(args.app_safe_info).replace("'", '"')
        # 判断此任务是否还有剩余数量
        # 判断用户是否已经提现成功
        tx = MysqlSearch().get_one(f"SELECT verify FROM {ET_MEMBER_WITHDRAWAL} WHERE member_id='{g.user_id}' and verify=2")
        current_app.logger.error(tx)
        if tx is None:
            return {"error": "请进行新手提现成功再领取任务"}
        sy = MysqlSearch().get_one(f"SELECT tasks_counts,count_tasks,check_router FROM {TASKS_TABLE} WHERE id='{args.task_id}'")
        if sy['tasks_counts'] == sy['count_tasks']:
            return {'error_code': 4003, 'msg': '此任务无法领取.数量不足'}
        task_status = current_app.redis_cli.sismember('cancel_tasks_{}'.format(g.user_id), args.task_id)
        if task_status is True:
            return {'error': '此任务用户已取消过, 24小时内不能在领取'},HttpStatus.OK.value
        complete_task = current_app.redis_cli.sismember('complete_tasks_{}'.format(g.user_id), args.task_id)
        if complete_task is True:
            return {'error': '此任务用户已领取'}, HttpStatus.OK.value
        else:
            now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            # todo  'http://' + '47.113.91.65:5007' 添加到config配置项
            current_app.logger.error(sy['check_router'])
            safe_token = global_config.getRaw('Invite_link', 'EWM_LINK') + f'?td={args.task_id}&fromu={g.user_id}&ref={sy["check_router"]}'
            current_app.logger.error(safe_token)
            sql = f"INSERT INTO {ET_TASK_ORDERS} (task_id,member_id,status,add_time,app_safe_info,safe_token) VALUE ('{args.task_id}','{g.user_id}',1,'{now_time}','{new_data}','{safe_token}')"
            res = MysqlWrite().write(sql)
            if res == 1:
                # 更新任务剩余数量
                r = MysqlWrite().write(f"UPDATE {TASKS_TABLE} SET count_tasks=count_tasks + 1 WHERE ID='{args.task_id}'")
                # redis操作
                rc = current_app.redis_cli
                # 删除用户任务缓存
                rc.delete('user_tasks_:{}'.format(g.user_id))
                # 删除任务缓存
                rc.delete('tasks_info')
                # 删除用户任务的缓存
                rc.delete('user_tasks_:{}'.format(g.user_id))
                rc.sadd('complete_tasks_:{}'.format(args.task_id),g.user_id)
                # 向已领取任务redis中添加数据
                rc.sadd('fetch_tasks_:{}'.format(args.task_id), g.user_id)
                # 删除任务详情缓存
                rc.delete("tasks_detail_:{}".format(args.task_id))
                # 删除用户任务总列表数据
                rc.delete(f"tasks_info_{g.user_id}")
                return {'data': '添加任务完成'}, HttpStatus.OK.value
            else:
                return {'error': '任务获取失败,请重试'}, HttpStatus.OK.value
