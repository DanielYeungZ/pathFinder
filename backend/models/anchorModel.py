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
    ListField,
)
from datetime import datetime, timezone
from .imageModel import Image
from models import Building


class Tag(EmbeddedDocument):
    text = StringField(max_length=100, required=True)
    x = FloatField(max_length=100)
    y = FloatField(max_length=100)
    width = FloatField(max_length=100)
    height = FloatField(max_length=100)


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
    tags = ListField(
        StringField(max_length=100), default=list
    )  # Set default value to an empty list
    tagData = ListField(EmbeddedDocumentField(Tag), default=list)

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Anchor, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            "id": str(self.id),
            "image": str(self.image.id) if self.image else None,
            "tags": self.tags,
            "tagData": [tag.to_mongo() for tag in self.tagData],
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "classType": self.classType,
            "classId": self.classId,
            "label": self.label,
            "detectionId": self.detectionId,
            "metadata": self.metadata,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
        }
