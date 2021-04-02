import json

from anytree import Node, findall_by_attr
from anytree.exporter import DictExporter
from anytree.importer import DictImporter
from flask import current_app

from utils.constants import ET_MEMBER_RELATIONS, MEMBERS_TABLE
from utils.mysql_cli import MysqlWrite, MysqlSearch


class MemberRelationTreeCache(object):
    def tree(self, mobile, iiuv):
        # 获取新用户的id
        member_id = f"SELECT id FROM {MEMBERS_TABLE} WHERE mobile='{mobile}'"
        member = MysqlSearch().get_one(member_id)
        # 获取父级用户id
        parent_id = f"SELECT id FROM {MEMBERS_TABLE} WHERE IIUV='{iiuv}'"
        parent = MysqlSearch().get_one(parent_id)
        if iiuv is None:
            # 设置当前用户为顶级节点
            parent_id = Node(member['id'])
            child_id = Node(None)
            exporter = DictExporter()
            data = exporter.export(parent_id)
            current_app.redis_cli.hsetnx('drp_relation_member_{}'.format(member['id']), 0, json.dumps(data))
            # todo 查询当前用户关系是否入库
            fx = MysqlSearch().get_one(f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
            if not fx:
                # 新增当前用户分销关系
                sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id,levels) VALUE ('{member['id']}','{member['id']}' ,1)"
                MysqlWrite().write(sql_iiuv)
            return True
        # 查询当前用户的顶级节点
        sql_top = f"SELECT top_parent_id,parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id={parent['id']}"
        top_parent = MysqlSearch().get_more(sql_top)[-1]
        if top_parent and top_parent['top_parent_id'] != None:
            parent_data = json.loads(
                current_app.redis_cli.hget('drp_relation_member_{}'.format(top_parent['top_parent_id']), 0).decode())
            importer = DictImporter()
            root = importer.import_(parent_data)
            lever_2 = findall_by_attr(root, top_parent['parent_id'])[0]
            lever_3 = findall_by_attr(root, parent['id'])[0]
            lever_4 = Node(member['id'], parent=lever_3)
            exporter = DictExporter()
            data = exporter.export(root)
            current_app.redis_cli.hset('drp_relation_member_{}'.format(top_parent['top_parent_id']), 0,
                                       json.dumps(data))
            # todo 查询当前用户关系是否入库
            fx = MysqlSearch().get_one(f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
            if not fx:
                # 新增当前用户分销关系
                sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
                MysqlWrite().write(sql_iiuv)
            # 更新数据库levels字段数据
            sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels=4,parent_id='{parent['id']}' WHERE member_id='{member['id']}'"
            MysqlWrite().write(sql)
            # 插入当前三级用户关系表里面的top_parent 冗余字段
            sql_top = f"UPDATE {ET_MEMBER_RELATIONS} SET top_parent_id={top_parent['top_parent_id']} WHERE member_id={member['id']}"
            MysqlWrite().write(sql_top)
            # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
            gl = MysqlSearch().get_one(f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
            if gl['parent_id'] != member['id']:
                # 删除树
                current_app.redis_cli.delete(f"drp_relation_member_{member['id']}")
            # 删除缓存
            rc = current_app.redis_cli
            rc.delete(f"user_apprentice_:{member['id']}")
            rc.delete(f"user_apprentice_:{parent['id']}")
            return True
        else:
            sql = f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id={parent['id']}"
            res = MysqlSearch().get_more(sql)[-1]
            if res:
                if res['parent_id'] != parent['id']:
                    try:
                        # 查询redis树结构是否有这个顶级id
                        parent_data = json.loads(
                            current_app.redis_cli.hget('drp_relation_member_{}'.format(res['parent_id']), 0).decode())
                        importer = DictImporter()
                        root = importer.import_(parent_data)
                        level_2 = findall_by_attr(root, parent['id'])[0]
                        lever_3 = Node(member['id'], parent=level_2)
                        exporter = DictExporter()
                        data = exporter.export(root)
                        current_app.redis_cli.hset('drp_relation_member_{}'.format(res['parent_id']), 0,
                                                   json.dumps(data))
                        # todo 查询当前用户关系是否入库
                        fx = MysqlSearch().get_one(
                            f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                        if not fx:
                            # 新增当前用户分销关系
                            sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
                            MysqlWrite().write(sql_iiuv)
                        # 更新数据库levels字段数据
                        sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels=3,parent_id='{parent['id']}' WHERE member_id='{member['id']}'"
                        MysqlWrite().write(sql)
                        # 插入当前三级用户关系表里面的top_parent 冗余字段
                        sql_top = f"UPDATE {ET_MEMBER_RELATIONS} SET top_parent_id={res['parent_id']} WHERE member_id={member['id']}"
                        MysqlWrite().write(sql_top)
                        # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
                        gl = MysqlSearch().get_one(
                            f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                        if gl['parent_id'] != member['id']:
                            # 删除树
                            current_app.redis_cli.delete(f"drp_relation_member_{member['id']}")
                        # 删除缓存
                        rc = current_app.redis_cli
                        rc.delete(f"user_apprentice_:{member['id']}")
                        rc.delete(f"user_apprentice_:{parent['id']}")
                        return True
                    except Exception as e:
                        current_app.logger.error(e)
            try:
                # 查找当前parent_id是否在数结构中存在
                parent_data = json.loads(
                    current_app.redis_cli.hget('drp_relation_member_{}'.format(parent['id']), 0).decode())
                importer = DictImporter()
                root = importer.import_(parent_data)
                child = Node(member['id'], parent=root)
                exporter = DictExporter()
                data = exporter.export(root)
                current_app.redis_cli.hset('drp_relation_member_{}'.format(parent['id']), 0, json.dumps(data))
                # todo 查询当前用户关系是否入库
                fx = MysqlSearch().get_one(
                    f"SELECt member_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                if not fx:
                    # 新增当前用户分销关系
                    sql_iiuv = f"INSERT INTO {ET_MEMBER_RELATIONS} (member_id,parent_id) VALUE ('{member['id']}','{parent['id']}')"
                    MysqlWrite().write(sql_iiuv)
                # 更新数据库levels字段数据
                sql = f"UPDATE {ET_MEMBER_RELATIONS} SET levels=2,parent_id='{parent['id']}' WHERE member_id='{member['id']}'"
                MysqlWrite().write(sql)
                # 判断当前用户是否已经关联了父级,如关联了就删除顶级用户树
                gl = MysqlSearch().get_one(
                    f"SELECT parent_id FROM {ET_MEMBER_RELATIONS} WHERE member_id='{member['id']}'")
                if gl['parent_id'] != member['id']:
                    # 删除树
                    current_app.redis_cli.delete(f"drp_relation_member_{member['id']}")
                # 删除缓存
                rc = current_app.redis_cli
                rc.delete(f"user_apprentice_:{member['id']}")
                rc.delete(f"user_apprentice_:{parent['id']}")
                return True
            except Exception as e:
                current_app.logger.error(e)
