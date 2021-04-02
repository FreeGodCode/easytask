from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class EtGlobalConfig(db.Model):
    __tablename__ = 'et_global_config'

    id = db.Column(db.Integer, primary_key=True)
    notice = db.Column(db.String(199), nullable=False, info='系统公告')
    domains = db.Column(db.String(255), nullable=False, info='风险域名')
    share_domains = db.Column(db.String(255), nullable=False, info='分享页风险域名')
    task_limit = db.Column(db.Integer, server_default=db.FetchedValue(), info='特殊任务接取数限制')
    banners = db.Column(db.String(255, 'utf8mb4_unicode_ci'), server_default=db.FetchedValue(), info='json:banner广告配置')
    limit_withdrawal = db.Column(db.String(99), server_default=db.FetchedValue(), info='提现门槛:当天的次数，可提现金额档次')
    sys_status = db.Column(db.Integer, server_default=db.FetchedValue(), info='系统状态: 1正常 2禁用')
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='上次更新时间')
    rules = db.Column(db.String(199), server_default=db.FetchedValue(), info='')
    helpers = db.Column(db.String(199), server_default=db.FetchedValue(), info='')
    start_page = db.Column(db.String(199), server_default=db.FetchedValue(), info='')
    upgrade = db.Column(db.Integer, server_default=db.FetchedValue(), info='')
    app_down = db.Column(db.String(199), server_default=db.FetchedValue(), info='')


class EtAppConfig(db.Model):
    __tablename__ = 'et_app_config'

    id = db.Column(db.Integer, primary_key=True)
    cur_version = db.Column(db.String(99), nullable=False, info='当前app版本')
    update_status = db.Column(db.Integer, server_default=db.FetchedValue(), info='App更新状态: 1非强制 2强制')
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='上次更新时间')

class EtAppsPubHistory(db.Model):
    __tablename__ = 'et_apps_pub_history'
    __table_args__ = (
        db.Index('version_downurl', 'version', 'down_url'),
    )

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(99), nullable=False, info='当前系统版本')
    osversion = db.Column(db.String(30), nullable=False, info='当前平台版本')
    update_status = db.Column(db.Integer, server_default=db.FetchedValue(), info='App更新状态: 1非强制 2强制')
    down_url = db.Column(db.String(199), server_default=db.FetchedValue(), info='app下载地址')
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='上次更新时间')
    up_logs = db.Column(db.String(299), server_default=db.FetchedValue(), info='更新内容')
