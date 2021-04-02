from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class EtPayLog(db.Model):
    __tablename__ = 'et_pay_logs'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer)
    open_id = db.Column(db.String(30))
    alipay_id = db.Column(db.String(30), nullable=False)
    transaction_no = db.Column(db.String(50), nullable=False)
    pay_price = db.Column(db.Integer)
    order_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Integer)
    return_code = Column(db.String(255))
    pay_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(),)
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())
