from functools import wraps

from flask import (
    redirect,
    session,
    url_for,
)

from models import Product


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
    """TODO: swap this out for a real gemstore API call, e.g.:
    response = requests.get(GEMSTORE_API_URL + "/inventory", headers={"Authorization": f"Bearer {API_KEY}"})
    return response.json()
    """
    return Product.query.all()

def get_public_inventory():
    return [product for product in get_inventory() if product.status in ["active", "coming_soon"]]


def get_product(product_id):
    """TODO: swap for a real single-item API call once available."""
    return Product.query.get(product_id)
