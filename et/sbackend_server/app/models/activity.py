from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class EtActivity(db.Model):
    __tablename__ = 'et_activity'
    __table_args__ = (
        db.Index('act_name', 'act_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    act_name = db.Column(db.String(99), nullable=False, info='活动名称')
    act_type = db.Column(db.Integer, nullable=False, info='活动类型')
    status = db.Column(db.Integer, server_default=db.FetchedValue(), info='活动状态: 0关闭1开启 2结束')
    round_num = db.Column(db.Integer, server_default=db.FetchedValue(), info='活动轮次')
    act_duration = db.Column(db.Integer, server_default=db.FetchedValue(), info='活动持续时间')
    rules = db.Column(db.String(299), server_default=db.FetchedValue(), info='活动规则')
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='活动添加日期')


class EtActivityConfigs(db.Model):
    __tablename__ = 'et_activity_configs'
    __table_args__ = (
        db.Index('act_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    act_id = db.Column(db.Integer, nullable=False, info='活动ID')
    act_configs = db.Column(db.String(299), server_default=db.FetchedValue(), info='活动参数配置')
    edit_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='编辑日期')

class ActivityRewards(db.Model):
    __tablename__ = 'activity_rewards'
    __table_args__ = (
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, nullable=False, info='member_id')
    pay_status = db.Column(db.Integer, nullable=False, info='pay_status')
    bonus=  db.Column(db.Integer, nullable=False, info='bonus')
    invite_count= db.Column(db.Integer, nullable=False, info='invite_count')
    activity_id=  db.Column(db.Integer, nullable=False, info='activity_id')
    rank_num=  db.Column(db.Integer, nullable=False, info='rank_num')
    name = db.Column(db.String(99), server_default=db.FetchedValue(), info='username')
    avatar = db.Column(db.String(299), server_default=db.FetchedValue(), info='avatar')
    fake = db.Column(db.Integer, nullable=False, info='fake')
    complete_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='编辑日期')
