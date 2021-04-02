import json
import random
import time

from flask_restplus import Resource, reqparse
from cache.old_tree import MemberRelationTreeCache
from cache.user import UserCache
from utils.hashids_iiuv import hashids_iivu_encode
from utils.constants import MEMBERS_TABLE, ET_MEMBER_EXTEND
from utils.mysql_cli import MysqlSearch,MysqlWrite
from utils.snowflake.id_worker import IdWorker
from utils.http_status import HttpStatus
from flask import current_app
from utils.short_link import get_short_link
from utils.hashids_iiuv import hashids_iivu_encode

# class OldMemberView(Resource):
#     def get(self):
#         k = 0
#         top_parents = MysqlSearch().get_more(f"SELECT phone,my_code, \
#                                                 sex,province,city,user_avatar,balance,name, \
#                                                 birth_year,id_card,status,alipayid,user_avatar\
#                                                     from old where parent_code IS NULL")
#         for i in top_parents:
#             if i['phone'] is None:
#                 mobile = '123' + '{:0>6d}'.format(random.randint(0, 9999999999))
#             else:
#                 mobile = i['phone']
#             iiuv = None
#             nickname = IdWorker(1, 2, 0).get_id()
#             # 生成用户表数据
#             my_code = i['my_code']
#             # 是否已实名
#             if i['id_card'] is not None:
#                 setreal = 2
#             else:
#                 setreal = 1
#             sql = f"INSERT INTO {MEMBERS_TABLE} (nickname,mobile,my_code,balance,alipayid,status,setreal,avatar) \
#                                 VALUE ('{nickname}','{mobile}','{my_code}','{i['balance']}','{i['alipayid']}','{i['status']}','{setreal}','{i['user_avatar']}')"
#             res = MysqlWrite().write(sql)
#             # 查询新用户id,生成iiuv邀请码
#             ii = MysqlSearch().get_one(f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile='{mobile}'")
#             member_iiuv = hashids_iivu_encode(ii['id'])
#             # 生成用户扩展表信息
#             sc = MysqlWrite().write(f"INSERT INTO {ET_MEMBER_EXTEND} (member_id,id_num,sex,name) VALUE ('{ii['id']}','{i['id_card']}','{i['birth_year']}','{i['name']}')")
#             # 生成iiuv入库
#             iiu = MysqlWrite().write(f"UPDATE {MEMBERS_TABLE} SET IIUV='{member_iiuv}' WHERE ID='{ii['id']}'")
#             if res == 1 and iiuv == None:
#                 user_info = UserCache(mobile).get()
#                 res = MemberRelationTreeCache().tree(mobile, iiuv)
#                 if res is False:
#                     k += 1
#                     print(k)
#                     continue
#                 k += 1
#                 print(k)
#             elif res == 1 and iiuv:
#                 MemberRelationTreeCache().tree(mobile, iiuv)
#                 k += 1
#                 time.sleep(1)
#                 print(k)

# class OldMemberView(Resource):
#     def get(self):
#         k = 0
#         top_parents = MysqlSearch().get_more(f"SELECT phone, my_code,parent_code,sex,user_avatar,name,birth_year,id_card,status,alipayid,balance \
#                                                             from old where parent_code IS NOT NULL")
#         for i in top_parents:
#             if i['phone'] is None:
#                 mobile = '123' + '{:0>6d}'.format(random.randint(0, 9999999999))
#             else:
#                 mobile = i['phone']
#             iiuv = i['parent_code']
#             nickname = IdWorker(1, 2, 0).get_id()
#             my_code = i['my_code']
#             parent_code = i['parent_code']
#             if len(i['id_card']) > 1 :
#                 setreal = 1
#             else:
#                 setreal = 2
#             sql = f"INSERT INTO {MEMBERS_TABLE} (nickname,mobile,my_code,balance,alipayid,status,setreal,avatar,parent_code) \
#                                             VALUE ('{nickname}','{mobile}','{my_code}','{i['balance']}','{i['alipayid']}','{i['status']}','{setreal}','{i['user_avatar']}','{i['parent_code']}')"
#             res = MysqlWrite().write(sql)
#             # 查询新用户id,生成iiuv邀请码
#             ii = MysqlSearch().get_one(f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile='{mobile}'")
#             member_iiuv = hashids_iivu_encode(ii['id'])
#             # 生成用户扩展表信息
#             sc = MysqlWrite().write(f"INSERT INTO {ET_MEMBER_EXTEND} (member_id,id_num,sex,name) VALUE ('{ii['id']}','{i['id_card']}','{i['birth_year']}','{i['name']}')")
#             # 生成iiuv入库
#             iiu = MysqlWrite().write(f"UPDATE {MEMBERS_TABLE} SET IIUV='{member_iiuv}' WHERE ID='{ii['id']}'")
#             if res == 1 and iiuv:
#                 res = MemberRelationTreeCache().tree(mobile, iiuv)
#                 if res is False:
#                     k += 1
#                     print(k)
#                     continue
#                 k += 1
#                 print(k)

# # # 第三次
# class OldMemberView(Resource):
#     def get(self):
#         k = 0
#         for i in range(0, current_app.redis_cli.llen('error_not_parent_id')):
#             data = current_app.redis_cli.lpop('error_not_parent_id')
#             json_data = json.loads(data)
#             # 通过redis pop出来的member_id 查找父亲id
#             fq = MysqlSearch().get_one(f"SELECT id FROM {MEMBERS_TABLE} WHERE my_code in \
#                                             (SELECT parent_code FROM {MEMBERS_TABLE} WHERE id='{json_data}')")
#             member_id = json_data
#             parent_id = fq['id']
#             res = MemberRelationTreeCache().tree(member_id, parent_id)
#             if res is False:
#                 k += 1
#                 print(k)
#                 continue
#             k += 1
#             print(k)

# 第四次
# class OldMemberView(Resource):
#     def get(self):
#         k = 0
#         for i in range(0, current_app.redis_cli.llen('error_not_top_parent_id_8')):
#             data = current_app.redis_cli.lpop('error_not_top_parent_id_8')
#             json_data = json.loads(data)
#             member_id = json_data['member_id']
#             parent_id = json_data['parent_id']
#             res = MemberRelationTreeCache().tree(member_id, parent_id)
#             if res is True:
#                 k += 1
#                 print(k)
#                 continue
#             k += 1
#             print(k)

# 老用户数据同步
class OldMemberView(Resource):
    def get(self):
        return 200
        # # 查询当前用户iiuv为空的用户并生成更新iiuv
        # # 查询新用户id,生成iiuv邀请码
        # ii = MysqlSearch().get_more(f"SELECT id FROM et_members WHERE avatar is not NULL")
        # for k in ii:
        #      # 随机头像生成
        #     ran_data = random.randint(1,12)
        #     txx = f"http://static.hfj447.com/avatars/{ran_data}.jpg"
        #     iiu = MysqlWrite().write(f"UPDATE et_members SET avatar='{txx}' WHERE id = {k['id']}")
        #     current_app.logger.error(iiu)
        # return {'msg': '修改完成'}, 200













