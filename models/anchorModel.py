from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    FloatField,
    ReferenceField,
    DictField,
    EmbeddedDocumentField,
    IntField,
    DateTimeField,
)
from datetime import datetime, timezone
from .imageModel import Image
from models import Building


# Define the User model (Document)
class Anchor(Document):
    image = ReferenceField(Image, required=True)
    x = FloatField(max_length=100)
    y = FloatField(max_length=100)
    width = FloatField(max_length=100)
    height = FloatField(max_length=100)
    confidence = FloatField(max_length=100)
    classType = StringField(max_length=100)
    classId = IntField(max_length=100)
    label = StringField(max_length=100)
    detectionId = StringField(max_length=100)
    metadata = DictField()
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Anchor, self).save(*args, **kwargs)
