import datetime

from flask_restplus import Resource, reqparse, Namespace, fields
from flask import current_app, g
from haozhuan.resources.user import user_api
from haozhuan.resources.user.tasks import TasksDetailsView
from utils.http_status import HttpStatus
from utils.decorators import verify_required, login_required, withdrawal, bind_aliplay
from utils.mysql_cli import MysqlWrite
from utils.constants import ET_TASK_ORDERS,TASKS_TABLE
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
    def get(self):
        """用户接任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('task_id', type=int, required=True, location='args')
        args = parser.parse_args()
        task_status = current_app.redis_cli.sismember('cancel_tasks_:{}'.format(args.task_id),g.user_id)
        if task_status is True:
            return {'error': '此任务用户已取消过, 24小时内不能在领取'},HttpStatus.OK.value
        complete_task = current_app.redis_cli.sismember('complete_tasks_:{}'.format(args.task_id),g.user_id)
        if complete_task is True:
            return {'error': '此任务用户已领取'}, HttpStatus.OK.value
        else:
            now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            sql = f"INSERT INTO {ET_TASK_ORDERS} (task_id,member_id,status,add_time) VALUE ('{args.task_id}','{g.user_id}',1,'{now_time}')"
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
