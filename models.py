from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    shape = db.Column(db.String(200), nullable=False)
    carat = db.Column(db.Float())
    price = db.Column(db.Integer()) # in cents, the shopper price (after markup)
    supplier_price = db.Column(db.Integer()) # in cents, holds gemstore price.
    stock = db.Column(db.Integer())
    image = db.Column(db.String(500))
    status = db.Column(db.String(200), default="coming_soon")
    stone_no = db.Column(db.String(50), unique=True)
    cut = db.Column(db.String(200))
    color = db.Column(db.String(200))
    clarity = db.Column(db.String(200))
    polish = db.Column(db.String(200))
    symmetry = db.Column(db.String(200))
    lab = db.Column(db.String(200))
    report_no = db.Column(db.String(200))
    certificate_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    quantity = db.Column(db.Integer())
    price_paid = db.Column(db.Integer()) # in cents, the shopper price (after markup)
    supplier_price = db.Column(db.Integer()) # in cents, the gemstore's price at the time of sale.
    time = db.Column(db.DateTime())
    product = db.relationship("Product")
    user = db.relationship("User")
    stripe_session_id = db.Column(db.String(200), unique=True)
    payment_status = db.Column(db.String(30))       # "paid", later "refunded"
    fulfillment_status = db.Column(db.String(30))   # "unfulfilled", "confirmed", "shipped", "delivered", "cancelled"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
