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
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(Request, self).save(*args, **kwargs)
