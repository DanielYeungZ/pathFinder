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
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Path, self).save(*args, **kwargs)
