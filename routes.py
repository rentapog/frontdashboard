
import os
import base64
import hashlib
import hmac
from flask import Blueprint, request, jsonify, current_app
from app import db
from models import User, Referral, Package, UserPackage, Payment
from datetime import datetime

bp = Blueprint('main', __name__)

# Root route for health check or homepage
@bp.route('/')
def index():
    return 'API is running!'

# PayPal Webhook endpoint
@bp.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    # Webhook signature verification
    webhook_id = os.getenv('PAYPAL_WEBHOOK_ID')
    transmission_id = request.headers.get('Paypal-Transmission-Id')
    transmission_time = request.headers.get('Paypal-Transmission-Time')
    cert_url = request.headers.get('Paypal-Cert-Url')
    auth_algo = request.headers.get('Paypal-Auth-Algo')
    transmission_sig = request.headers.get('Paypal-Transmission-Sig')
    webhook_event = request.get_data(as_text=True)
    actual_body = request.get_data()

    # For local verification, use the webhook secret (deprecated, but simple for dev)
    webhook_secret = os.getenv('PAYPAL_WEBHOOK_SECRET')
    if webhook_secret:
        expected_sig = base64.b64encode(hmac.new(webhook_secret.encode(), actual_body, hashlib.sha256).digest()).decode()
        if not hmac.compare_digest(expected_sig, transmission_sig or ''):
            return jsonify({'error': 'Invalid webhook signature'}), 400

    # Continue with event handling
    event = request.json
    event_type = event.get('event_type')
    resource = event.get('resource', {})
    # Example: handle payment capture completed
    if event_type == 'CHECKOUT.ORDER.APPROVED' or event_type == 'PAYMENT.CAPTURE.COMPLETED':
        order_id = resource.get('id')
        # Find payment by PayPal order/txn id
        payment = Payment.query.filter_by(paypal_txn_id=order_id).first()
        if payment:
            payment.payment_date = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Payment recorded'}), 200
        return jsonify({'error': 'Payment not found'}), 404
    # Add more event types as needed
    return jsonify({'message': 'Event received'}), 200

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    first_name = data.get('first_name')
    ref_code = data.get('ref_code')  # referrer's email, id, or username
    package_id = data.get('package_id')
    admin_user = User.query.filter_by(username='seobrain').first()
    if not email or not package_id or not username or not first_name:
        return jsonify({'error': 'Missing required fields'}), 400
    if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 400
    user = User(email=email, username=username)
    # Always pay admin fee to admin
    if admin_user:
        admin_payment = Payment(
            payer_id=user.id,
            payee_id=admin_user.id,
            package_id=package_id,
            amount=Package.query.get(package_id).price,
            payment_type='activation',
            payment_date=datetime.utcnow()
        )
        db.session.add(admin_payment)
        db.session.commit()
    # Referral logic
    if ref_code:
        referrer = User.query.filter((User.email==ref_code)|(User.id==ref_code)|(User.username==ref_code)).first()
        if referrer:
            user.referrer_id = referrer.id
    db.session.add(user)
    db.session.commit()
    # Assign package
    up = UserPackage(user_id=user.id, package_id=package_id)
    db.session.add(up)
    db.session.commit()
    # Track referral: always assign referral to the user who brought them in
    if user.referrer_id:
        referral = Referral(referrer_id=user.referrer_id, referred_id=user.id)
        db.session.add(referral)
        db.session.commit()
    return jsonify({'message': 'User registered', 'user_id': user.id})

@bp.route('/referrals/<int:user_id>')
def get_referrals(user_id):
    count = Referral.query.filter_by(referrer_id=user_id).count()
    return jsonify({'referral_count': count})


from paypal import create_paypal_order

# Initiate a PayPal payment (activation or daily)
@bp.route('/pay', methods=['POST'])
def pay():
    data = request.json
    user_id = data.get('user_id')
    package_id = data.get('package_id')
    payment_type = data.get('payment_type', 'activation')
    user = User.query.get(user_id)
    package = Package.query.get(package_id)
    if not user or not package:
        return jsonify({'error': 'Invalid user or package'}), 400
    amount = package.price if payment_type == 'activation' else package.daily_payment_amount
    desc = f"{package.name} Web Hosting Package ({payment_type.title()} Fee)"
    order = create_paypal_order(amount, desc)
    # Record payment intent (not captured yet)
    payment = Payment(
        payer_id=user.referrer_id if payment_type == 'daily' else user.id,
        payee_id=user.id,
        package_id=package.id,
        amount=amount,
        payment_type=payment_type,
        paypal_txn_id=order['id']
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({'paypal_order': order})

# Activate daily payments after 3 paid referrals
@bp.route('/activate-daily/<int:user_id>', methods=['POST'])
def activate_daily(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    # Count paid referrals (referrals with activation payment to admin)
    referrals = Referral.query.filter_by(referrer_id=user.id).all()
    paid_count = 0
    for r in referrals:
        payment = Payment.query.filter_by(payer_id=r.referred_id, payee_id=admin_user.id, payment_type='activation').first()
        if payment:
            paid_count += 1
    if paid_count >= 3:
        up = UserPackage.query.filter_by(user_id=user.id).first()
        if up and not up.daily_payment_active:
            up.daily_payment_active = True
            up.daily_payment_start_date = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Daily payments activated'})
        return jsonify({'message': 'Already active'})
    return jsonify({'message': 'Not enough paid referrals', 'paid_count': paid_count})
