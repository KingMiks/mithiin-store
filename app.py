"""
Mithiin — Flask skeleton
------------------------
This is a starting structure for the real store. Right now everything
runs on MOCK_INVENTORY (fake data) so the site is fully clickable and
testable before the gemstore API and Stripe Connect are wired in.

TODO markers show exactly where real integration will plug in later.
"""

import os
from datetime import datetime
from functools import wraps

import stripe
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash

from models import Order, Product, User, db

load_dotenv()  # reads .env locally; on a real host, env vars come from that host's dashboard instead
app = Flask(__name__)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
db.init_app(app)
Migrate(app, db, render_as_batch=True)

# TODO: replace with a real call to the gemstore API once we have the docs/key.
# For now this is fake data so we can build and test the site's layout and flow.
# requests = url(API_KEY)

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


@app.route("/")
def home():
    inventory = get_public_inventory()
    return render_template("index.html", inventory=inventory)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if product is None or product.status == "hidden":
        abort(404)
    elif product.status == "coming_soon":
        return render_template("coming_soon.html", product=product)
    else:
        return render_template("product.html", product=product)


@app.route("/checkout/<int:product_id>")
def checkout(product_id):
    product = get_product(product_id)
    if product is None or product.status != "active":
        abort(404)
    
    customer_email = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = User.query.filter_by(id=user_id).first()
        customer_email = user.email

    stripe_session = stripe.checkout.Session.create(
        
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": product.name},
                "unit_amount": product.price * 100, 
            },
            "quantity": 1,
        }],
        customer_email=customer_email,
        mode="payment",
        metadata={"product_id": product.id},
        success_url=url_for("checkout_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=url_for("checkout", product_id=product_id, _external=True),
    )
    return redirect(stripe_session.url, code=303)

@app.route("/admin/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST" and ADMIN_PASSWORD and request.form.get("password") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin_dashboard"))
    elif request.method == "POST" and ADMIN_PASSWORD and request.form.get("password") != ADMIN_PASSWORD:
        flash("Incorrect password.")
        return redirect(url_for("login"))
    else:
        return render_template("admin/login.html")

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("is_admin", False):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    return wrapper

@app.route("/admin")
@admin_required
def admin_dashboard():
    inventory = get_inventory()
    return render_template("admin/dashboard.html", inventory=inventory)

@app.route("/admin/add", methods = ["GET", "POST"])
@admin_required
def admin_add():
    if request.method == "POST":
        new_product = Product(name=request.form.get("name"), cut=request.form.get("cut"), carat= float(request.form.get("carat")),
                          price= int(request.form.get("price")), stock= int(request.form.get("stock")), image=request.form.get("image"), status = request.form.get("status"))
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/form.html")

@app.route("/admin/edit/<int:product_id>", methods = ["GET", "POST"])
@admin_required
def admin_edit(product_id):
    product = Product.query.get(product_id)
    if request.method == "POST":
        product.name = request.form.get("name")
        product.cut = request.form.get("cut")
        product.carat = float(request.form.get("carat"))
        product.price = int(request.form.get("price"))
        product.stock = int(request.form.get("stock"))
        product.image = request.form.get("image")
        product.status = request.form.get("status")
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/form.html", product=product)

@app.route("/admin/logout", methods = ["GET"])
@admin_required
def admin_logout():
        session.clear()
        return redirect(url_for("login"))

@app.route("/admin/delete/<int:product_id>", methods = ["POST"])
@admin_required
def admin_delete(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/checkout/success")
def checkout_success():
    session_id = request.args.get("session_id")
    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        return render_template("checkout_failed.html")
    if stripe_session.payment_status == "paid":
        existing_order = Order.query.filter_by(stripe_session_id=stripe_session.id).first()
        if existing_order is not None:
            return render_template("checkout_success.html")

        product_id = int(stripe_session.metadata.get('product_id'))
        product = Product.query.get(product_id)
        new_order = Order(product_id=product.id, quantity=1, price_paid=product.price, time=datetime.now(), user_id=session.get("user_id"), stripe_session_id=stripe_session.id)
        product.stock -= new_order.quantity
        db.session.add(new_order)
        db.session.commit()
        return render_template("checkout_success.html")
    else:
        return render_template("checkout_failed.html")

@app.route("/register", methods =["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        password = request.form.get("password")
        if user is not None:
            flash("Email already registered")
            return redirect(url_for('register'))
        else:
            password_hash = generate_password_hash(password)
            new_user = User(email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("home"))
    else:
        return render_template("user/register.html")

@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash("Invalid email or password")
            return redirect(url_for('user_login'))
        else:
            typed_password = request.form.get("password")
            stored_hash = user.password_hash
            check_password = check_password_hash(stored_hash, typed_password)
            if not check_password:
                flash("Invalid email or password")
                return redirect(url_for('user_login'))
            else:
                session["user_id"] = user.id
                return redirect(url_for('home'))
    else:
        return render_template("user/login.html")

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_id", False):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("user_login"))
    return wrapper

@app.route("/user/logout", methods=["GET"])
@user_required
def user_logout():
    session.pop("user_id", None)
    return redirect(url_for('user_login'))

@app.route("/account/orders", methods=["GET"])
@user_required
def orders():
    user_id = session.get("user_id")
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.time.desc()).all()
    return render_template("user/orders.html", orders=orders)
    


if __name__ == "__main__":
    app.run(debug=True)
