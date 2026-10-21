from models import User

def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200

def test_missing_page_gives_404(client):
    response = client.get("/nothing-here")
    assert response.status_code == 404
    assert b"Not Found" in response.data

def test_register_rejects_short_password(client):
    response = client.post("/register", data={"email": "new@example.com", "password": "short"}, follow_redirects=True)
    assert b"at least 8 characters" in response.data
    assert User.query.filter_by(email="new@example.com").first() is None

def test_register_creates_user(client):
    response = client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    assert response.status_code == 200
    assert User.query.filter_by(email="new@example.com").first() is not None
    assert User.password_hash != "longenough123"

def test_register_rejects_duplciates_email(client):
    response = client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    response = client.post("/register", data={"email": "new@example.com", "password":"longenough123"}, follow_redirects=True)
    assert b"Email already registered" in response.data
    assert User.query.filter_by(email ="new@example.com").count()==1

def test_register_is_rate_imited(client):
    for _ in range(5):
        response = client.post("/register", data={"email": "new@example.com", "password":"short"}, follow_redirects=True)
    response = client.post("/register", data={"email": "new@example.com", "password":"short"}, follow_redirects=True)    
    assert response.status_code == 429
    assert b"Too many attempts" in response.data