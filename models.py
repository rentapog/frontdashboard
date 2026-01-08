from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    paypal_id = db.Column(db.String(120), unique=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(128))
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[id]), lazy='dynamic')

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    daily_payment_amount = db.Column(db.Float, nullable=False)

class UserPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    activated_date = db.Column(db.DateTime, default=datetime.utcnow)
    daily_payment_active = db.Column(db.Boolean, default=False)
    daily_payment_start_date = db.Column(db.DateTime)

class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referred_date = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20))  # 'activation', 'daily'
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    paypal_txn_id = db.Column(db.String(120))
