from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    ReferenceField,
    DictField,
    EmbeddedDocumentField,
    DateTimeField,
    ListField,
    IntField,
    BinaryField,
)
from datetime import datetime, timezone
from models import Building


# Define the User model (Document)
class Image(Document):
    building = ReferenceField(Building, required=True)
    inferenceId = StringField(default=None, required=False)
    type = StringField(
        required=True, max_length=100, choices=["raw", "processed", "path"]
    )
    url = StringField(required=True, max_length=200)
    floor = IntField(required=True)
    imageWidth = IntField(default=None, required=False)
    imageHeight = IntField(default=None, required=False)
    image_binary = BinaryField(required=False)
    image_shape = ListField(IntField(), required=False)
    createdAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    binary_image = ListField()

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
        return super(Image, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            "id": str(self.id),
            "building": self.building.to_dict(),
            "type": self.type,
            "url": self.url,
            "floor": self.floor,
            "imageWidth": self.imageWidth,
            "imageHeight": self.imageHeight,
            "binary_image": self.binary_image,
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat(),
        }

    def simple_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "url": self.url,
            "floor": self.floor,
            "imageWidth": self.imageWidth,
            "imageHeight": self.imageHeight,
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat(),
        }
