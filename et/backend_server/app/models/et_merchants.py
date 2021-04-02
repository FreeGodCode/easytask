from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class EtMerchants(db.Model):
    __tablename__ = "et_merchants"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nickname = db.Column(db.String(20), nullable=False, info="角色名称")
    user_type = db.Column(db.String(20), nullable=False, info="用户角色")
    industry = db.Column(db.String(20), nullable=False, info="所属行业")
    status = db.Column(db.Integer, default=1, info="是否锁定")
    addtime = db.Column(db.DateTime, info="添加时间")
    last_login = db.Column(db.DateTime, info="最后登录时间")
    ip = db.Column(db.String(20), info="ip")
    accounts_name = db.Column(db.String(), info="管理员名称")
    password = db.Column(db.String(100), nullable=False, info="密码")
    permissions = db.Column(db.String(255), nullable=False, info="商户权限")
    username = db.Column(db.String(20), nullable=False, info="账号")
    mobile = db.Column(db.String(20), nullable=False, info="手机号码")
    balance = db.Column(db.Integer, info="余额*100入库")
    balance_version = db.Column(db.String(60))
    lock_balance = db.Column(db.Integer, info="冻结金额*100入库")