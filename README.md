# 🎨 Rangmanch — Indo Ethnic Fashion Marketplace

A full-featured Flask e-commerce application for Indo ethnic wear targeting young audiences.

---

## ✨ Features

### 🛍️ Storefront
- Beautiful homepage with auto-advancing hero carousel
- Product listings with filters (category, occasion, price range), search & sorting
- Detailed product pages with image gallery, size/color selectors, and zoom
- Wishlist functionality
- Real-time cart with coupon support
- Multi-step checkout with saved addresses
- Order tracking with status timeline

### 💳 Payments
- **Razorpay** integration (Cards, UPI, NetBanking, EMI, Wallets)
- Cash on Delivery (COD)
- Coupon code engine (% off / flat off)
- Free shipping threshold (₹999+)
- Payment verification via HMAC signature

### 📦 Inventory Management
- Per-product, per-size, per-color stock tracking
- Low stock alerts with configurable thresholds
- Real-time stock deduction on order placement
- Inline stock update from admin panel

### 📊 Business Analytics
- Monthly/weekly/daily revenue charts
- Order status distribution (donut chart)
- Top-selling products (bar chart)
- Category-wise revenue breakdown (pie chart)
- Customer segmentation (VIP, Loyal, Regular, New)
- KPI cards with growth percentages vs prior period

### 👑 Admin Panel
- Dashboard with live stats
- Product CRUD with multi-image upload
- Inventory management with bulk updates
- Order management with one-click status updates
- Coupon creation and toggling
- Customer directory
- Review moderation (approve/hide)

---

## 🚀 Quick Start

### 1. Clone & setup environment
```bash
cd rangmanch
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your Razorpay keys and SMTP credentials
```

### 3. Run the app
```bash
python app.py
```

The app will auto-seed demo data on first run.

### 4. Access the app
- **Store**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
- **Analytics**: http://localhost:5000/analytics

### 5. Demo Credentials
| Role     | Email                    | Password  |
|----------|--------------------------|-----------|
| Admin    | admin@rangmanch.in       | admin123  |
| Customer | priya@example.com        | test123   |

---

## 📁 Project Structure

```
rangmanch/
├── app.py                    # App factory & extensions
├── models/
│   └── __init__.py           # All SQLAlchemy models
├── routes/
│   ├── shop.py               # Storefront routes
│   ├── cart.py               # Cart & checkout routes
│   ├── auth.py               # Login/register/profile
│   ├── admin.py              # Admin CRUD routes
│   ├── payment.py            # Razorpay integration
│   └── analytics.py          # Business analytics API
├── templates/
│   ├── base.html             # Storefront base layout
│   ├── shop/                 # Customer-facing pages
│   │   ├── index.html        # Homepage
│   │   ├── products.html     # Product listing
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── payment.html
│   │   ├── order_success.html
│   │   ├── orders.html
│   │   ├── order_detail.html
│   │   ├── wishlist.html
│   │   └── collections.html
│   ├── admin/                # Admin panel pages
│   │   ├── base.html         # Admin layout with sidebar
│   │   ├── dashboard.html
│   │   ├── analytics.html
│   │   ├── products.html
│   │   ├── product_form.html
│   │   ├── inventory.html
│   │   ├── orders.html
│   │   ├── order_detail.html
│   │   ├── coupons.html
│   │   ├── customers.html
│   │   ├── reviews.html
│   │   └── categories.html
│   └── auth/
│       ├── login.html
│       ├── register.html
│       └── profile.html
├── utils/
│   └── seed.py               # Demo data seeding
├── static/
│   └── images/products/      # Uploaded product images
├── requirements.txt
└── .env.example
```

---

## 🔑 Key Models

| Model      | Purpose                                    |
|------------|--------------------------------------------|
| User       | Customers & admins                         |
| Category   | Product categories (Kurtas, Lehengas etc.) |
| Product    | Products with images, sizes, colors        |
| Inventory  | Per-variant stock levels                   |
| Order      | Orders with shipping + payment info        |
| OrderItem  | Line items per order                       |
| CartItem   | Persistent cart                            |
| Coupon     | Promo codes (flat or % discount)           |
| Wishlist   | Saved products per user                    |
| Review     | Star ratings + comments                    |
| Address    | Multiple shipping addresses per user       |
| Banner     | Homepage carousel slides                   |

---

## 💳 Razorpay Setup

1. Create account at [razorpay.com](https://razorpay.com)
2. Go to **Settings → API Keys** → Generate Test Key
3. Add `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` to `.env`
4. For production, switch from test keys to live keys

---

## 🚢 Production Deployment

### With Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 "app:create_app()"
```

### Switch to PostgreSQL
```bash
pip install psycopg2-binary
# Update DATABASE_URL in .env:
# DATABASE_URL=postgresql://user:pass@host/dbname
```

### Static files
Use Nginx to serve `/static/` directly for better performance.

---

## 🎨 Customisation

| Thing to change            | Where                          |
|----------------------------|--------------------------------|
| Brand name & logo          | `templates/base.html`          |
| Brand colours              | `:root` CSS vars in base.html  |
| Homepage banners           | Admin → seed_data or DB        |
| Featured products          | Admin → Products → ✔ Featured  |
| Coupon codes               | Admin → Coupons                |
| Free shipping threshold    | `routes/cart.py` (line ~30)    |
| Low stock threshold        | Admin → Inventory              |
| Email templates            | `utils/` (extend as needed)    |

---

Made with ❤️ for Indian fashion.
