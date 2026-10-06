import os

from dotenv import load_dotenv
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from extensions import limiter
from helpers import admin_required, get_inventory
from models import Order, Product, db

load_dotenv()  # reads .env locally; on a real host, env vars come from that host's dashboard instead

admin = Blueprint("admin", __name__)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

@admin.route("/admin/login", methods = ["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST" and ADMIN_PASSWORD and request.form.get("password") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin.admin_dashboard"))
    elif request.method == "POST" and ADMIN_PASSWORD and request.form.get("password") != ADMIN_PASSWORD:
        flash("Incorrect password.")
        return redirect(url_for("admin.login"))
    else:
        return render_template("admin/login.html")

@admin.route("/admin")
@admin_required
def admin_dashboard():
    inventory = get_inventory()
    return render_template("admin/dashboard.html", inventory=inventory)

@admin.route("/admin/add", methods = ["GET", "POST"])
@admin_required
def admin_add():
    if request.method == "POST":
        new_product = Product(name=request.form.get("name"), cut=request.form.get("cut"), carat= float(request.form.get("carat")),
                          price= int(request.form.get("price")), stock= int(request.form.get("stock")), image=request.form.get("image"), status = request.form.get("status"))
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("admin.admin_dashboard"))
    return render_template("admin/form.html")

@admin.route("/admin/edit/<int:product_id>", methods = ["GET", "POST"])
@admin_required
def admin_edit(product_id):
    product = Product.query.get(product_id)
    if product is None:
            abort(404)
    if request.method == "POST":
        product.name = request.form.get("name")
        product.cut = request.form.get("cut")
        product.carat = float(request.form.get("carat"))
        product.price = int(request.form.get("price"))
        product.stock = int(request.form.get("stock"))
        product.image = request.form.get("image")
        product.status = request.form.get("status")
        db.session.commit()
        return redirect(url_for("admin.admin_dashboard"))
    return render_template("admin/form.html", product=product)

@admin.route("/admin/logout", methods = ["GET"])
@admin_required
def admin_logout():
        session.clear()
        return redirect(url_for("admin.login"))

@admin.route("/admin/delete/<int:product_id>", methods = ["POST"])
@admin_required
def admin_delete(product_id):
    product = Product.query.get(product_id)
    if product is None:
        abort(404)
    if Order.query.filter_by(product_id=product_id).first() is not None:
        flash("Orders of this item exist. Cannot delete this item")
    else:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for("admin.admin_dashboard"))