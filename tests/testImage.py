import unittest
import warnings
from flask import Flask
from services.auth import token_required
from routes.imageRoute import image_bp
from models import User, Building, Image
import jwt
from config import TOKEN_SECRET_KEY
from mongoengine import connect, disconnect
from io import BytesIO
import os
from config import (
    S3_BUCKET,
)


class ImageRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(image_bp, url_prefix="/api")
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

        connect(
            db="pathFinder",
            host="mongodb+srv://db1:VIotwHFXr3WA1JiT@cluster0.ohmao.mongodb.net/",
            tls=True,
            tlsAllowInvalidCertificates=True,
            uuidRepresentation="standard",
        )

        # Create a test user
        password = "testPassword"
        self.test_user = User(username="test", email="test@gmail.com")
        self.test_user.set_password(password)
        self.test_user.save()

        # Create a test building
        self.test_building = Building(name="Test Building", user=self.test_user)
        self.test_building.save()

        # Generate a valid token for the test user
        self.valid_token = jwt.encode(
            {"user_id": str(self.test_user.id)}, TOKEN_SECRET_KEY, algorithm="HS256"
        )

    def tearDown(self):
        # Clean up the database
        User.objects(id=self.test_user.id).delete()
        Building.objects(id=self.test_building.id).delete()
        # Image.objects.delete()
        disconnect()

    def test_upload_image_success(self):
        data = {
            "file": (BytesIO(b"test image content"), "test_image.jpg"),
            "building_id": str(self.test_building.id),
            "type": "raw",
            "floor": 1,
        }
        response = self.client.post(
            "/api/upload_image",
            headers={"Authorization": self.valid_token},
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("File uploaded successfully", response.json["message"])

    def test_upload_real_image_success(self):
        image_path = os.path.join(
            os.path.dirname(__file__), "assets", "ENG_Floor1_4.jpg"
        )

        with open(image_path, "rb") as img:
            data = {
                "file": (img, "ENG_Floor1_4.jpg"),
                "building_id": str(self.test_building.id),
                "type": "raw",
                "floor": 1,
            }
            response = self.client.post(
                "/api/upload_image",
                headers={"Authorization": self.valid_token},
                data=data,
                content_type="multipart/form-data",
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("File uploaded successfully", response.json["message"])

    def test_upload_image_missing_file(self):
        data = {"building_id": str(self.test_building.id), "type": "raw", "floor": 1}
        response = self.client.post(
            "/api/upload_image", headers={"Authorization": self.valid_token}, data=data
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No file part", response.json["error"])

    def test_upload_image_missing_token(self):
        data = {
            "file": (BytesIO(b"test image content"), "test_image.jpg"),
            "building_id": str(self.test_building.id),
            "type": "raw",
            "floor": 1,
        }
        response = self.client.post(
            "/api/upload_image", data=data, content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token is missing", response.json["message"])

    def test_calculate_path_success(self):
        data = {
            "s3_image_url": f"https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg",
            "start_point": [0, 0],
            "end_point": [0, 1]
        }
        response = self.client.post(
            "/api/calculate_path",
            headers={"Authorization": self.valid_token},
            json=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("path_image_url", response.json)

    def test_calculate_path_missing_params(self):
        data = {"s3_image_url": f"https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg"}
        response = self.client.post(
            "/api/calculate_path",
            headers={"Authorization": self.valid_token},
            json=data
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_download_image_success(self):
        response = self.client.get(
            f"/api/download_image?s3_image_url=https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg",
            headers={"Authorization": self.valid_token}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/jpeg")

    def test_download_image_missing_url(self):
        response = self.client.get("/api/download_image", headers={"Authorization": self.valid_token})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    unittest.main(verbosity=2)
