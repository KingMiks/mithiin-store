import os

import stripe

from flask import Blueprint, current_app, request
from orders import fulfill_checkout


webhooks = Blueprint("webhooks", __name__)

@webhooks.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        return "", 400
    except stripe.error.SignatureVerificationError:
        return "", 400

    session_obj = event["data"]["object"]
    if event["type"] in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        fulfill_checkout(session_obj)
    elif event["type"] == "checkout.session.async_payment_failed":
        current_app.logger.warning(f"Delayed payment failed for Stripe session {session_obj.id}")

    current_app.logger.info(f"Stripe event: {event['type']}")
    return "", 200