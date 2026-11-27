from flask import current_app
from sqlalchemy.exc import IntegrityError

from helpers import build_order
from models import Order, Product, db


def fulfill_checkout(stripe_session):
    """Create the order for a paid Stripe Checkout Session. Safe to call twice."""
    # 1. Not paid yet? Do Nothing.
    if stripe_session.payment_status != "paid":
        return None

    # 2. Already have an order for this session? Return it (this is what makes a 2nd call harmless).
    existing = Order.query.filter_by(stripe_session_id=stripe_session.id).first()

    if existing is not None:
        return existing

    # 3. Read product and user from the metadata.
    raw_product = stripe_session.metadata.get("product_id")
    if not raw_product:
        current_app.logger.warning(f"Stripe session {stripe_session.id} has no product_id in metadata; skipped.")
        return None
    product_id = int(raw_product)
    raw_user = stripe_session.metadata.get("user_id", "")
    user_id = int(raw_user) if raw_user else None
    
    #4. Product deleted mid-payment? Log a refund and stop.
    product = db.session.get(Product, product_id)
    if product is None:
        current_app.logger.warning(f"REFUND NEEDED: Stripe session {stripe_session.id} paid for product {product_id}, but the product no longer exists.")
        return None
    new_order = build_order(product=product, stripe_session_id=stripe_session.id, user_id=user_id)
    rows_updated = Product.query.filter(Product.id == product_id, Product.stock > 0).update({"stock": Product.stock - 1})
    if rows_updated == 0:
        db.session.rollback()
        current_app.logger.warning(f"REFUND NEEDED: Stripe session {stripe_session.id} paid for product {product_id}, but it was out of stock.")
        return None
    try:
        db.session.add(new_order)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return Order.query.filter_by(stripe_session_id=stripe_session.id).first()
    return new_order