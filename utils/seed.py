import json

def seed_data():
    from extensions import db, bcrypt
    from models import User, Category, Product, Inventory, Banner, Coupon
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.engine)
    if not inspector.has_table('user'):
        return
    if db.session.execute(db.select(User)).first():
        return

    # Admin user
    admin = User(
        name='Swaraj Atelier Admin',
        email='admin@swarajatelier.in',
        password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
        role='admin'
    )
    db.session.add(admin)

    # Demo customer
    customer = User(
        name='Priya Sharma',
        email='priya@example.com',
        password=bcrypt.generate_password_hash('test123').decode('utf-8'),
        role='customer'
    )
    db.session.add(customer)

    # Categories
    categories_data = [
        ('Kurtas & Kurtis', 'kurtas-kurtis', 'Contemporary kurtas for everyday glam'),
        ('Lehengas', 'lehengas', 'Festive lehengas for every celebration'),
        ('Sarees', 'sarees', 'Modern sarees for the new-age woman'),
        ('Salwar Suits', 'salwar-suits', 'Elegant suits for work and festive'),
        ('Co-ord Sets', 'co-ord-sets', 'Trendy ethnic co-ord sets'),
        ('Accessories', 'accessories', 'Jewellery, dupattas & more'),
    ]
    cats = {}
    for name, slug, desc in categories_data:
        c = Category(name=name, slug=slug, description=desc)
        db.session.add(c)
        cats[slug] = c

    db.session.flush()

    # Products
    products_data = [
        {
            'name': 'Gulabi Block Print Kurta', 'price': 1299, 'mrp': 1799, 'cost': 600,
            'category': 'kurtas-kurtis', 'fabric': 'Cotton', 'occasion': 'Casual',
            'sizes': ['XS','S','M','L','XL'], 'colors': ['Pink', 'Ivory'],
            'featured': True,
            'desc': 'Hand block-printed cotton kurta in the iconic Jaipur style. Perfect for your everyday ethnic look.'
        },
        {
            'name': 'Indigo Kantha Stitch Kurta', 'price': 1599, 'mrp': 2299, 'cost': 750,
            'category': 'kurtas-kurtis', 'fabric': 'Cotton', 'occasion': 'Casual',
            'sizes': ['S','M','L','XL'], 'colors': ['Indigo', 'White'],
            'featured': True,
            'desc': 'Hand-stitched Kantha work on pure cotton. A sustainable and stylish choice.'
        },
        {
            'name': 'Anarkali Silk Kurta Set', 'price': 2499, 'mrp': 3499, 'cost': 1100,
            'category': 'kurtas-kurtis', 'fabric': 'Art Silk', 'occasion': 'Festive',
            'sizes': ['XS','S','M','L','XL','XXL'], 'colors': ['Magenta', 'Teal', 'Royal Blue'],
            'featured': True,
            'desc': 'Floor-length Anarkali in lustrous art silk with zari border. Turn heads at every celebration.'
        },
        {
            'name': 'Riya Bridal Lehenga', 'price': 12999, 'mrp': 18999, 'cost': 6000,
            'category': 'lehengas', 'fabric': 'Velvet & Net', 'occasion': 'Bridal',
            'sizes': ['XS','S','M','L','XL'], 'colors': ['Crimson', 'Gold'],
            'featured': True,
            'desc': 'Heavy embroidered bridal lehenga with zari and sequin work. Made for your big day.'
        },
        {
            'name': 'Meera Festive Lehenga', 'price': 4999, 'mrp': 6999, 'cost': 2200,
            'category': 'lehengas', 'fabric': 'Georgette', 'occasion': 'Festive',
            'sizes': ['S','M','L','XL'], 'colors': ['Peach', 'Mint', 'Lavender'],
            'featured': True,
            'desc': 'Light georgette lehenga with delicate thread embroidery. Perfect for sangeet and parties.'
        },
        {
            'name': 'Sundari Chanderi Saree', 'price': 3299, 'mrp': 4499, 'cost': 1500,
            'category': 'sarees', 'fabric': 'Chanderi', 'occasion': 'Festive',
            'sizes': ['Free Size'], 'colors': ['Rose Gold', 'Sky Blue'],
            'featured': False,
            'desc': 'Pure Chanderi saree with woven zari butis and contrast border. Effortless elegance.'
        },
        {
            'name': 'Linen Handloom Saree', 'price': 2199, 'mrp': 2999, 'cost': 950,
            'category': 'sarees', 'fabric': 'Linen', 'occasion': 'Casual',
            'sizes': ['Free Size'], 'colors': ['Nude', 'Charcoal', 'Olive'],
            'featured': False,
            'desc': 'Breathable linen saree for the modern working woman. Sustainable & chic.'
        },
        {
            'name': 'Palazzo Salwar Set', 'price': 1799, 'mrp': 2499, 'cost': 800,
            'category': 'salwar-suits', 'fabric': 'Rayon', 'occasion': 'Casual',
            'sizes': ['XS','S','M','L','XL','XXL'], 'colors': ['Mustard', 'White', 'Red'],
            'featured': False,
            'desc': 'Printed kurta with matching palazzo pants and dupatta. The perfect everyday set.'
        },
        {
            'name': 'Kashmiri Embroidered Suit', 'price': 5499, 'mrp': 7499, 'cost': 2500,
            'category': 'salwar-suits', 'fabric': 'Wool Blend', 'occasion': 'Festive',
            'sizes': ['S','M','L','XL'], 'colors': ['Maroon', 'Forest Green'],
            'featured': True,
            'desc': 'Hand-embroidered Kashmiri motifs on a warm woollen blend. Winter festive perfection.'
        },
        {
            'name': 'Crop Top Co-ord Set', 'price': 2299, 'mrp': 2999, 'cost': 1000,
            'category': 'co-ord-sets', 'fabric': 'Cotton', 'occasion': 'Party',
            'sizes': ['XS','S','M','L'], 'colors': ['Black Gold', 'White Silver'],
            'featured': True,
            'desc': 'Ethnic co-ord with embroidered crop top and flared skirt. Indo-western perfection.'
        },
        {
            'name': 'Mirror Work Sharara Set', 'price': 3499, 'mrp': 4799, 'cost': 1600,
            'category': 'co-ord-sets', 'fabric': 'Georgette', 'occasion': 'Party',
            'sizes': ['S','M','L','XL'], 'colors': ['Fuchsia', 'Cobalt'],
            'featured': True,
            'desc': 'Mirror-work sharara set with matching dupatta. Disco meets desi!'
        },
        {
            'name': 'Kundan Maang Tikka Set', 'price': 599, 'mrp': 899, 'cost': 250,
            'category': 'accessories', 'fabric': 'Metal Alloy', 'occasion': 'Festive',
            'sizes': ['Free Size'], 'colors': ['Gold', 'Silver'],
            'featured': False,
            'desc': 'Kundan-set maang tikka with matching earrings. Complete your bridal look.'
        },
    ]

    for pd in products_data:
        cat = cats[pd['category']]
        slug = pd['name'].lower().replace(' ', '-').replace("'", '')
        product = Product(
            name=pd['name'], slug=slug,
            description=pd['desc'],
            price=pd['price'], mrp=pd['mrp'], cost_price=pd['cost'],
            category_id=cat.id,
            images=json.dumps([
                f'/media/products/{slug}.png',
                f'/media/products/{slug}.png',
            ]),
            sizes=json.dumps(pd['sizes']),
            colors=json.dumps(pd['colors']),
            fabric=pd['fabric'],
            occasion=pd['occasion'],
            is_featured=pd['featured'],
        )
        db.session.add(product)
        db.session.flush()

        for size in pd['sizes']:
            for color in pd['colors']:
                inv = Inventory(product_id=product.id, size=size, color=color, quantity=20)
                db.session.add(inv)

    # Banners
    banners = [
        Banner(title='New Season, New You', subtitle='Shop our festive edit — up to 40% off',
               image_url='/media/banners/banner1.png', link='/products', order=1),
        Banner(title='Bridal Looks 2024', subtitle='Curated for the modern Indian bride',
               image_url='/media/banners/banner2.png', link='/products?category=lehengas', order=2),
        Banner(title='Sustainable Fashion', subtitle='Handcrafted with love for the planet',
               image_url='/media/banners/banner3.png', link='/collections', order=3),
    ]
    for b in banners:
        db.session.add(b)

    # Coupons
    coupons = [
        Coupon(code='WELCOME10', discount_type='percent', discount_value=10,
               min_order=500, max_uses=1000),
        Coupon(code='FLAT200', discount_type='flat', discount_value=200,
               min_order=999, max_uses=500),
        Coupon(code='FESTIVE25', discount_type='percent', discount_value=25,
               min_order=2000, max_uses=200),
    ]
    for c in coupons:
        db.session.add(c)

    db.session.commit()
    print('✅ Seed data loaded successfully!')
