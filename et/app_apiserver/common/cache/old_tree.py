import json
from anytree.importer import DictImporter
from flask import current_app
from redis import RedisError
from anytree import Node, findall_by_attr
from anytree.exporter import DictExporter
from utils.constants import ET_MEMBER_RELATIONS,MEMBERS_TABLE
from utils.mysql_cli import MysqlWrite, MysqlSearch

# class MemberRelationTreeCache(object):
#     def tree(self, mobile, iiuv):
#         rc = current_app.redis_cli
#         # 获取新用户的id
#         member_id = f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile='{mobile}'"
#         member = MysqlSearch().get_one(member_id)
#         # 获取父级用户id
#         parent_id = f"SELECT id FROM {MEMBERS_TABLE} WHERE my_code='{iiuv}'"
#         parent = MysqlSearch().get_one(parent_id)
#         if iiuv is None:
#             # 设置当前用户为顶级节点
#             parent_id = Node(member['id'])
#             child_id = Node(None)
#             exporter = DictExporter()
#             data = exporter.export(parent_id)
#             rc.hsetnx(f"drp_relation_member_{member['id']}", 0, json.dumps(data))
#             # todo 查询当前用户关系是否入库
#             fx = MysqlSearch().get_one(f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
#             if not fx:
#                 # 新增当前用户分销关系
#                 sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id,levels) VALUE ('{member['id']}','{member['id']}' ,1)"
#                 MysqlWrite().write(sql_iiuv)
#             return True
#         # TODO 查询当前用户的parent_id是否顶级节点
#         try:
#             root_data = rc.hget(f"drp_relation_member_{parent['id']}", 0)
#         except Exception as e:
#             rc.lpush('error_not_parent_id', member['id'])
#             return False
#         if root_data:
#             try:
#                 json_data = json.loads(root_data)
#                 importer = DictImporter()
#                 root = importer.import_(json_data)
#                 level_2 = Node(member['id'], parent=root)
#                 exporter = DictExporter()
#                 data = exporter.export(root)
#                 rc.hset(f"drp_relation_member_{parent['id']}", 0, json.dumps(data))
#                 # todo 查询当前用户关系是否入库
#                 fx = MysqlSearch().get_one(
#                     f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
#                 if not fx:
#                     # 新增当前用户分销关系
#                     sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
#                     MysqlWrite().write(sql_iiuv)
#                 # 更新数据库levels字段数据
#                 sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels=2,parent_id='{parent['id']}',top_parent_id='{parent['id']}' WHERE member_id='{member['id']}'"
#                 MysqlWrite().write(sql)
#                 # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
#                 gl = MysqlSearch().get_one(
#                     f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
#                 if gl['parent_id'] != member['id']:
#                     # 删除树
#                     rc.delete(f"drp_relation_member_{member['id']}")
#                 # 删除缓存
#                 rc.delete(f"user_apprentice_:{member['id']}")
#                 rc.delete(f"user_apprentice_:{parent['id']}")
#                 return True
#             except Exception as e:
#                 current_app.logger.error(e)
#                 return False
#         else:
#             # TODO 如果当前parent_id不是顶级节点,查询当前parent_id的上级并进入树结构查询
#             top_parent = MysqlSearch().get_one(f"SELECT top_parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{parent['id']}'")
#             try:
#                 root_data = rc.hget(f"drp_relation_member_{top_parent['top_parent_id']}", 0)
#             except Exception as e:
#                 json_data = {
#                     'member_id': member['id'],
#                     'parent_id': parent['id']
#                 }
#                 rc.lpush('error_not_top_parent_id', json.dumps(json_data))
#             if root_data:
#                 json_data = json.loads(root_data)
#                 importer = DictImporter()
#                 root = importer.import_(json_data)
#                 level_1 = findall_by_attr(root, top_parent['top_parent_id'])[0]
#                 level_2 = findall_by_attr(root, parent['id'])[0]
#                 level_3 = Node(member['id'],parent=level_2)
#                 exporter = DictExporter()
#                 data = exporter.export(root)
#                 rc.hset(f"drp_relation_member_{top_parent['top_parent_id']}", 0, json.dumps(data))
#                 # 查询当前parent的等级
#                 lv = MysqlSearch().get_one(f"SELECT levels FROM {ET_MEMBER_RELATIONS} WHERE member_id='{parent['id']}'")
#                 # todo 查询当前用户关系是否入库
#                 fx = MysqlSearch().get_one(
#                     f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
#                 if not fx:
#                     # 新增当前用户分销关系
#                     sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
#                     MysqlWrite().write(sql_iiuv)
#                 # 更新数据库levels字段数据
#                 sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels='{lv['levels'] + 1}',parent_id='{parent['id']}',top_parent_id='{top_parent['top_parent_id']}' WHERE member_id='{member['id']}'"
#                 MysqlWrite().write(sql)
#                 # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
#                 gl = MysqlSearch().get_one(
#                     f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
#                 if gl['parent_id'] != member['id']:
#                     # 删除树
#                     rc.delete(f"drp_relation_member_{member['id']}")
#                 # 删除缓存
#                 rc.delete(f"user_apprentice_:{member['id']}")
#                 rc.delete(f"user_apprentice_:{parent['id']}")
#                 return True


class MemberRelationTreeCache(object):
    def tree(self, mobile, iiuv):
        rc = current_app.redis_cli
        # 获取新用户的id
        member_id = f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile='{mobile}'"
        member = MysqlSearch().get_one(member_id)
        # 获取父级用户id
        parent_id = f"SELECT id FROM {MEMBERS_TABLE} WHERE my_code='{iiuv}'"
        parent = MysqlSearch().get_one(parent_id)
        if iiuv is None:
            # 设置当前用户为顶级节点
            parent_id = Node(member['id'])
            child_id = Node(None)
            exporter = DictExporter()
            data = exporter.export(parent_id)
            rc.hsetnx(f"drp_relation_member_{member['id']}", 0, json.dumps(data))
            # todo 查询当前用户关系是否入库
            fx = MysqlSearch().get_one(f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
            if not fx:
                # 新增当前用户分销关系
                sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id,levels) VALUE ('{member['id']}','{member['id']}' ,1)"
                MysqlWrite().write(sql_iiuv)
            return True
        # TODO 查询当前用户的parent_id是否顶级节点
        try:
            root_data = rc.hget(f"drp_relation_member_{parent['id']}", 0)
        except Exception as e:
            rc.lpush('error_not_parent_id', member['id'])
            return False
        if root_data:
            try:
                json_data = json.loads(root_data)
                importer = DictImporter()
                root = importer.import_(json_data)
                level_2 = Node(member['id'], parent=root)
                exporter = DictExporter()
                data = exporter.export(root)
                rc.hset(f"drp_relation_member_{parent['id']}", 0, json.dumps(data))
                # todo 查询当前用户关系是否入库
                fx = MysqlSearch().get_one(
                    f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                if not fx:
                    # 新增当前用户分销关系
                    sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
                    MysqlWrite().write(sql_iiuv)
                # 更新数据库levels字段数据
                sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels=2,parent_id='{parent['id']}',top_parent_id='{parent['id']}' WHERE member_id='{member['id']}'"
                MysqlWrite().write(sql)
                # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
                gl = MysqlSearch().get_one(
                    f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                if gl['parent_id'] != member['id']:
                    # 删除树
                    rc.delete(f"drp_relation_member_{member['id']}")
                # 删除缓存
                rc.delete(f"user_apprentice_:{member['id']}")
                rc.delete(f"user_apprentice_:{parent['id']}")
                return True
            except Exception as e:
                current_app.logger.error(e)
                return False
        else:
            # TODO 如果当前parent_id不是顶级节点,查询当前parent_id的上级并进入树结构查询
            top_parent = MysqlSearch().get_one(f"SELECT top_parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{parent['id']}'")
            try:
                root_data = rc.hget(f"drp_relation_member_{top_parent['top_parent_id']}", 0)
            except Exception as e:
                json_data = {
                    'member_id': member['id'],
                    'parent_id': parent['id']
                }
                rc.lpush('error_not_top_parent_id', json.dumps(json_data))
            if root_data:
                json_data = json.loads(root_data)
                importer = DictImporter()
                root = importer.import_(json_data)
                level_1 = findall_by_attr(root, top_parent['top_parent_id'])[0]
                level_2 = findall_by_attr(root, parent['id'])[0]
                level_3 = Node(member['id'],parent=level_2)
                exporter = DictExporter()
                data = exporter.export(root)
                rc.hset(f"drp_relation_member_{top_parent['top_parent_id']}", 0, json.dumps(data))
                # 查询当前parent的等级
                lv = MysqlSearch().get_one(f"SELECT levels FROM {ET_MEMBER_RELATIONS} WHERE member_id='{parent['id']}'")
                # todo 查询当前用户关系是否入库
                fx = MysqlSearch().get_one(
                    f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                if not fx:
                    # 新增当前用户分销关系
                    sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
                    MysqlWrite().write(sql_iiuv)
                # 更新数据库levels字段数据
                sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels='{lv['levels'] + 1}',parent_id='{parent['id']}',top_parent_id='{top_parent['top_parent_id']}' WHERE member_id='{member['id']}'"
                MysqlWrite().write(sql)
                # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
                gl = MysqlSearch().get_one(
                    f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                if gl['parent_id'] != member['id']:
                    # 删除树
                    rc.delete(f"drp_relation_member_{member['id']}")
                # 删除缓存
                rc.delete(f"user_apprentice_:{member['id']}")
                rc.delete(f"user_apprentice_:{parent['id']}")
                return True



# todo 除了第一第二步这里全跑
# class MemberRelationTreeCache(object):
#     def tree(self, member_id, parent_id):
#         rc = current_app.redis_cli
#         # 获取新用户的id
#         # TODO 查询当前用户的parent_id是否顶级节点
#         try:
#             root_data = rc.hget(f"drp_relation_member_{parent_id}", 0)
#         except Exception as e:
#             rc.lpush('error_not_parent_id_2', member_id)
#             return False
#         if root_data:
#             try:
#                 json_data = json.loads(root_data)
#                 importer = DictImporter()
#                 root = importer.import_(json_data)
#                 level_2 = Node(member_id, parent=root)
#                 exporter = DictExporter()
#                 data = exporter.export(root)
#                 rc.hset(f"drp_relation_member_{parent_id}", 0, json.dumps(data))
#                 # todo 查询当前用户关系是否入库
#                 fx = MysqlSearch().get_one(
#                     f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member_id}'")
#                 if not fx:
#                     # 新增当前用户分销关系
#                     sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member_id}','{parent_id}')"
#                     MysqlWrite().write(sql_iiuv)
#                 # 更新数据库levels字段数据
#                 sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels=2,parent_id='{parent_id}',top_parent_id='{parent_id}' WHERE member_id='{member_id}'"
#                 MysqlWrite().write(sql)
#                 # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
#                 gl = MysqlSearch().get_one(
#                     f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member_id}'")
#                 if gl['parent_id'] != member_id:
#                     # 删除树
#                     rc.delete(f"drp_relation_member_{member_id}")
#                 # 删除缓存
#                 rc.delete(f"user_apprentice_:{member_id}")
#                 rc.delete(f"user_apprentice_:{parent_id}")
#                 return True
#             except Exception as e:
#                 current_app.logger.error(e)
#                 return False
#         else:
#             # TODO 如果当前parent_id不是顶级节点,查询当前parent_id的上级并进入树结构查询
#             top_parent = MysqlSearch().get_one(f"SELECT top_parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{parent_id}'")
#             try:
#                 root_data = rc.hget(f"drp_relation_member_{top_parent['top_parent_id']}", 0)
#             except Exception as e:
#                 json_data = {
#                     'member_id': member_id,
#                     'parent_id': parent_id
#                 }
#                 rc.lpush('error_not_top_parent_id_33', json.dumps(json_data))
#                 return False
#             if root_data:
#                 json_data = json.loads(root_data)
#                 importer = DictImporter()
#                 root = importer.import_(json_data)
#                 level_1 = findall_by_attr(root, top_parent['top_parent_id'])[0]
#                 level_2 = findall_by_attr(root, parent_id)[0]
#                 level_3 = Node(member_id,parent=level_2)
#                 exporter = DictExporter()
#                 data = exporter.export(root)
#                 rc.hset(f"drp_relation_member_{top_parent['top_parent_id']}", 0, json.dumps(data))
#                 # 查询当前parent的等级
#                 lv = MysqlSearch().get_one(f"SELECT levels FROM {ET_MEMBER_RELATIONS} WHERE member_id='{parent_id}'")
#                 # todo 查询当前用户关系是否入库
#                 fx = MysqlSearch().get_one(
#                     f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member_id}'")
#                 if not fx:
#                     # 新增当前用户分销关系
#                     sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member_id}','{parent_id}')"
#                     MysqlWrite().write(sql_iiuv)
#                 # 更新数据库levels字段数据
#                 sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels='{lv['levels'] + 1}',parent_id='{parent_id}',top_parent_id='{top_parent['top_parent_id']}' WHERE member_id='{member_id}'"
#                 MysqlWrite().write(sql)
#                 # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
#                 gl = MysqlSearch().get_one(
#                     f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member_id}'")
#                 if gl['parent_id'] != member_id:
#                     # 删除树
#                     rc.delete(f"drp_relation_member_{member_id}")
#                 # 删除缓存
#                 rc.delete(f"user_apprentice_:{member_id}")
#                 rc.delete(f"user_apprentice_:{parent_id}")
#                 return True

# class MemberRelationTreeCache(object):
#     def tree(self, member, iiuv):
#         rc = current_app.redis_cli
#         if iiuv is None:
#             # 设置当前用户为顶级节点
#             parent_id = Node(iiuv)
#             child_id = Node(member, parent=parent_id)
#             exporter = DictExporter()
#             data = exporter.export(parent_id)
#             rc.hsetnx(f"drp_relation_member_{iiuv}", 0, json.dumps(data))
#             # todo 查询当前用户关系是否入库
#             fx = MysqlSearch().get_one(f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member}'")
#             if not fx:
#                 # 新增当前用户分销关系
#                 sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id,levels) VALUE ('{member}','{parent_id}' ,1)"
#                 MysqlWrite().write(sql_iiuv)
#             return True