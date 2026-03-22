from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from models import CartItem, Product, Coupon, Order, OrderItem, Inventory, Address
from datetime import datetime
import json
import random
import string

cart = Blueprint('cart', __name__)

def get_cart_data():
    if current_user.is_authenticated:
        items = CartItem.query.filter_by(user_id=current_user.id).all()
        return items
    return []

@cart.route('/')
@login_required
def view_cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(i.product.price * i.quantity for i in items)
    shipping = 0 if subtotal >= 999 else 99
    return render_template('shop/cart.html', items=items, subtotal=subtotal, shipping=shipping)

@cart.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    size = request.form.get('size', '')
    color = request.form.get('color', '')
    quantity = request.form.get('quantity', 1, type=int)

    product = Product.query.get_or_404(product_id)
    inv = Inventory.query.filter_by(product_id=product_id, size=size, color=color).first()
    available = inv.quantity if inv else 0

    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
        size=size,
        color=color
    ).first()

    wanted = (existing.quantity if existing else 0) + quantity
    if wanted > available:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': f'Only {available} items in stock.'}), 400
        flash(f'Only {available} items in stock.', 'danger')
        return redirect(url_for('shop.product_detail', slug=product.slug))

    if existing:
        existing.quantity += quantity
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id,
                       size=size, color=color, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'added', 'cart_count': cart_count})
    flash(f'{product.name} added to cart! 🛍️', 'success')
    return redirect(url_for('cart.view_cart'))

@cart.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    qty = request.form.get('quantity', type=int)
    if qty and qty > 0:
        inv = Inventory.query.filter_by(product_id=item.product_id, size=item.size, color=item.color).first()
        available = inv.quantity if inv else 0
        if qty > available:
            return jsonify({'error': f'Only {available} in stock'}), 400
        item.quantity = qty
        db.session.commit()
    elif qty == 0:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart.view_cart'))

@cart.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('cart.view_cart'))
    db.session.delete(item)
    db.session.commit()
    flash('Item removed.', 'info')
    return redirect(url_for('cart.view_cart'))

@cart.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    code = request.form.get('coupon_code', '').upper()
    coupon = Coupon.query.filter_by(code=code, is_active=True).first()
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code.'})
    if coupon.valid_until and coupon.valid_until < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Coupon expired.'})
    if coupon.used_count >= coupon.max_uses:
        return jsonify({'success': False, 'message': 'Coupon usage limit reached.'})
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(i.product.price * i.quantity for i in items)
    if subtotal < coupon.min_order:
        return jsonify({'success': False, 'message': f'Minimum order ₹{coupon.min_order} required.'})

    if coupon.discount_type == 'percent':
        discount = subtotal * coupon.discount_value / 100
    else:
        discount = coupon.discount_value

    session['coupon_code'] = code
    session['discount'] = discount
    return jsonify({'success': True, 'discount': discount,
                    'message': f'Coupon applied! You save ₹{discount:.0f}'})

@cart.route('/checkout')
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(i.product.price * i.quantity for i in items)
    discount = session.get('discount', 0)
    shipping = 0 if subtotal >= 999 else 99
    total = subtotal - discount + shipping
    return render_template('shop/checkout.html', items=items, addresses=addresses,
                           subtotal=subtotal, discount=discount,
                           shipping=shipping, total=total,
                           coupon_code=session.get('coupon_code', ''))

def generate_order_number():
    return 'RNG' + ''.join(random.choices(string.digits, k=8))

@cart.route('/place-order', methods=['POST'])
@login_required
def place_order():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Cart is empty.', 'danger')
        return redirect(url_for('cart.view_cart'))

    payment_method = request.form.get('payment_method', 'cod')

    if request.form.get('new_line1'):
        address = Address(
            user_id=current_user.id,
            name=request.form.get('new_name') or current_user.name,
            phone=request.form.get('new_phone') or current_user.phone,
            line1=request.form.get('new_line1'),
            line2=request.form.get('new_line2', ''),
            city=request.form.get('new_city'),
            state=request.form.get('new_state'),
            pincode=request.form.get('new_pincode')
        )
        db.session.add(address)
        db.session.flush()
    else:
        address_id = request.form.get('address_id', type=int)
        address = Address.query.get(address_id)
        if not address or address.user_id != current_user.id:
            flash('Please select a valid address.', 'danger')
            return redirect(url_for('cart.checkout'))

    # Verify inventory again before creating the order
    for item in items:
        inv = Inventory.query.filter_by(product_id=item.product_id, size=item.size, color=item.color).first()
        available = inv.quantity if inv else 0
        if available < item.quantity:
            flash(f'{item.product.name} ({item.size}, {item.color}) is out of stock. Available: {available}', 'danger')
            return redirect(url_for('cart.view_cart'))

    subtotal = sum(i.product.price * i.quantity for i in items)
    discount = session.get('discount', 0)
    shipping = 0 if subtotal >= 999 else 99
    total = subtotal - discount + shipping

    addr_snapshot = json.dumps({
        'name': address.name, 'phone': address.phone,
        'line1': address.line1, 'line2': address.line2,
        'city': address.city, 'state': address.state, 'pincode': address.pincode
    })

    order = Order(
        order_number=generate_order_number(),
        user_id=current_user.id,
        status='pending',
        subtotal=subtotal,
        discount=discount,
        shipping_charge=shipping,
        total=total,
        coupon_code=session.get('coupon_code', ''),
        shipping_address=addr_snapshot,
        payment_method=payment_method,
        payment_status='pending' if payment_method == 'cod' else 'pending'
    )
    db.session.add(order)
    db.session.flush()

    for item in items:
        oi = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            size=item.size,
            color=item.color,
            quantity=item.quantity,
            unit_price=item.product.price,
            total_price=item.product.price * item.quantity
        )
        db.session.add(oi)
        # Deduct inventory
        inv = Inventory.query.filter_by(product_id=item.product_id, size=item.size, color=item.color).first()
        if inv:
            inv.quantity = max(0, inv.quantity - item.quantity)

    # Clear cart
    for item in items:
        db.session.delete(item)

    # Apply coupon usage
    if session.get('coupon_code'):
        coupon = Coupon.query.filter_by(code=session['coupon_code']).first()
        if coupon:
            coupon.used_count += 1

    db.session.commit()
    session.pop('coupon_code', None)
    session.pop('discount', None)

    if payment_method == 'online':
        return redirect(url_for('payment.initiate', order_id=order.id))

    flash(f'Order #{order.order_number} placed successfully! 🎉', 'success')
    return redirect(url_for('cart.order_success', order_id=order.id))

@cart.route('/order-success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('shop/order_success.html', order=order)

@cart.route('/orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('shop/orders.html', orders=orders)

@cart.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.role == 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('cart.my_orders'))
    return render_template('shop/order_detail.html', order=order)
