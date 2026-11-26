from decimal import Decimal
from functools import wraps

from flask import (
    redirect,
    session,
    url_for,
)

from models import Product, db, Order
from datetime import datetime
import stripe

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("is_admin", False):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("admin.login"))
    return wrapper

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_id", False):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("account.user_login"))
    return wrapper

def get_inventory():
    # TODO: once we have the gemstore API docs and key, replace this with real API calls.
    # For now it reads from our own SQLite database.
    return Product.query.all()

def get_public_inventory():
    return [product for product in get_inventory() if product.status in ["active", "coming_soon"]]


def get_product(product_id):
    """TODO: swap for a real single-item API call once available."""
    return db.session.get(Product, product_id)

def to_cents(amount):
    return int(Decimal(str(amount)) * 100)

def format_price(amount):
    dollars, cents = divmod(amount, 100)
    return f"${dollars:,}.{cents:02d}"

def cents_to_dollars(amount):
    dollars, cents = divmod(amount, 100)
    return f"{dollars}.{cents:02d}"

def build_order(product, stripe_session_id, user_id):
    return Order(product_id=product.id, quantity=1, price_paid=product.price, time=datetime.now(), user_id=user_id, stripe_session_id=stripe_session_id, supplier_price=product.supplier_price)