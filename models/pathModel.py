from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    ReferenceField,
    DictField,
    EmbeddedDocumentField,
    ListField,
    IntField,
    DateTimeField,
)
from datetime import datetime, timezone, timedelta
from models import Building, Image


# Define the User model (Document)
class Path(Document):
    image = ReferenceField(Image, required=True)
    path = DictField()
    url = StringField(required=True, max_length=200)
    start = ListField(IntField(), required=True)
    end = ListField(IntField(), required=True)
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    expireAt = DateTimeField(
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1)
    )  # Set default expiration to 1 day

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Path, self).save(*args, **kwargs)

    meta = {"indexes": [{"fields": ["expireAt"], "expireAfterSeconds": 0}]}
