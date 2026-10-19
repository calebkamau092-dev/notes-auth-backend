#!/usr/bin/env python3

from random import choice, randint

from faker import Faker

from app import app
from extensions import db
from models import Note, User

fake = Faker()
SEED_PASSWORD = "password123"

with app.app_context():
    print("Clearing old data...")
    Note.query.delete()
    User.query.delete()

    print("Creating users...")
    users = []
    for username in ["alice", "bob", "carol"]:
        user = User(username=username)
        user.password_hash = SEED_PASSWORD
        users.append(user)
    db.session.add_all(users)

    print("Creating notes...")
    for user in users:
        for _ in range(randint(12, 15)):
            db.session.add(Note(
                title=fake.sentence(nb_words=4).rstrip("."),
                content=fake.paragraph(nb_sentences=3),
                pinned=choice([True, False, False, False]),
                user=user,
            ))

    db.session.commit()
    print(f"Done seeding! Log in as alice, bob or carol with password '{SEED_PASSWORD}'.")