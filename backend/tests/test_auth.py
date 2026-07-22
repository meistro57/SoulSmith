# backend/tests/test_auth.py
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_user_signup_and_login_flow():
    uid = str(uuid.uuid4())[:8]
    email = f"user_{uid}@example.com"
    username = f"user_{uid}"

    # 1. Signup a new user
    signup_payload = {
        "email": email,
        "username": username,
        "password": "secretpassword123",
        "display_name": "Mythic Soulkeeper",
    }
    signup_res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 200
    signup_data = signup_res.json()
    assert "access_token" in signup_data
    assert signup_data["user"]["email"] == email
    token = signup_data["access_token"]

    # 2. Get Me using Bearer Token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == username

    # 3. Duplicate email signup attempt
    dup_res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 4. Login with valid credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": email, "password": "secretpassword123"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 5. Login with invalid password
    bad_res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": email, "password": "wrongpassword"},
    )
    assert bad_res.status_code == 401
