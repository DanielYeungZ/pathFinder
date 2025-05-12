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
    url = StringField(required=False, max_length=200)
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

    def to_dict(self):
        return {
            "id": str(self.id),
            "image": (
                str(self.image.id) if self.image else None
            ),  # Serialize the image reference
            "path": self.path,  # Serialize the path dictionary
            "url": self.url,  # Serialize the URL
            "start": self.start,  # Serialize the start point list
            "end": self.end,  # Serialize the end point list
            "createdAt": (
                self.createdAt.isoformat() if self.createdAt else None
            ),  # Serialize datetime
            "updatedAt": (
                self.updatedAt.isoformat() if self.updatedAt else None
            ),  # Serialize datetime
            "expireAt": (
                self.expireAt.isoformat() if self.expireAt else None
            ),  # Serialize datetime
        }
