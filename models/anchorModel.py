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
from models import Building, Image


# Define the User model (Document)
class Anchor(Document):
    building = ReferenceField(Building, required=True)
    image = ReferenceField(Image, required=True)
    type = StringField(
        required=True, max_length=100, choices=["classroom", "door", "exit", "stair"]
    )
    cord_x = StringField(max_length=100)
    cord_y = StringField(max_length=100)
    label = StringField(max_length=100)
    metadata = DictField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(Anchor, self).save(*args, **kwargs)
