from flask import Flask, send_from_directory
from extensions import db, bcrypt, login_manager, mail, csrf
import os


def create_app():
    app = Flask(__name__)

    # ---------------- CONFIG ---------------- #
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 'swaraj-atelier-secret-key-2024'
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///swaraj_atelier.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'media/products')
    app.config['MEDIA_FOLDER'] = os.path.join(app.root_path, 'media')

    # Razorpay
    app.config['RAZORPAY_KEY_ID'] = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_key')
    app.config['RAZORPAY_KEY_SECRET'] = os.environ.get('RAZORPAY_KEY_SECRET', 'rzp_test_secret')

    # Mail
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')

    # ---------------- EXTENSIONS ---------------- #
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ---------------- BLUEPRINTS ---------------- #
    from routes.auth import auth
    from routes.shop import shop
    from routes.cart import cart
    from routes.admin import admin
    from routes.payment import payment
    from routes.analytics import analytics

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(shop)
    app.register_blueprint(cart, url_prefix='/cart')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(payment, url_prefix='/payment')
    app.register_blueprint(analytics, url_prefix='/analytics')

    # ---------------- STATIC MEDIA ROUTE ---------------- #
    @app.route('/media/<path:filename>')
    def media(filename):
        return send_from_directory(app.config['MEDIA_FOLDER'], filename)

    # ---------------- DB INIT ---------------- #
    with app.app_context():
        db.create_all()
        from utils.seed import seed_data
        seed_data()

    return app


# ---------------- RUN LOCALLY ---------------- #
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)