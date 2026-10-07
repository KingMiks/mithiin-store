"""
Mithiin — Flask skeleton
------------------------
This is a starting structure for the real store. Right now everything
runs on MOCK_INVENTORY (fake data) so the site is fully clickable and
testable before the gemstore API and Stripe Connect are wired in.

TODO markers show exactly where real integration will plug in later.
"""

import os

import stripe
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

from extensions import limiter
from models import db
from routes.account import account
from routes.admin import admin
from routes.shop import shop

load_dotenv()  # reads .env locally; on a real host, env vars come from that host's dashboard instead
app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///inventory.db")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "false").lower() == "true"
csrf = CSRFProtect(app)
app.register_blueprint(account)
app.register_blueprint(admin)
app.register_blueprint(shop)
db.init_app(app)
limiter.init_app(app)
Migrate(app, db, render_as_batch=True)

# TODO: replace with a real call to the gemstore API once we have the docs/key.
# For now this is fake data so we can build and test the site's layout and flow.
# requests = url(API_KEY)

@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", title="Not Found", message="We couldn't find that page."), 404

@app.errorhandler(429)
def attempt_limit(error):
    return render_template("error.html", title="Too many attempts", message="You've made too many attempts. Please wait a bit and try again."), 429

@app.errorhandler(500)
def developer_error(error):
    return render_template("error.html", title="Something went wrong", message="We hit a problem on our end. Please try again in a few minutes. If you have any issues please contact us with the email below, thank you."), 500




if __name__ == "__main__":
    app.run(debug=True)