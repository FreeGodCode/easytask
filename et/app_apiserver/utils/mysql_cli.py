import MySQLdb
# from flask import current_app

from haozhuan.config import global_config


class MysqlSearch(object):
    def __init__(self):
        self.get_connection()

    def get_connection(self):
        try:
            self.connection = MySQLdb.connect(
                host=global_config.getRaw('mysql', 'HOST'),
                user=global_config.getRaw('mysql', 'USER'),
                password=global_config.getRaw('mysql', 'PASSWORD'),
                db=global_config.getRaw('mysql', 'DB'),
                charset=global_config.getRaw('mysql', 'CHARSET'),
            )
        except MySQLdb.Error as e:
            print('Error : {} '.format(e))

    def close_connection(self):
        try:
            if self.connection:
                self.connection.close()
        except MySQLdb.Error as e:
            print('Error : {} '.format(e))

    def get_one(self,sql):
        try:
            # 获取会话指针
            cursor = self.connection.cursor()
            # 执行sql
            cursor.execute(sql)
            # 使用 下面方法把元祖转成字典列表,并且进行数据的整合
            data = cursor.fetchone()
            if not data:
                cursor.close()
                return False
            result = dict(zip([k[0] for k in cursor.description],data))
            cursor.close()
            return result
        except Exception as e:
            print("Exception: {}".format(e))
        finally:
            # 关闭 cursor 和连接
            self.close_connection()

    def get_more(self, sql):
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            # 使用 下面方法把元祖转成字典列表,并且进行数据的整合
            result = [dict(zip([k[0] for k in cursor.description],row))
                for row in cursor.fetchall()]
            cursor.close()
            return result
        except Exception as e:
            print("Exception: {}".format(e))
        finally:
            self.close_connection()


class MysqlWrite(object):
    def __init__(self):
        self.get_connection()

    def get_connection(self):
        try:
            self.connection = MySQLdb.connect(
                host=global_config.getRaw('mysql', 'HOST'),
                user=global_config.getRaw('mysql', 'USER'),
                password=global_config.getRaw('mysql', 'PASSWORD'),
                db=global_config.getRaw('mysql', 'DB'),
                charset=global_config.getRaw('mysql', 'CHARSET'),
            )
        except MySQLdb.Error as e:
            print('Error : {} '.format(e))

    def close_connection(self):
        try:
            if self.connection:
                self.connection.close()
        except MySQLdb.Error as e:
            print('Error : {} '.format(e))

    def write(self,sql):
        try:
            cursor = self.connection.cursor()
            result = cursor.execute(sql)
            self.connection.commit()
            cursor.close()
            return result
        except Exception as e:
            print("Exception: {}".format(e))
            self.connection.rollback()
        finally:
            self.close_connection()



