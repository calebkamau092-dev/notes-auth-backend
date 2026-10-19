from extensions import db
from models import Note


def add_notes(user, count):
    for i in range(count):
        db.session.add(Note(title=f"Note {i}", content="Some content", user=user))
    db.session.commit()


# ---------- Auth protection ----------

def test_notes_require_login(client, bobs_note):
    assert client.get("/notes").status_code == 401
    assert client.post("/notes", json={"title": "x", "content": "y"}).status_code == 401
    assert client.get(f"/notes/{bobs_note.id}").status_code == 401
    assert client.patch(f"/notes/{bobs_note.id}", json={"title": "x"}).status_code == 401
    assert client.delete(f"/notes/{bobs_note.id}").status_code == 401


def test_cannot_view_edit_or_delete_another_users_note(logged_in_client, bobs_note):
    url = f"/notes/{bobs_note.id}"
    assert logged_in_client.get(url).status_code == 403
    assert logged_in_client.patch(url, json={"title": "Hacked"}).status_code == 403
    assert logged_in_client.delete(url).status_code == 403
    assert db.session.get(Note, bobs_note.id).title == "Bob's secret"


def test_index_only_shows_own_notes(logged_in_client, alice, bobs_note):
    add_notes(alice, 2)
    data = logged_in_client.get("/notes").get_json()
    assert data["total"] == 2
    assert all(note["user_id"] == alice.id for note in data["notes"])


# ---------- Create ----------

def test_create_note(logged_in_client, alice):
    response = logged_in_client.post("/notes", json={"title": "Groceries", "content": "Milk, eggs"})
    data = response.get_json()
    assert response.status_code == 201
    assert data["title"] == "Groceries"
    assert data["pinned"] is False
    assert data["user_id"] == alice.id


def test_create_note_rejects_user_id_in_body(logged_in_client, alice, bob):
    """A user can't create a note on someone else's account."""
    response = logged_in_client.post(
        "/notes", json={"title": "Sneaky", "content": "x", "user_id": bob.id}
    )
    assert response.status_code == 422


def test_create_note_validation(logged_in_client):
    response = logged_in_client.post("/notes", json={"title": ""})
    assert response.status_code == 422
    errors = response.get_json()["errors"]
    assert any("title" in e for e in errors)
    assert any("content" in e for e in errors)


# ---------- Read ----------

def test_get_own_note(logged_in_client, alice):
    add_notes(alice, 1)
    note_id = Note.query.first().id
    response = logged_in_client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Note 0"


def test_get_missing_note(logged_in_client):
    assert logged_in_client.get("/notes/999").status_code == 404


# ---------- Update ----------

def test_patch_note(logged_in_client, alice):
    add_notes(alice, 1)
    note_id = Note.query.first().id
    response = logged_in_client.patch(f"/notes/{note_id}", json={"pinned": True})
    data = response.get_json()
    assert response.status_code == 200
    assert data["pinned"] is True
    assert data["title"] == "Note 0"


def test_patch_note_validation(logged_in_client, alice):
    add_notes(alice, 1)
    note_id = Note.query.first().id
    response = logged_in_client.patch(f"/notes/{note_id}", json={"title": ""})
    assert response.status_code == 422
    assert db.session.get(Note, note_id).title == "Note 0"


# ---------- Delete ----------

def test_delete_note(logged_in_client, alice):
    add_notes(alice, 1)
    note_id = Note.query.first().id
    assert logged_in_client.delete(f"/notes/{note_id}").status_code == 204
    assert logged_in_client.get(f"/notes/{note_id}").status_code == 404


# ---------- Pagination ----------

def test_pagination(logged_in_client, alice):
    add_notes(alice, 25)
    page1 = logged_in_client.get("/notes?page=1&per_page=10").get_json()
    page3 = logged_in_client.get("/notes?page=3&per_page=10").get_json()
    assert len(page1["notes"]) == 10
    assert page1["total"] == 25
    assert page1["pages"] == 3
    assert len(page3["notes"]) == 5


def test_pagination_defaults_and_limits(logged_in_client, alice):
    add_notes(alice, 3)
    data = logged_in_client.get("/notes").get_json()
    assert data["page"] == 1 and data["per_page"] == 10
    assert logged_in_client.get("/notes?per_page=1000").get_json()["per_page"] == 50
    assert logged_in_client.get("/notes?page=0").status_code == 400


def test_pinned_notes_come_first(logged_in_client, alice):
    add_notes(alice, 3)
    pinned = Note.query.order_by(Note.id).first()
    pinned.pinned = True
    db.session.commit()
    first = logged_in_client.get("/notes").get_json()["notes"][0]
    assert first["id"] == pinned.id