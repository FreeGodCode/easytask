from sqlalchemy import Column, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class ETMerchants(db.Model):
    __tablename__ = 'et_merchants'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info="角色名称")
    user_type = db.Column(db.String(20, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info="用户角色")
    industry = db.Column(db.String(20, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info="所属行业")
    status = db.Column(db.Integer, server_default=db.FetchedValue(), info="用户状态,是否锁定 1:正常 2:已锁定")
    addtime = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info="添加商户时间")
    last_login = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info="最后登录时间")
    ip = db.Column(db.String(20, 'utf8mb4_unicode_ci'), nullable=False,server_default=db.FetchedValue(), info="ip地址")
    accounts_name = db.Column(db.String(20, 'utf8mb4_unicode_ci'), info="管理员名称")
    username = db.Column(db.String(20, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='商户账号')
    password = db.Column(db.String(20, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info="商户密码")
    mobile = db.Column(db.String(20, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info="手机号码")
