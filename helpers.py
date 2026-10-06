from functools import wraps
from flask import session, redirect, url_for

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("is_admin", False):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    return wrapper

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_id", False):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("account.user_login"))
    return wrapper