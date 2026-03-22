from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import Order, OrderItem, Product, User, Category
from sqlalchemy import func, extract
from datetime import datetime, timedelta

analytics = Blueprint('analytics', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            from flask import redirect, url_for, flash
            flash('Admin access required.', 'danger')
            return redirect(url_for('shop.index'))
        return f(*args, **kwargs)
    return login_required(decorated)

@analytics.route('/')
@admin_required
def dashboard():
    return render_template('admin/analytics.html')

@analytics.route('/api/revenue')
@admin_required
def revenue_data():
    period = request.args.get('period', 'monthly')
    now = datetime.utcnow()

    if period == 'daily':
        start = now - timedelta(days=30)
        result = db.session.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total).label('revenue'),
            func.count(Order.id).label('orders')
        ).filter(Order.created_at >= start, Order.payment_status == 'paid')\
         .group_by(func.date(Order.created_at)).all()
        labels = [str(r.date) for r in result]
    elif period == 'weekly':
        start = now - timedelta(weeks=12)
        result = db.session.query(
            func.strftime('%Y-W%W', Order.created_at).label('week'),
            func.sum(Order.total).label('revenue'),
            func.count(Order.id).label('orders')
        ).filter(Order.created_at >= start, Order.payment_status == 'paid')\
         .group_by(func.strftime('%Y-W%W', Order.created_at)).all()
        labels = [r.week for r in result]
    else:
        result = db.session.query(
            func.strftime('%Y-%m', Order.created_at).label('month'),
            func.sum(Order.total).label('revenue'),
            func.count(Order.id).label('orders')
        ).filter(Order.payment_status == 'paid')\
         .group_by(func.strftime('%Y-%m', Order.created_at)).all()
        labels = [r.month for r in result]

    return jsonify({
        'labels': labels,
        'revenue': [float(r.revenue or 0) for r in result],
        'orders': [int(r.orders) for r in result]
    })

@analytics.route('/api/top-products')
@admin_required
def top_products():
    results = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('units_sold'),
        func.sum(OrderItem.total_price).label('revenue')
    ).join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.payment_status == 'paid')\
     .group_by(Product.id)\
     .order_by(func.sum(OrderItem.revenue).desc() if False else func.sum(OrderItem.quantity).desc())\
     .limit(10).all()

    return jsonify({
        'products': [r.name for r in results],
        'units': [int(r.units_sold) for r in results],
        'revenue': [float(r.revenue or 0) for r in results]
    })

@analytics.route('/api/category-breakdown')
@admin_required
def category_breakdown():
    results = db.session.query(
        Category.name,
        func.count(OrderItem.id).label('items'),
        func.sum(OrderItem.total_price).label('revenue')
    ).join(Product, Product.category_id == Category.id)\
     .join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.payment_status == 'paid')\
     .group_by(Category.id).all()

    return jsonify({
        'categories': [r.name for r in results],
        'revenue': [float(r.revenue or 0) for r in results],
        'items': [int(r.items) for r in results]
    })

@analytics.route('/api/order-status')
@admin_required
def order_status():
    results = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()
    return jsonify({
        'statuses': [r.status for r in results],
        'counts': [int(r.count) for r in results]
    })

@analytics.route('/api/summary')
@admin_required
def summary():
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    this_month_rev = db.session.query(func.sum(Order.total))\
        .filter(Order.created_at >= month_start, Order.payment_status == 'paid').scalar() or 0
    last_month_rev = db.session.query(func.sum(Order.total))\
        .filter(Order.created_at >= last_month_start,
                Order.created_at < month_start,
                Order.payment_status == 'paid').scalar() or 0

    this_month_orders = Order.query.filter(Order.created_at >= month_start).count()
    last_month_orders = Order.query.filter(Order.created_at >= last_month_start,
                                            Order.created_at < month_start).count()

    new_customers = User.query.filter(User.created_at >= month_start).count()
    total_customers = User.query.filter_by(role='customer').count()

    avg_order_value = db.session.query(func.avg(Order.total))\
        .filter(Order.payment_status == 'paid').scalar() or 0

    rev_growth = ((this_month_rev - last_month_rev) / last_month_rev * 100) if last_month_rev else 0
    order_growth = ((this_month_orders - last_month_orders) / last_month_orders * 100) if last_month_orders else 0

    return jsonify({
        'this_month_revenue': float(this_month_rev),
        'revenue_growth': round(float(rev_growth), 1),
        'this_month_orders': this_month_orders,
        'order_growth': round(float(order_growth), 1),
        'new_customers': new_customers,
        'total_customers': total_customers,
        'avg_order_value': round(float(avg_order_value), 2)
    })

@analytics.route('/api/customer-segments')
@admin_required
def customer_segments():
    # Customers by order count
    vip = db.session.query(func.count()).filter(
        db.session.query(func.count(Order.id)).filter(
            Order.user_id == User.id).correlate(User).as_scalar() >= 5
    ).scalar() or 0

    results = db.session.query(
        User.id,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total).label('lifetime_value')
    ).join(Order, Order.user_id == User.id)\
     .filter(Order.payment_status == 'paid')\
     .group_by(User.id).all()

    segments = {'VIP (5+)': 0, 'Loyal (3-4)': 0, 'Regular (2)': 0, 'New (1)': 0}
    for r in results:
        if r.order_count >= 5:
            segments['VIP (5+)'] += 1
        elif r.order_count >= 3:
            segments['Loyal (3-4)'] += 1
        elif r.order_count == 2:
            segments['Regular (2)'] += 1
        else:
            segments['New (1)'] += 1

    return jsonify({
        'segments': list(segments.keys()),
        'counts': list(segments.values())
    })
