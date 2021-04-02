from datetime import datetime
from app.utils.core import db

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class EtAccountRole(db.Model):
    __tablename__ = 'et_account_roles'
    __table_args__ = (
        db.Index('account_role', 'account_id', 'roles'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False, info='角色ID')
    roles = db.Column(db.Integer, nullable=False, info='权限ID 1:平台权限2:超级管理员')



class EtAccount(db.Model):
    __tablename__ = 'et_accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(99), nullable=False, info='运营账号名称')
    password = db.Column(db.String(99), nullable=False, info='账号密码')
    role_id = db.Column(db.Integer, nullable=False, info='角色ID')
    status = db.Column(db.Integer, server_default=db.FetchedValue(), info='状态: 1正常 2禁用')
    add_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='账号添加时间')
    last_login = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='账号添加时间')
    ip = db.Column(db.String(20), nullable=False, info='ip')


