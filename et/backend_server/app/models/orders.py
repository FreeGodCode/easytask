from sqlalchemy import Column, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()



class EtMemberEarning(db.Model):
    __tablename__ = 'et_member_earnings'
    __table_args__ = (
        db.Index('member_task_type', 'member_id', 'task_id', 'amount_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, nullable=False, info='用户ID')
    task_id = db.Column(db.Integer, nullable=False, info='奖励任务ID')
    amounts = db.Column(db.SmallInteger, nullable=False, info='资金详细数值(原值*100存储)')
    amount_type = db.Column(db.Integer, server_default=db.FetchedValue(), info='收益来源：1：任务收益 2：分销佣金')
    add_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='资金入账日期')
    task_order_id = db.Column(db.Integer, nullable=False, info='任务订单ID')


class EtMemberRelation(db.Model):
    __tablename__ = 'et_member_relations'
    __table_args__ = (
        db.Index('member_parent_levels', 'member_id', 'parent_id', 'levels'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, nullable=False, info='用户ID')
    parent_id = db.Column(db.Integer, nullable=False, info='上级用户ID')
    child_id = db.Column(db.Integer, nullable=False, info='下级用户ID')
    levels = db.Column(db.Integer, nullable=False, info='当前分销节点层级：1级 2级 3级')



class EtMemberWithdrawal(db.Model):
    __tablename__ = 'et_member_withdrawal'
    __table_args__ = (
        db.Index('member_verify', 'member_id', 'verify','start_time','end_time','amounts'),
        db.Index('pay_status', 'check_time'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, server_default=db.FetchedValue(), info='用户ID')
    verify = db.Column(db.SmallInteger, server_default=db.FetchedValue(), info='后台提现审核：0：待审核 1：审核未通过 2:通过审核')
    verify_log = db.Column(db.String(100, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='审核备注')
    withdrawal_type = db.Column(db.Integer, server_default=db.FetchedValue(), info='提现方式：1：支付宝2：微信')
    start_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='资金提现开始日期')
    end_time = db.Column(db.DateTime, info='提现到账日期')
    amounts = db.Column(db.SmallInteger, nullable=False, info='提现额详细数值(原值*100存储)')
    account = db.Column(db.String(100, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='审核员账户')
    pay_status = db.Column(db.SmallInteger, server_default=db.FetchedValue(), info='支付状态：1：待支付2：支付中3：支付成功')
    check_time = db.Column(db.DateTime, info='审核时间')
    pay_log = db.Column(db.String(500, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='支付接口日志')
    origin_amount = db.Column(db.SmallInteger, nullable=False, info='原提现金额，未扣除手续费')

