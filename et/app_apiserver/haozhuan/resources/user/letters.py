from flask_restplus import Resource
from utils.mysql_cli import MysqlSearch
from utils.constants import ET_MEMBER_EARNINGS, MEMBERS_TABLE

class LettersView(Resource):
    """获取快报信息"""
    def get(self):
        # 获取当前快报信息
        k = MysqlSearch().get_more(f"SELECT amounts,add_time,etm.nickname from {ET_MEMBER_EARNINGS} as ete \
                        LEFT JOIN et_tasks as ett on ett.id = ete.task_id \
                            LEFT JOIN {MEMBERS_TABLE} as etm on etm.id = ete.member_id \
                                ORDER BY add_time DESC LIMIT 0,30")
        json_list = list()
        for i in k:
            dic = {
                "bonus": i["amounts"],
                "time": i["add_time"].strftime("%m-%d"),
                "user_name": i["nickname"][0:5]
            }
            json_list.append(dic)
        return {'code': 2001, "data": json_list}, 200