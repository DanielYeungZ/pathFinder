from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    ReferenceField,
    DictField,
    EmbeddedDocumentField,
    DateTimeField,
)
from datetime import datetime, timezone
from models import User


# Define the User model (Document)
class Request(Document):
    user = ReferenceField(User, required=True)
    type = StringField(required=True, max_length=100)
    status = StringField(
        required=True, max_length=100, choices=["pending", "completed", "failed"]
    )
    metadata = DictField()
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Request, self).save(*args, **kwargs)
