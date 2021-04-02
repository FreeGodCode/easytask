from flask_restplus import Resource
from cache.usertaskearningscache import UserTaskEarningsCache
from utils.http_status import HttpStatus

class UserTaskEarnings(Resource):
    def get(self):
        """用户任务个人收益"""
        res = UserTaskEarningsCache().get()
        if res is False:
            return {'error': '用户没有个人收益'}, HttpStatus.OK.value
        else:
            return {'data': res}, HttpStatus.OK.value