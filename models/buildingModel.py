from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    ReferenceField,
    EmbeddedDocumentField,
    DateTimeField,
    DictField,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from models.userModel import User


class Building(Document):
    name = StringField(required=True, max_length=100)
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    user = ReferenceField(User, required=True)
    metadata = DictField()

    def save(self, *args, **kwargs):
        if not self.updatedAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Building, self).save(*args, **kwargs)
