from mongoengine import Document, EmbeddedDocument, StringField, ReferenceField, EmbeddedDocumentField, DateTimeField
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

# Define the User model (Document)
class User(Document):
    username = StringField(required=True, max_length=50)
    email = StringField(required=True, max_length=100)
    status = StringField(required=True, max_length=40,default="active")
    password_hash = StringField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check the password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(User, self).save(*args, **kwargs)



class Building(Document):
    name = StringField(required=True, max_length=100)
    email = StringField(required=True, max_length=100)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    user = ReferenceField(User, required=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(Building, self).save(*args, **kwargs)