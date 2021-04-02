import json
from flask_restplus import Resource, reqparse, Namespace, fields
from haozhuan.resources.user import user_api
from utils.mysql_cli import MysqlWrite,MysqlSearch
from utils.decorators import verify_required, login_required
from utils.constants import ET_TASK_ORDERS,TASKS_TABLE
from utils.http_status import HttpStatus
from flask import g,current_app
import datetime
import re

add_tasks = Namespace('user_add_task',description='用户提交任务 请求方式:json')
user_api.add_namespace(add_tasks)

tasks_add = user_api.model('tasks_add', {
        'task_id': fields.String(required=True, description='要提交任务的id'),
        'json_data':fields.Integer(required=True, description='用户任务凭证---->json数据'),
        '返回信息': fields.String(description='任务提交回调'),
        '提示': fields.String(description='此接口必须携带token'),
})

@add_tasks.route('')
class UserAddTaskView(Resource):
    method_decorators = [
        verify_required, login_required
    ]
    @add_tasks.expect(tasks_add)
    def post(self):
        """用户提交任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('task_id', type=int, required=True, location='json')
        parser.add_argument('json_data', type=dict, required=True, location='json')
        args = parser.parse_args()
        if args.json_data:
            if args.json_data['imgs'] == []:
                return {'code': 4002, 'msg': '请上传图片'}
        # todo 4月1号晚上修改格式
        # 要json数据入库,接收的类型必须是dict然后转str,不然会一直报错.可能需要flask的json,
        new_data = json.dumps(args.json_data).replace("'", '"')
        #     new_data = json.dumps(data)
        # 是否接过此任务
        t = MysqlSearch().get_more(f"SELECT task_id FROM {ET_TASK_ORDERS} WHERE member_id='{g.user_id}'")
        if {'task_id': args.task_id} not in t:
            return {'error': '请先领取改任务'}, HttpStatus.OK.value
        # 查询当前接任务的时间
        r = MysqlSearch().get_one(f"SELECT add_time FROM {ET_TASK_ORDERS} WHERE task_id='{args.task_id}'")
        # 获取任务最后结束时间, 查询当前任务deadline_time
        task_end_time = MysqlSearch().get_one(f"SELECT end_time,deadline_time FROM {TASKS_TABLE} WHERE id='{args.task_id}'")
        end_time = task_end_time['end_time'].strftime("%Y-%m-%d-%H-%M-%S")
        now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        # 通过接任务的时间+任务deadline时间l
        # a = (r['add_time'] + datetime.timedelta(hours=int(task_end_time['deadline_time']))).strftime("%Y-%m-%d-%H-%S-%M")
        # todo >
        if now_time > (r['add_time'] + datetime.timedelta(hours=int(task_end_time['deadline_time']))).strftime("%Y-%m-%d-%H-%S-%M"):
            return {'error': '该任务已超过做单时间,无法提交'}, HttpStatus.OK.value
        # todo <
        if end_time < now_time:
            return {'error': '该任务已超过结束时间,无法提交'}, HttpStatus.OK.value
        else:
            # 更新order表数据
            sql = f"UPDATE {ET_TASK_ORDERS} SET status=2,user_submit='{new_data}',submit_time='{now_time}' WHERE member_id={g.user_id} AND task_id='{args.task_id}'"
            res = MysqlWrite().write(sql)
            if res == 1:
                # 更新任务数量
                # 删除用户任务详情缓存
                rc = current_app.redis_cli
                rc.delete('user_tasks_:{}'.format(g.user_id))
                return {'data': '提交成功'}, HttpStatus.OK.value
            else:
                return {"error": '提交失败,尝试再次提交'}, HttpStatus.OK.value





