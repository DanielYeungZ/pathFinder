from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    ReferenceField,
    EmbeddedDocumentField,
    DateTimeField,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


# Define the User model (Document)
class User(Document):
    username = StringField(required=True, max_length=50)
    email = StringField(required=True, max_length=100)
    status = StringField(required=True, max_length=40, default="active")
    passwordHash = StringField(required=True)
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.passwordHash = generate_password_hash(password)

    # Method to check the password
    def check_password(self, password):
        return check_password_hash(self.passwordHash, password)

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(User, self).save(*args, **kwargs)
