from email_validator import EmailNotValidError, validate_email
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import limiter
from helpers import user_required
from models import Order, User, db

account = Blueprint("account", __name__)

@account.route("/register", methods =["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            flash("Please enter a valid email address")
            return redirect(url_for("account.register"))
        user = User.query.filter_by(email=email).first()
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for('account.register'))
        if user is not None:
            flash("Email already registered")
            return redirect(url_for('account.register'))
        else:
            password_hash = generate_password_hash(password)
            new_user = User(email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("shop.home"))
    else:
        return render_template("user/register.html")

@account.route("/user/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email", "")
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash("Invalid email or password")
            return redirect(url_for('account.user_login'))
        else:
            typed_password = request.form.get("password","")
            stored_hash = user.password_hash
            check_password = check_password_hash(stored_hash, typed_password)
            if not check_password:
                flash("Invalid email or password")
                return redirect(url_for('account.user_login'))
            else:
                session["user_id"] = user.id
                return redirect(url_for('shop.home'))
    else:
        return render_template("user/login.html")

@account.route("/user/logout", methods=["GET"])
@user_required
def user_logout():
    session.pop("user_id", None)
    return redirect(url_for('account.user_login'))

@account.route("/account/orders", methods=["GET"])
@user_required
def orders():
    user_id = session.get("user_id")
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.time.desc()).all()
    return render_template("user/orders.html", orders=orders)
    