import os

import stripe

from flask import Blueprint, current_app, request


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

    current_app.logger.info(f"Stripe event: {event['type']}")
    return "", 200