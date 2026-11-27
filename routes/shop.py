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

from helpers import get_product, get_public_inventory
from models import User
from orders import fulfill_checkout

shop = Blueprint("shop", __name__)

@shop.route("/")
def home():
    inventory = get_public_inventory()
    return render_template("index.html", inventory=inventory)


@shop.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if product is None or product.status in ("hidden", "pending"):
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
                    "unit_amount": product.price, 
                },
                "quantity": 1,
            }],
            customer_email=customer_email,
            mode="payment",
            metadata={"product_id": product.id, "user_id": user_id if user_id else ""},
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
    if stripe_session.payment_status != "paid":
        return render_template("error.html", title="Payment Processing", message="Your payment is still being confirmed. We'll record your order as soon as it clears."), 200
    order = fulfill_checkout(stripe_session)
    if order is None:
        return render_template("checkout_failed.html")
    return render_template("checkout_success.html", product_name=order.product.name, price_paid=order.price_paid, user_id=email)
