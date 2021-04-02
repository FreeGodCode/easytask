from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class EtRechargeWithdrawal(db.Model):
    __tablename__ = "et_recharge_withdrawal"

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    accounts_name = db.Column(db.String(99), nullable=False, info="管理员账户")
    withdrawal_num = db.Column(db.Integer(), nullable=False, info="流水号")
    add_time = db.Column(db.DateTime, nullable=False, info="充值时间")
    mer_id = db.Column(db.Integer, nullable=False, info="商户id")
    balance = db.Column(db.Integer(), nullable=False, info="充值金额")
    business_id = db.Column(db.Integer, nullable=False, info="任务摘要 0:删除任务退回 1:创建任务冻结 2:平台充值")
    type_id = db.Column(db.Integer, nullable=False, info="类型 0:支出 1:收入")