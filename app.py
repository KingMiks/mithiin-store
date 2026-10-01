"""
Mithiin — Flask skeleton
------------------------
This is a starting structure for the real store. Right now everything
runs on MOCK_INVENTORY (fake data) so the site is fully clickable and
testable before the gemstore API and Stripe Connect are wired in.

TODO markers show exactly where real integration will plug in later.
"""

import os
from functools import wraps

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

from models import Product, db

load_dotenv()  # reads .env locally; on a real host, env vars come from that host's dashboard instead
app = Flask(__name__)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
db.init_app(app)
with app.app_context():
    db.create_all()

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
    return [product for product in get_inventory() if product.status == "active"]


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
    if product is None or product.status != "active":
        abort(404)
    return render_template("product.html", product=product)


@app.route("/checkout/<int:product_id>")
def checkout(product_id):
    product = get_product(product_id)
    if product is None or product.status != "active":
        abort(404)
    # TODO: replace this stub with real Stripe Connect checkout session creation.
    # This is where the payment split between us and the gemstore gets set up.
    return render_template("checkout.html", product=product)

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

if __name__ == "__main__":
    app.run(debug=True)
