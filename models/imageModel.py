from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    ReferenceField,
    DictField,
    EmbeddedDocumentField,
    DateTimeField,
    IntField,
)
from datetime import datetime, timezone
from models import Building


# Define the User model (Document)
class Image(Document):
    building = ReferenceField(Building, required=True)
    type = StringField(
        required=True, max_length=100, choices=["raw", "processed", "path"]
    )
    url = StringField(required=True, max_length=200)
    floor = IntField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(Image, self).save(*args, **kwargs)
