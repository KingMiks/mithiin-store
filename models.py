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