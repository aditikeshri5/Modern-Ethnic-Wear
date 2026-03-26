from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from models import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '')
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('auth.register'))
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password=hashed, phone=phone)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to Swaraj Atelier, {name}! 🎉', 'success')
        return redirect(url_for('shop.index'))
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            flash('Welcome back! ✨', 'success')
            return redirect(next_page or url_for('shop.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('shop.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import Address, Order
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        current_user.phone = request.form.get('phone', current_user.phone)
        db.session.commit()
        flash('Profile updated!', 'success')
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    return render_template('auth/profile.html', addresses=addresses, orders=orders)

@auth.route('/address/add', methods=['POST'])
@login_required
def add_address():
    from models import Address
    addr = Address(
        user_id=current_user.id,
        name=request.form.get('name'),
        phone=request.form.get('phone'),
        line1=request.form.get('line1'),
        line2=request.form.get('line2', ''),
        city=request.form.get('city'),
        state=request.form.get('state'),
        pincode=request.form.get('pincode'),
        is_default=bool(request.form.get('is_default'))
    )
    if addr.is_default:
        Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
    db.session.add(addr)
    db.session.commit()
    flash('Address added!', 'success')
    return redirect(url_for('auth.profile'))
