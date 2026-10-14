from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "change-this-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sales_insight.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.static_folder, "uploads").mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        from .models import User, Product, Sale
        db.create_all()
        seed_data()

    return app

def seed_data():
    from .models import User, Product, Sale
    from werkzeug.security import generate_password_hash
    from datetime import date, timedelta
    import random

    if User.query.count() == 0:
        db.session.add_all([
            User(name="System Administrator", email="admin@demo.com",
                 password_hash=generate_password_hash("admin123"), role="admin"),
            User(name="Demo User", email="user@demo.com",
                 password_hash=generate_password_hash("user123"), role="user")
        ])
        db.session.commit()

    if Product.query.count() == 0:
        products = [
            ("Laptop Pro 14", "Electronics", 65000, 52000),
            ("Smartphone X", "Electronics", 32000, 25000),
            ("Wireless Headphones", "Accessories", 4500, 2800),
            ("Office Chair", "Furniture", 8500, 6000),
            ("Mechanical Keyboard", "Accessories", 5200, 3400),
            ("Monitor 24", "Electronics", 14500, 10500),
        ]
        for name, cat, price, cost in products:
            db.session.add(Product(name=name, category=cat, unit_price=price, unit_cost=cost))
        db.session.commit()

    if Sale.query.count() == 0:
        products = Product.query.all()
        regions = ["North", "South", "East", "West"]
        random.seed(42)
        start = date(2025, 1, 1)
        rows = []
        for i in range(240):
            p = random.choice(products)
            d = start + timedelta(days=random.randint(0, 485))
            qty = random.randint(1, 8)
            rows.append(Sale(date=d, product_id=p.id, quantity=qty,
                             unit_price=p.unit_price, unit_cost=p.unit_cost,
                             region=random.choice(regions)))
        db.session.add_all(rows)
        db.session.commit()
