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

import stripe
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from helpers import get_product, get_public_inventory
from models import Order, Product, User, db
from routes.account import account
from routes.admin import admin

load_dotenv()  # reads .env locally; on a real host, env vars come from that host's dashboard instead
app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.register_blueprint(account)
app.register_blueprint(admin)
db.init_app(app)
Migrate(app, db, render_as_batch=True)

# TODO: replace with a real call to the gemstore API once we have the docs/key.
# For now this is fake data so we can build and test the site's layout and flow.
# requests = url(API_KEY)

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
        rows_updated = Product.query.filter(Product.id == product_id, Product.stock > 0).update({"stock": Product.stock - 1})
        if rows_updated == 0:
            db.session.rollback()
            app.logger.warning(f"{session_id} paid for {product_id} when out of stock, refund is needed.")
            return render_template("checkout_failed.html")
        try:
            db.session.add(new_order)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return render_template("checkout_success.html")
    else:
        return render_template("checkout_failed.html")



if __name__ == "__main__":
    app.run(debug=True)
