from models import User, db, Product, Order
from datetime import datetime
def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200

def test_missing_page_gives_404(client):
    response = client.get("/nothing-here")
    assert response.status_code == 404
    assert b"Homepage" in response.data

def test_register_rejects_short_password(client):
    response = client.post("/register", data={"email": "new@example.com", "password": "short"}, follow_redirects=True)
    assert b"at least 8 characters" in response.data
    assert User.query.filter_by(email="new@example.com").first() is None

def test_register_creates_user(client):
    response = client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    assert response.status_code == 200
    assert User.query.filter_by(email="new@example.com").first() is not None
    user = User.query.filter_by(email="new@example.com").first()
    assert user.password_hash != "longenough123"

def test_register_rejects_duplicates_email(client):
    response = client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    response = client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    assert b"Email already registered" in response.data
    assert User.query.filter_by(email ="new@example.com").count()==1

def test_register_is_rate_limited(client):
    for _ in range(5):
        response = client.post("/register", data={"email": "new@example.com", "password":"short"}, follow_redirects=True)
    response = client.post("/register", data={"email": "new@example.com", "password":"short"}, follow_redirects=True)    
    assert response.status_code == 429
    assert b"Too many attempts" in response.data

def test_account_redirects_when_logged_out(client):
    response = client.get("/account")
    assert response.status_code == 302
    assert "/user/login" in response.location

def test_login_rejects_wrong_password(client):
    client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    response = client.post("/user/login", data={"email": "new@example.com", "password":"short"}, follow_redirects=True)
    assert b"Invalid email or password" in response.data
    assert b"Logout" not in response.data

def test_admin_pages_redirect_when_logged_out(client):
    response = client.get("/admin")
    assert response.status_code == 302
    assert "/admin/login" in response.location
    response = client.get("/admin/orders")
    assert response.status_code == 302
    assert "/admin/login" in response.location

def test_edit_missing_product_gives_404(client):
    with client.session_transaction() as sess:
        sess["is_admin"] = True
    response = client.get("/admin")
    assert response.status_code == 200
    response = client.get("/admin/edit/<int:product_id>")
    assert response.status_code == 404

def test_deleting_product_with_orders_is_refused(client):
    product = Product(name="diamond", cut="princess", carat=24, price=100, stock=10, image="", status="active")
    db.session.add(product)
    db.session.commit()
    order = Order(product_id = product.id, quantity=1, price_paid=100, time=datetime.now(), stripe_session_id ="2xd21")
    db.session.add(order)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["is_admin"] = True
    response = client.post(f"/admin/delete/{product.id}", follow_redirects=True)
    assert db.session.get(Product, product.id) is not None
    assert b"Orders of this item exist. Cannot delete this item" in response.data

def test_active_product_page_loads(client):
    product = Product(name="zzqtestgem", cut="princess", carat=24, price=100, stock=10, image="", status="active")
    db.session.add(product)
    db.session.commit()
    response = client.get(f"/product/{product.id}")
    assert response.status_code == 200
    assert b"zzqtestgem" in response.data

def test_coming_soon_product_cannot_be_bought(client):
    product = Product(name="zzqtestgem", cut="princess", carat=24, price=100, stock=10, image="", status="coming_soon")
    db.session.add(product)
    db.session.commit()
    response = client.get(f"/checkout/{product.id}")
    assert response.status_code == 404

def test_stock_not_shown_to_shoppers(client):
    product = Product(name="awefacweftestgem", cut="princess", carat=24, price=100, stock=7342, image="", status="active")
    db.session.add(product)
    db.session.commit()
    response = client.get(f"/product/{product.id}")
    assert response.status_code == 200
    assert b"7342" not in response.data