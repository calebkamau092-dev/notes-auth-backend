def signup(client, username="alice", password="password123", confirmation=None):
    return client.post("/signup", json={
        "username": username,
        "password": password,
        "password_confirmation": password if confirmation is None else confirmation,
    })


# ---------- Signup ----------

def test_signup_creates_user_and_logs_in(client):
    response = signup(client)
    assert response.status_code == 201
    assert response.get_json() == {"id": 1, "username": "alice"}
    assert client.get("/check_session").status_code == 200


def test_signup_never_returns_password(client):
    body = signup(client).get_json()
    assert "password" not in body and "_password_hash" not in body


def test_signup_rejects_mismatched_passwords(client):
    response = signup(client, confirmation="different123")
    assert response.status_code == 422
    assert isinstance(response.get_json()["errors"], list)


def test_signup_rejects_short_password(client):
    assert signup(client, password="short").status_code == 422


def test_signup_rejects_duplicate_username(client):
    signup(client)
    client.delete("/logout")
    response = signup(client)
    assert response.status_code == 422
    assert response.get_json()["errors"] == ["Username is already taken."]


# ---------- Login ----------

def test_login_success(client, alice):
    response = client.post("/login", json={"username": "alice", "password": "password123"})
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


def test_login_wrong_password(client, alice):
    response = client.post("/login", json={"username": "alice", "password": "nope"})
    assert response.status_code == 401
    assert response.get_json() == {"errors": ["Invalid username or password."]}


def test_login_unknown_user(client):
    response = client.post("/login", json={"username": "ghost", "password": "password123"})
    assert response.status_code == 401


# ---------- Check session ----------

def test_check_session_when_logged_out(client):
    response = client.get("/check_session")
    assert response.status_code == 401
    assert response.get_json() == {}


def test_check_session_when_logged_in(logged_in_client):
    response = logged_in_client.get("/check_session")
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


# ---------- Logout ----------

def test_logout(logged_in_client):
    assert logged_in_client.delete("/logout").status_code == 204
    assert logged_in_client.get("/check_session").status_code == 401


def test_logout_when_not_logged_in(client):
    assert client.delete("/logout").status_code == 401