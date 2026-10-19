from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=30))


class SignupSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=30))
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=72))
    password_confirmation = fields.Str(required=True, load_only=True)

    @validates_schema
    def passwords_match(self, data, **kwargs):
        if data.get("password") != data.get("password_confirmation"):
            raise ValidationError("Passwords do not match.", "password_confirmation")


class NoteSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    content = fields.Str(required=True, validate=validate.Length(min=1))
    pinned = fields.Bool(load_default=False)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)


user_schema = UserSchema()
signup_schema = SignupSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)


def error_list(messages):
    """Flatten marshmallow's {"field": ["msg"]} into ["field: msg"].

    The provided frontend expects {"errors": [...]} as a list of strings.
    """
    errors = []
    for field, field_messages in messages.items():
        for message in field_messages:
            errors.append(message if field == "_schema" else f"{field}: {message}")
    return errors