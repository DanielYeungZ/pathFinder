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
from models import Building


# Define the User model (Document)
class Path(Document):
    building = ReferenceField(Building, required=True)
    path = DictField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(Path, self).save(*args, **kwargs)
