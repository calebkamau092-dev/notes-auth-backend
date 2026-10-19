# Notes API: Full Auth Flask Backend

A secure Flask REST API for a personal notes app. Users sign up, log in and manage their **own** notes. Every note route requires login, and users can never view, edit or delete another user's notes.

Authentication uses **Flask sessions** (a signed cookie), matching the provided [session-based React client](https://github.com/learn-co-curriculum/flask-c10-summative-lab-sessions-and-jwt-clients/tree/main/client-with-sessions).

Built with Flask, Flask-RESTful, Flask-SQLAlchemy, Flask-Migrate, Flask-Bcrypt and Marshmallow.

## Features

- Sign up, log in, check session and log out
- Passwords hashed with **bcrypt**; the hash can never be read back from the model
- Unique usernames (database constraint + validation)
- Full CRUD for notes, with **pagination** on the index route
- Notes are scoped to their owner: other users get `403 Forbidden`
- Validation on both the schema (Marshmallow) and model (`@validates`) level
- Faker seed data and a 33-test pytest suite

## Project Structure

```
notes-auth-backend/
├── Pipfile / Pipfile.lock
├── pytest.ini
├── server/
│   ├── app.py              # App factory, config, route registration
│   ├── extensions.py       # db, bcrypt and migrate instances
│   ├── models.py           # User and Note models
│   ├── schemas.py          # Marshmallow schemas and validation
│   ├── seed.py             # Example users and notes (Faker)
│   ├── resources/
│   │   ├── auth.py         # Signup, Login, CheckSession, Logout + login_required
│   │   └── notes.py        # Note CRUD with pagination and ownership checks
│   └── migrations/         # Flask-Migrate (Alembic) migrations
└── tests/                  # pytest suite
```

## Data Models

| Model | Fields |
|-------|--------|
| **User** | `id`, `username` (unique, 3–30 characters), `_password_hash` (bcrypt) |
| **Note** | `id`, `title` (1–100 characters), `content`, `pinned` (bool), `created_at`, `updated_at`, `user_id` (foreign key to User) |

A user has many notes. Deleting a user deletes their notes.

## Installation

Requires Python 3.12 and [Pipenv](https://pipenv.pypa.io/).

```bash
git clone https://github.com/calebkamau092-dev/notes-auth-backend.git
cd notes-auth-backend

pipenv install
pipenv shell
```

Create the database and load example data:

```bash
cd server
flask db upgrade head
python seed.py
```

The seed file creates three users, **alice**, **bob** and **carol**, all with the password **`password123`**, and 12–15 notes each. It clears existing data first, so you can rerun it any time.

## Running the App

From the `server/` directory:

```bash
python app.py
```

The API runs at `http://127.0.0.1:5555`, the port the provided frontend's proxy expects.

For anything other than local development, set a real secret key first:

```bash
export SECRET_KEY="a-long-random-string"
```

### Using the provided frontend

```bash
git clone https://github.com/learn-co-curriculum/flask-c10-summative-lab-sessions-and-jwt-clients.git
cd flask-c10-summative-lab-sessions-and-jwt-clients/client-with-sessions
npm install
npm start
```

With the API running, open `http://localhost:3000` and sign up, or log in as `alice` / `password123`.

## Running the Tests

From the project root:

```bash
pytest -v
```

The tests use an in-memory database and don't touch your real data.

## API Endpoints

All requests and responses use JSON. Errors are always returned as `{"errors": ["message", ...]}`.

### Authentication

| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| POST | `/signup` | Create an account and log in. Body: `username`, `password`, `password_confirmation` | 201 | 422 |
| POST | `/login` | Log in. Body: `username`, `password` | 200 | 401 |
| GET | `/check_session` | Return the logged-in user, or `{}` with 401 if logged out | 200 | 401 |
| DELETE | `/logout` | Log out | 204 | 401 |

Signup and login responses return the user without any password data:

```json
{"id": 1, "username": "alice"}
```

### Notes (login required)

| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| GET | `/notes?page=1&per_page=10` | The current user's notes, pinned first, paginated (`per_page` max 50) | 200 | 400, 401 |
| POST | `/notes` | Create a note. Body: `title`, `content`, optional `pinned` | 201 | 401, 422 |
| GET | `/notes/<id>` | One of the current user's notes | 200 | 401, 403, 404 |
| PATCH | `/notes/<id>` | Update any of `title`, `content`, `pinned` | 200 | 401, 403, 404, 422 |
| DELETE | `/notes/<id>` | Delete a note | 204 | 401, 403, 404 |

**Paginated response from `GET /notes?page=1&per_page=2`**

```json
{
  "notes": [
    {
      "id": 7,
      "title": "Project ideas",
      "content": "Build a habit tracker.",
      "pinned": true,
      "created_at": "2026-10-19T12:50:03",
      "updated_at": "2026-10-19T12:50:03",
      "user_id": 1
    },
    {
      "id": 3,
      "title": "Groceries",
      "content": "Milk, eggs, bread.",
      "pinned": false,
      "created_at": "2026-10-19T12:50:03",
      "updated_at": "2026-10-19T12:50:03",
      "user_id": 1
    }
  ],
  "page": 1,
  "per_page": 2,
  "total": 14,
  "pages": 7
}
```

### Status codes

| Status | Meaning |
|--------|---------|
| 401 Unauthorized | Not logged in, or wrong username/password |
| 403 Forbidden | Logged in, but the note belongs to another user |
| 404 Not Found | The note doesn't exist |
| 422 Unprocessable Entity | Validation failed (e.g. empty title, passwords don't match, username taken) |

## Example: Testing with curl

curl needs a cookie file to keep the session between requests:

```bash
B=http://127.0.0.1:5555
H="Content-Type: application/json"

curl -c cookies.txt -b cookies.txt -X POST $B/login -H "$H" \
  -d '{"username": "alice", "password": "password123"}'

curl -c cookies.txt -b cookies.txt "$B/notes?page=1&per_page=5"

curl -c cookies.txt -b cookies.txt -X POST $B/notes -H "$H" \
  -d '{"title": "Groceries", "content": "Milk, eggs, bread"}'

curl -c cookies.txt -b cookies.txt -X DELETE $B/logout
```
