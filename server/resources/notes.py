from flask import request
from flask_restful import Resource
from marshmallow import ValidationError

from extensions import db
from models import Note
from resources.auth import current_user, login_required
from schemas import error_list, note_schema, notes_schema

MAX_PER_PAGE = 50


def find_own_note(note_id):
    """Return (note, None) if the note belongs to the current user, else (None, error_response)."""
    note = db.session.get(Note, note_id)
    if note is None:
        return None, ({"errors": ["Note not found."]}, 404)
    if note.user_id != current_user().id:
        return None, ({"errors": ["You do not have access to this note."]}, 403)
    return note, None


class NoteList(Resource):
    method_decorators = [login_required]

    def get(self):
        """List the current user's notes, pinned first. Supports ?page= and ?per_page=."""
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), MAX_PER_PAGE)
        if page < 1 or per_page < 1:
            return {"errors": ["page and per_page must be positive integers."]}, 400

        query = (
            db.select(Note)
            .filter_by(user_id=current_user().id)
            .order_by(Note.pinned.desc(), Note.updated_at.desc(), Note.id.desc())
        )
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)

        return {
            "notes": notes_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }, 200

    def post(self):
        try:
            data = note_schema.load(request.get_json() or {})
            note = Note(**data, user=current_user())
        except ValidationError as err:
            return {"errors": error_list(err.messages)}, 422
        except ValueError as err:
            return {"errors": [str(err)]}, 422

        db.session.add(note)
        db.session.commit()
        return note_schema.dump(note), 201


class NoteDetail(Resource):
    method_decorators = [login_required]

    def get(self, id):
        note, error = find_own_note(id)
        if error:
            return error
        return note_schema.dump(note), 200

    def patch(self, id):
        note, error = find_own_note(id)
        if error:
            return error

        try:
            # partial=True: only the fields sent are required and validated.
            data = note_schema.load(request.get_json() or {}, partial=True)
            for field, value in data.items():
                setattr(note, field, value)
        except ValidationError as err:
            db.session.rollback()
            return {"errors": error_list(err.messages)}, 422
        except ValueError as err:
            db.session.rollback()
            return {"errors": [str(err)]}, 422

        db.session.commit()
        return note_schema.dump(note), 200

    def delete(self, id):
        note, error = find_own_note(id)
        if error:
            return error
        db.session.delete(note)
        db.session.commit()
        return {}, 204