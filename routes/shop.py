from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import Product, Category, Banner, Review, Wishlist
from sqlalchemy import or_

shop = Blueprint('shop', __name__)

@shop.route('/')
def index():
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.order).all()
    featured = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    categories = Category.query.filter_by(is_active=True).all()
    new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template('shop/index.html', banners=banners, featured=featured,
                           categories=categories, new_arrivals=new_arrivals)

@shop.route('/collections')
def collections():
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('shop/collections.html', categories=categories)

@shop.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    search = request.args.get('q', '')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 100000, type=float)
    occasion = request.args.get('occasion', '')

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if search:
        query = query.filter(or_(
            Product.name.ilike(f'%{search}%'),
            Product.description.ilike(f'%{search}%'),
            Product.fabric.ilike(f'%{search}%'),
            Product.occasion.ilike(f'%{search}%')
        ))

    if occasion:
        query = query.filter(Product.occasion.ilike(f'%{occasion}%'))

    query = query.filter(Product.price >= min_price, Product.price <= max_price)

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        query = query.order_by(Product.id.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()

    return render_template('shop/products.html', pagination=pagination,
                           products=pagination.items, categories=categories,
                           current_category=category_slug, sort=sort,
                           search=search, occasion=occasion)

@shop.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter_by(category_id=product.category_id, is_active=True)\
        .filter(Product.id != product.id).limit(4).all()
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
    return render_template('shop/product_detail.html', product=product,
                           related=related, in_wishlist=in_wishlist)

@shop.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash('You have already reviewed this product.', 'warning')
        return redirect(url_for('shop.product_detail', slug=product.slug))
    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        rating=int(request.form.get('rating', 5)),
        comment=request.form.get('comment', '')
    )
    db.session.add(review)
    db.session.commit()
    flash('Review submitted! Thank you. ✨', 'success')
    return redirect(url_for('shop.product_detail', slug=product.slug))

@shop.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        status = 'removed'
    else:
        db.session.add(Wishlist(user_id=current_user.id, product_id=product_id))
        status = 'added'
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': status})
    return redirect(request.referrer or url_for('shop.index'))

@shop.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('shop/wishlist.html', items=items)

@shop.route('/search')
def search():
    q = request.args.get('q', '')
    return redirect(url_for('shop.products', q=q))
