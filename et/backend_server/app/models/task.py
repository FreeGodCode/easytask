from sqlalchemy import Column, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class EtMemberEarning(db.Model):
    """商家收益表"""
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


class EtTaskOrder(db.Model):
    """商家任务订单表"""
    __tablename__ = 'et_task_orders'
    __table_args__ = (
        db.Index('task_member', 'task_id', 'member_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, nullable=False, info='任务ID')
    member_id = db.Column(db.Integer, nullable=False, info='用户ID')
    account_id = db.Column(db.Integer, nullable=False, info='审核员ID')
    status = db.Column(db.Integer, server_default=db.FetchedValue(), info='任务完成状态 1：完成 2：未完成')
    chance = db.Column(db.Integer, server_default=db.FetchedValue(), info='高级用户特权机会')
    add_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='领取任务时间')
    submit_time = db.Column(db.DateTime, info='提交任务时间')
    user_submit = db.Column(db.String(255, 'utf8mb4_unicode_ci'),nullable=False, info='提交任务凭证')
    app_safe_info = db.Column(db.String(255, 'utf8mb4_unicode_ci'),nullable=False, info='APP指纹信息')
    safe_token = db.Column(db.String(100, 'utf8mb4_unicode_ci'),nullable=False, info='用户任务交单验证字符串')
    confidence = db.Column(db.Integer, server_default=db.FetchedValue(), info='用户作弊置信度')
    verify_log = db.Column(db.String(99, 'utf8mb4_unicode_ci'), nullable=False, info='审核记录')


class EtTask(db.Model):
    """商家任务表"""
    __tablename__ = 'et_tasks'
    __table_args__ = (
        db.Index('name_account', 'name', 'account_id'),
    )

    id = db.Column(db.Integer, primary_key=True, info='任务ID')
    account_id = db.Column(db.Integer, server_default=db.FetchedValue(), info='添加任务账号ID')
    name = db.Column(db.String(99, 'utf8mb4_unicode_ci'), nullable=False, info='任务名称')
    status = db.Column(db.Integer, server_default=db.FetchedValue(), info='任务状态  1：待审核下架 2：审核上架3：已关闭4：删除5：驳回6：待提交')
    task_class = db.Column(db.Integer, index=True, server_default=db.FetchedValue(), info='任务所属类别 1：平台 2：高级 3:特殊任务')
    end_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='任务截止时间')
    begin_task_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='前端用户允许做单开始时间')
    check_time = db.Column(db.DateTime, info='(审核)上架时间')
    count_tasks = db.Column(db.Integer, server_default=db.FetchedValue(), info='任务累计发布数')
    allow_nums = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='允许参与次数')
    allow_member_nums = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='任务允许参与人数')
    virtual_nums = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='虚拟人气数')
    tasks_counts = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='任务总参与次数')
    task_reward = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='任务奖励')
    task_info = db.Column(db.String(199, 'utf8mb4_unicode_ci'), nullable=False, info='任务说明')
    poster_img = db.Column(db.String(199, 'utf8mb4_unicode_ci'), nullable=False, server_default=db.FetchedValue(), info='任务发布者头像')
    task_steps = db.Column(db.Text(300, 'utf8mb4_unicode_ci'), nullable=False, server_default=db.FetchedValue(), info='任务指引图片，存储七牛云图片地址')
    tags = db.Column(db.String(99, 'utf8mb4_unicode_ci'), nullable=False, server_default=db.FetchedValue(), info='前端任务标签')
    recommend = db.Column(db.Integer, server_default=db.FetchedValue(), info='热门推荐权重越大越靠前')
    edit_time = db.Column(db.DateTime, server_default=db.FetchedValue(), info='上次编辑时间')
    deadline_time = db.Column(db.String(25, 'utf8mb4_unicode_ci'), info='任务交付期限 保存秒')
    sys_tags = db.Column(db.String(99, 'utf8mb4_unicode_ci'), info='后台任务标签')
    task_cats = db.Column(db.String(99, 'utf8mb4_unicode_ci'), info='任务大分类')
    check_router = db.Column(db.String(199, 'utf8mb4_unicode_ci'), info='任务分享跳转路由')
    servicefree = db.Column(db.Integer, nullable=False, info="任务收取的服务费")
    mer_id = db.Column(db.Integer, nullable=False, info="商戶id")
    task_balance = db.Column(db.Integer, info="任務金額")

class EtTasksVerify(db.Model):
    """商家任务审核表"""
    __tablename__ = 'et_tasks_verify'

    id = db.Column(db.Integer, primary_key=True, info='审核ID')
    tasks_id = db.Column(db.Integer, index=True, server_default=db.FetchedValue(), info='任务ID')
    account_name = db.Column(db.Integer, server_default=db.FetchedValue(), info='任务审核账号ID')
    verify_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='审核时间（任务上架）')
    comment = db.Column(db.String, nullable=False, info='审核员消息备注')
    add_time = db.Column(db.DateTime, nullable=False, info="任务提交审核时间")