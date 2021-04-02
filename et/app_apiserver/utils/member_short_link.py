from utils.mysql_cli import MysqlSearch,MysqlWrite
from utils.constants import MEMBERS_TABLE
from flask import g
from utils.short_link import get_short_link

def mer_short_link():
    # 查询当前用户是否有旧的邀请链接
    old_sql = f"SELECT short_link,IIUV FROM {MEMBERS_TABLE} WHERE id = {g.user_id}"
    old_data = MysqlSearch().get_one(old_sql)
    old_short_link = old_data['short_link']
    if old_short_link != 'N':
        short_link = old_short_link
        return short_link
    elif old_short_link == 'N':
        # 生成短链接入库
        res_data = get_short_link(old_data['IIUV'])
        w_sql = f"UPDATE {MEMBERS_TABLE} SET short_link = '{res_data}' WHERE id = {g.user_id}"
        res = MysqlWrite().write(w_sql)
        if res == 1:
            return res_data
        else:
            return 'N'