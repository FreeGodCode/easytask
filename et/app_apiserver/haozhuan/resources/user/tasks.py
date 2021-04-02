import json
from flask_restplus import Resource, Namespace, fields, reqparse
from cache.tasks import TasksCache
from cache.tasks_high import TasksHighCache
from cache.tasks_detail import TasksDetail
from cache.user_tasks import UserTasks
from haozhuan.resources.user import user_api
from utils.decorators import login_required,verify_required
from flask import current_app, g
from utils.http_status import HttpStatus
from utils.constants import ET_TASK_ORDERS,ET_GLOBAL_CONFIG
from utils.mysql_cli import MysqlWrite,MysqlSearch

# 任务列表
tasks = Namespace('tasks',description='获取所有任务列表 请求方式:json')
user_api.add_namespace(tasks)

#任务详情
tasks_detail = Namespace('tasks_detail',description='获取任务详情 请求方式:关键字')
user_api.add_namespace(tasks_detail)

# 用户任务列表
user_tasks = Namespace('user_tasks',description='获取用户所有任务列表 请求方式:关键字')
user_api.add_namespace(user_tasks)

#任务列表
tasks_model = user_api.model('tasks_model', {
        'option': fields.String(required=True, description='high/general---->高级任务/简单任务'),
        'page_index':fields.Integer(required=True, description='分页页数'),
        'page_size':fields.Integer(required=True, description='页总数'),
        '返回信息': fields.String(description='任务data[列表]'),
        '提示': fields.String(description='此接口必须携带token'),
})

#任务详情
tasks_detail_model = user_api.model('tasks_detail_model', {
        'task_id': fields.Integer(required=True, description='需要获取详情的id'),
        '返回信息': fields.String(description='当前任务详情的数据'),
        '提示': fields.String(description='此接口必须携带token'),
})

#用户任务列表
user_tasks_detail_model = user_api.model('user_tasks_detail_model', {
        'kw': fields.Integer(required=True, description='underway/complete/unfinished--->进行中/已完成/未完成'),
        '返回信息': fields.String(description='当前用户任务详情的数据[列表]'),
        '提示': fields.String(description='此接口必须携带token'),
})


@tasks.route('')
class TasksView(Resource):
    @tasks.expect(tasks_model)
    def post(self):
        """获取任务列表"""
        parser = reqparse.RequestParser()
        parser.add_argument('kw',type=str,required=True,location='json')
        parser.add_argument('page_index',type=int,required=True,location='json')
        parser.add_argument('page_size',type=int,required=True,location='json')
        args = parser.parse_args()
        p_i, p_num = (args.page_index - 1), args.page_size
        if args.kw == 'high':
            # 检查当前用户是否高级用户
            tasks_data = TasksHighCache().get(p_i, p_num)
            user_info = 'user_info_:{}'.format(g.mobile)
            user_class_redis = current_app.redis_cli.hget(user_info, 0)
            if user_class_redis:
                user_class = json.loads(user_class_redis.decode())['m_class']
                if user_class != 2:
                    # TODO 查询当前用户任务数量 现在暂时查库,后期缓存
                    tasks = dict()
                    l = MysqlSearch().get_one(f"SELECT task_limit FROM {ET_GLOBAL_CONFIG}")
                    u = MysqlSearch().get_one(f"SELECT count(task_id) FROM {ET_TASK_ORDERS} WHERE member_id='{g.user_id}' AND status=4")
                    if u['count(task_id)']:
                        tasks['已做任务'] = int(u['count(task_id)'])
                    else:
                        tasks['已做任务'] = 0
                    tasks['升级需要'] = l['task_limit']
                    return {'error': tasks}, HttpStatus.OK.value
                else:
                    return {'data': tasks_data}, HttpStatus.OK.value
            else:
                return {'error':'no authority'}, HttpStatus.OK.value
        elif args.kw == "general":
            tasks_data = TasksCache().get(p_i, p_num)
            return {'data': tasks_data}, HttpStatus.OK.value
        else:
            return {'error': 'bad parameter'},HttpStatus.OK.value

@tasks_detail.route('')
class TasksDetailsView(Resource):
    @tasks_detail.expect(tasks_detail_model)
    def get(self):
        """获取任务详情"""
        parser = reqparse.RequestParser()
        parser.add_argument('tasks_id', type=int, required=True, location='args')
        args = parser.parse_args()
        tasks_id = args.tasks_id
        tasks_detail = TasksDetail(tasks_id).get()
        status = dict()
        # 审核状态标识
        s = MysqlSearch().get_one(f"SELECT status FROM {ET_TASK_ORDERS} WHERE task_id='{args.tasks_id}' and member_id='{g.user_id}'")
        if s is not False and s['status']:
            status['状态'] = s['status']
            return {'data':tasks_detail, 'status': status}, HttpStatus.OK.value
        status['状态'] = 0
        # todo 需要做一个用户单独任务状态缓存
        return {'data':tasks_detail, 'status': status}, HttpStatus.OK.value

@user_tasks.route('')
class UserTasksView(Resource):
    method_decorators = [
        login_required
    ]
    @user_tasks.expect(user_tasks_detail_model)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('kw', type=str, required=True,location='args')
        args = parser.parse_args()
        res = UserTasks(g.user_id).get()
        # 对列表里面的字典内容进行排序
        if res is not False:
            data_list = sorted(res, key=lambda e: e.__getitem__('用户提交时间'), reverse = True)
            status_1 = []
            status_2 = []
            status_3 = []
            for status in data_list:
                # 进行中
                if status['任务状态'] == 1 or status['任务状态'] == 2:
                    status_1.append({
                        '任务id':status['任务id'],
                        '用户id':status['用户id'],
                        '任务名称':status['任务名称'],
                        '任务奖励':status['任务奖励'],
                        '任务头像':status['任务头像'],
                        '任务截止时间':status['任务截止时间'],
                        '用户提交时间':status['用户提交时间'],
                        '任务状态':status['任务状态'],
                        '审核提示':status['审核提示']
                    })
                # 什么驳回 -----> 未完成
                elif status['任务状态'] == 5 :
                    status_2.append({
                        '任务id': status['任务id'],
                        '用户id': status['用户id'],
                        '任务名称': status['任务名称'],
                        '任务奖励': status['任务奖励'],
                        '任务头像': status['任务头像'],
                        '任务截止时间': status['任务截止时间'],
                        '用户提交时间': status['用户提交时间'],
                        '任务状态': status['任务状态'],
                        '审核提示': status['审核提示']
                    })
                elif status['任务状态'] == 4:
                    # 已完成
                    status_3.append({
                        '任务id': status['任务id'],
                        '用户id': status['用户id'],
                        '任务名称': status['任务名称'],
                        '任务奖励': status['任务奖励'],
                        '任务头像': status['任务头像'],
                        '任务截止时间': status['任务截止时间'],
                        '用户提交时间': status['用户提交时间'],
                        '任务状态': status['任务状态'],
                        '审核提示': status['审核提示']
                    })
            if args.kw == 'unfinished':
                return {'data': status_2}, HttpStatus.OK.value
            elif args.kw == 'underway':
                return {'data': status_1}, HttpStatus.OK.value
            elif args.kw == 'complete':
                return {'data': status_3}, HttpStatus.OK.value
        else:
            return {'error':'当前用户没有任何任务'}, HttpStatus.OK.value

class CancelTaskView(Resource):
    """取消任务"""
    method_decorators = [
        login_required
    ]
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('task_id', type=int, required=True, location='args')
        args = parser.parse_args()
        q = MysqlWrite().write(f"UPDATE {ET_TASK_ORDERS} SET status=3 WHERE task_id='{args.task_id}' and member_id='{g.user_id}'")
        if q == 1:
            rc = current_app.redis_cli
            rc.sadd('cancel_tasks_:{}'.format(args.task_id), g.user_id)
            rc.delete('user_tasks_:{}'.format(g.user_id))
            return {'data': '取消完成.'}, HttpStatus.OK.value






