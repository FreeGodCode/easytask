from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()



class EtMemberExtend(db.Model):
    __tablename__ = 'et_member_extend'

    member_id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue(), info='用户ID')
    open_id = db.Column(db.String(30, 'utf8mb4_unicode_ci'), nullable=False, index=True, info='用户微信唯一标识')
    sex = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='性别 0.未知 1.男 2.女')
    province = db.Column(db.String(50, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='省份')
    city = db.Column(db.String(50, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='城市')
    company = db.Column(db.String(100, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='公司名')
    occupation = db.Column(db.String(50, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='职业')



class EtMember(db.Model):
    __tablename__ = 'et_members'
    __table_args__ = (
        db.Index('cls_mobile_IIUV', 'm_class', 'mobile', 'IIUV'),
    )

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255, 'utf8mb4_unicode_ci'), nullable=False, info='用户昵称')
    open_id = db.Column(db.String(30, 'utf8mb4_unicode_ci'), nullable=False, info='用户微信唯一标识')
    union_id = db.Column(db.String(30, 'utf8mb4_unicode_ci'), nullable=False, info='微信开放平台唯一标识')
    alipayid = db.Column(db.String(30, 'utf8mb4_unicode_ci'), nullable=False, info='支付宝用户唯一标识')
    status = db.Column(db.Integer, server_default=db.FetchedValue(), info='会员状态 1：正常 2：禁用')
    m_class = db.Column(db.Integer, index=True, info='用户等级 1：普通用户 2：高级用户')
    mobile = db.Column(db.String(30, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='手机')
    realname = db.Column(db.String(99, 'utf8mb4_unicode_ci'), index=True, server_default=db.FetchedValue(), info='姓名')
    avatar = db.Column(db.String(255, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='会员头像')
    reg_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='注册时间')
    logout_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='上次登出时间')
    IIUV = db.Column(db.String(50, 'utf8mb4_unicode_ci'), info='代表每个用户唯一的注册推荐码，用于分享')
    setreal = db.Column(db.Integer,  info='用户是否完成实名认证1认证2未认证')
    balance = db.Column(db.Integer, index=True, info='用户余额')
    balance_version = db.Column(db.String(66, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='乐观锁版本号')
    app_version = db.Column(db.String(25, 'utf8mb4_unicode_ci'),server_default=db.FetchedValue(), info='APP版本号')
