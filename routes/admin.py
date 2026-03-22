from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import (Product, Category, Inventory, Order, User,
                    Coupon, Banner, Review)
from datetime import datetime
import json
import os
import uuid
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('shop.index'))
        return f(*args, **kwargs)
    return login_required(decorated)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def save_image(file):
    from flask import current_app
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        fname = f'{uuid.uuid4().hex}.{ext}'
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, fname))
        return f'/static/images/products/{fname}'
    return None

# ──────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────

@admin.route('/')
@admin_required
def dashboard():
    from sqlalchemy import func
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total))\
        .filter(Order.payment_status == 'paid').scalar() or 0
    total_customers = User.query.filter_by(role='customer').count()
    total_products = Product.query.filter_by(is_active=True).count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    low_stock = Inventory.query.filter(Inventory.quantity <= Inventory.low_stock_threshold).all()
    return render_template('admin/dashboard.html',
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           total_customers=total_customers,
                           total_products=total_products,
                           recent_orders=recent_orders,
                           low_stock=low_stock)

# ──────────────────────────────────────────
# PRODUCTS
# ──────────────────────────────────────────

@admin.route('/products')
@admin_required
def products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@admin.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        images = []
        for f in request.files.getlist('images'):
            url = save_image(f)
            if url:
                images.append(url)

        name = request.form.get('name')
        slug = name.lower().replace(' ', '-').replace('/', '-') + '-' + uuid.uuid4().hex[:6]
        sizes = request.form.getlist('sizes')
        colors = request.form.getlist('colors')

        product = Product(
            name=name, slug=slug,
            description=request.form.get('description'),
            price=float(request.form.get('price', 0)),
            mrp=float(request.form.get('mrp') or 0),
            cost_price=float(request.form.get('cost_price') or 0),
            category_id=int(request.form.get('category_id')),
            images=json.dumps(images),
            sizes=json.dumps(sizes),
            colors=json.dumps(colors),
            fabric=request.form.get('fabric', ''),
            occasion=request.form.get('occasion', ''),
            is_featured=bool(request.form.get('is_featured')),
        )
        db.session.add(product)
        db.session.flush()

        # Create inventory records
        for size in sizes:
            for color in colors:
                qty = request.form.get(f'stock_{size}_{color}', 0)
                inv = Inventory(product_id=product.id, size=size,
                                color=color, quantity=int(qty))
                db.session.add(inv)

        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, product=None)

@admin.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', product.price))
        product.mrp = float(request.form.get('mrp') or 0)
        product.cost_price = float(request.form.get('cost_price') or 0)
        product.category_id = int(request.form.get('category_id'))
        product.fabric = request.form.get('fabric', '')
        product.occasion = request.form.get('occasion', '')
        product.is_featured = bool(request.form.get('is_featured'))
        product.is_active = bool(request.form.get('is_active', True))

        new_images = []
        for f in request.files.getlist('images'):
            url = save_image(f)
            if url:
                new_images.append(url)
        if new_images:
            existing = product.get_images()
            product.images = json.dumps(existing + new_images)

        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=product, categories=categories)

@admin.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    flash('Product deactivated.', 'info')
    return redirect(url_for('admin.products'))

# ──────────────────────────────────────────
# INVENTORY
# ──────────────────────────────────────────

@admin.route('/inventory')
@admin_required
def inventory():
    items = Inventory.query.join(Product).filter(Product.is_active == True).all()
    return render_template('admin/inventory.html', items=items)

@admin.route('/inventory/update', methods=['POST'])
@admin_required
def update_inventory():
    inv_id = request.form.get('inv_id', type=int)
    qty = request.form.get('quantity', type=int)
    threshold = request.form.get('threshold', type=int)
    inv = Inventory.query.get_or_404(inv_id)
    if qty is not None:
        inv.quantity = qty
    if threshold is not None:
        inv.low_stock_threshold = threshold
    db.session.commit()
    return jsonify({'success': True, 'quantity': inv.quantity})

# ──────────────────────────────────────────
# ORDERS
# ──────────────────────────────────────────

@admin.route('/orders')
@admin_required
def orders():
    status = request.args.get('status', '')
    query = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    orders = query.all()
    return render_template('admin/orders.html', orders=orders, status=status)

@admin.route('/orders/<int:order_id>', methods=['GET', 'POST'])
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        order.status = request.form.get('status', order.status)
        db.session.commit()
        flash('Order status updated!', 'success')
    return render_template('admin/order_detail.html', order=order)

@admin.route('/orders/update-status', methods=['POST'])
@admin_required
def update_order_status():
    order_id = request.form.get('order_id', type=int)
    status = request.form.get('status')
    order = Order.query.get_or_404(order_id)
    order.status = status
    db.session.commit()
    return jsonify({'success': True})

# ──────────────────────────────────────────
# CATEGORIES
# ──────────────────────────────────────────

@admin.route('/categories')
@admin_required
def categories():
    cats = Category.query.all()
    return render_template('admin/categories.html', categories=cats)

@admin.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('name')
    slug = name.lower().replace(' ', '-')
    cat = Category(name=name, slug=slug,
                   description=request.form.get('description', ''))
    db.session.add(cat)
    db.session.commit()
    flash(f'Category "{name}" added!', 'success')
    return redirect(url_for('admin.categories'))

# ──────────────────────────────────────────
# COUPONS
# ──────────────────────────────────────────

@admin.route('/coupons')
@admin_required
def coupons():
    coupons = Coupon.query.order_by(Coupon.id.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

@admin.route('/coupons/add', methods=['POST'])
@admin_required
def add_coupon():
    coupon = Coupon(
        code=request.form.get('code', '').upper(),
        discount_type=request.form.get('discount_type'),
        discount_value=float(request.form.get('discount_value', 0)),
        min_order=float(request.form.get('min_order', 0)),
        max_uses=int(request.form.get('max_uses', 100)),
    )
    db.session.add(coupon)
    db.session.commit()
    flash('Coupon created!', 'success')
    return redirect(url_for('admin.coupons'))

@admin.route('/coupons/toggle/<int:coupon_id>', methods=['POST'])
@admin_required
def toggle_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    return jsonify({'is_active': coupon.is_active})

# ──────────────────────────────────────────
# CUSTOMERS
# ──────────────────────────────────────────

@admin.route('/customers')
@admin_required
def customers():
    users = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
    return render_template('admin/customers.html', users=users)

# ──────────────────────────────────────────
# REVIEWS
# ──────────────────────────────────────────

@admin.route('/reviews')
@admin_required
def reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@admin.route('/reviews/toggle/<int:review_id>', methods=['POST'])
@admin_required
def toggle_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_approved = not review.is_approved
    db.session.commit()
    return jsonify({'is_approved': review.is_approved})
