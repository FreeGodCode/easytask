# from sqlalchemy import Column, DateTime, Index, Integer, SmallInteger, String
# from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class EtDrpConfig(db.Model):
    __tablename__ = 'et_drp_config'

    id = db.Column(db.Integer, primary_key=True)
    drp_layers = db.Column(db.Integer, server_default=db.FetchedValue(),info='分销层级')
    profit_percentage = db.Column(db.String(199, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(),info='json:各级分销奖金比列')
    need_setreal = db.Column(db.Integer, server_default=db.FetchedValue(),info='是否实名后计算收益 1:需要实名2：无需实名')
    daily_max = db.Column(db.Integer, server_default=db.FetchedValue(),info='每日邀请奖励金额上限，达标后不计算收益（金额*100）')
    min_money = db.Column(db.Integer, server_default=db.FetchedValue(),info='提现最少金额（金额*100）')
    handling_fee = db.Column(db.String(5, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='提现手续费')
    daily_withdrawal = db.Column(db.String(99, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(),info='每日提现门槛:当天的次数，可提现金额档次')
    withdrawal_condition = db.Column(db.String(500, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(),info='json:配置按条件提现门槛(总金额，新用户，收徒数)')
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())


class EtMemberDrp(db.Model):
    __tablename__ = 'et_member_drps'
    __table_args__ = (
        db.Index('member_from', 'member_id', 'from_member_id','add_time'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, nullable=False, info='用户ID')
    from_member_id = db.Column(db.Integer, nullable=False, info='贡献该笔奖励用户ID')
    from_task_id = db.Column(db.Integer, nullable=False, info='贡献该笔奖励任务ID')
    amounts = db.Column(db.SmallInteger, nullable=False, info='收益资金详细数值(原值*100存储)')
    add_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='分销收益入账日期')


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
        db.Index('member_verify', 'member_id', 'verify'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, server_default=db.FetchedValue(), info='用户ID')
    verify = db.Column(db.Integer, server_default=db.FetchedValue(), info='后台提现审核：0：待审核 1：审核未通过 2:通过审核')
    verify_log = db.Column(db.String(100, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='审核备注')
    withdrawal_type = db.Column(db.Integer, server_default=db.FetchedValue(), info='提现方式：1：微信 2支付宝')
    start_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='资金提现开始日期')
    end_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='提现到账日期')


class EtPromoteLink(db.Model):
    __tablename__ = 'et_promote_link'

    id = db.Column(db.Integer, primary_key=True)
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='更新时间')
    link_url = db.Column(db.String(255, 'utf8mb4_unicode_ci'), nullable=False, server_default=db.FetchedValue(), info='推广链接URL')
    enter_page = db.Column(db.String(255, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='入口页面')
    click_count = db.Column(db.Integer, server_default=db.FetchedValue(), info='点击次数')
    attention_num = db.Column(db.Integer, server_default=db.FetchedValue(), info='引进用户数')
    success_order_count = db.Column(db.Integer, server_default=db.FetchedValue(), info='成功订单数')
    member_id = db.Column(db.Integer, server_default=db.FetchedValue(), info='用户id')
    parent_id = db.Column(db.Integer, server_default=db.FetchedValue(), info='推广链接对应用户id')
