from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    cut = db.Column(db.String(200), nullable=False)
    carat = db.Column(db.Float())
    price = db.Column(db.Integer())
    stock = db.Column(db.Integer())
    image = db.Column(db.String(200))
    status = db.Column(db.String(200), default="coming_soon")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    quantity = db.Column(db.Integer())
    price_paid = db.Column(db.Integer())
    time = db.Column(db.DateTime())

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
