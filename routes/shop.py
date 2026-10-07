from datetime import datetime

import stripe
from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from helpers import get_product, get_public_inventory
from models import Order, Product, User, db

shop = Blueprint("shop", __name__)

@shop.route("/")
def home():
    inventory = get_public_inventory()
    return render_template("index.html", inventory=inventory)


@shop.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if product is None or product.status == "hidden":
        abort(404)
    elif product.status == "coming_soon":
        return render_template("coming_soon.html", product=product)
    else:
        return render_template("product.html", product=product)


@shop.route("/checkout/<int:product_id>")
def checkout(product_id):
    product = get_product(product_id)
    if product is None or product.status != "active":
        abort(404)
    
    customer_email = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = User.query.filter_by(id=user_id).first()
        if user is not None:
            customer_email = user.email
    try:
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
            success_url=url_for("shop.checkout_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("shop.product_detail", product_id=product_id, _external=True),
        )
        return redirect(stripe_session.url, code=303)
    except stripe.error.StripeError as e:
        current_app.logger.warning(f"Stripe checkout failed for product {product_id}: {e}")
        return render_template("error.html", title="Transaction failed", message="Stripe Checkout failed, no transaction was taken. Please try again."), 502

@shop.route("/checkout/success")
def checkout_success():
    session_id = request.args.get("session_id")
    email = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = User.query.filter_by(id=user_id).first()
        if user is not None:
            email = user.email
    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        return render_template("checkout_failed.html")
    if stripe_session.payment_status == "paid":
        existing_order = Order.query.filter_by(stripe_session_id=stripe_session.id).first()
        if existing_order is not None:
            return render_template("checkout_success.html", product_name=existing_order.product.name, price_paid=existing_order.price_paid, user_id=email)

        product_id = int(stripe_session.metadata.get('product_id'))
        product = Product.query.get(product_id)
        new_order = Order(product_id=product.id, quantity=1, price_paid=product.price, time=datetime.now(), user_id=session.get("user_id"), stripe_session_id=stripe_session.id)
        rows_updated = Product.query.filter(Product.id == product_id, Product.stock > 0).update({"stock": Product.stock - 1})
        if rows_updated == 0:
            db.session.rollback()
            current_app.logger.warning(f"{session_id} paid for {product_id} when out of stock, refund is needed.")
            return render_template("checkout_failed.html")
        try:
            db.session.add(new_order)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return render_template("checkout_success.html", product_name=product.name, price_paid=product.price, user_id=email)
    else:
        return render_template("checkout_failed.html")
