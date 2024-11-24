from mongoengine import Document, EmbeddedDocument, StringField, ReferenceField, EmbeddedDocumentField, DateTimeField
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from models.userModel import User

class Building(Document):
    name = StringField(required=True, max_length=100)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    user = ReferenceField(User, required=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(Building, self).save(*args, **kwargs)
