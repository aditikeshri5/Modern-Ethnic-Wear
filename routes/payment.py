from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import Order
import hmac
import hashlib

payment = Blueprint('payment', __name__)

@payment.route('/initiate/<int:order_id>')
@login_required
def initiate(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('shop.index'))

    # SIMULATED PAYMENT MODE
    razorpay_order_id = f'order_demo_{order.id}'
    order.razorpay_order_id = razorpay_order_id
    db.session.commit()

    return render_template('shop/payment.html',
                           order=order,
                           razorpay_order_id=razorpay_order_id,
                           amount_paise=int(order.total * 100),
                           user=current_user)

@payment.route('/verify', methods=['POST'])
@login_required
def verify():
    order_id = request.form.get('order_id', type=int)
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('shop.index'))

    # Demo verification logic bypassing Razorpay
    razorpay_payment_id = f'pay_demo_{order.id}'

    order.razorpay_payment_id = razorpay_payment_id
    order.payment_status = 'paid'
    order.status = 'confirmed'
    db.session.commit()

    flash(f'Payment successful! Order #{order.order_number} confirmed. 🎉', 'success')
    return redirect(url_for('cart.order_success', order_id=order.id))

@payment.route('/failed', methods=['POST'])
@login_required
def failed():
    order_id = request.form.get('order_id', type=int)
    order = Order.query.get(order_id)
    if order and order.user_id == current_user.id:
        order.payment_status = 'failed'
        db.session.commit()
    flash('Payment failed. Please try again or choose Cash on Delivery.', 'danger')
    return redirect(url_for('cart.checkout'))

@payment.route('/cod-confirm/<int:order_id>', methods=['POST'])
@login_required
def cod_confirm(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    order.status = 'confirmed'
    db.session.commit()
    return jsonify({'success': True})
