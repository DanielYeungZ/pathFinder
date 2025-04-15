import unittest
import warnings
import logging
from flask import Flask
from services.auth import token_required
from routes.imageRoute import image_bp
from models import User, Building, Image, Anchor, Tag
import jwt
from config import TOKEN_SECRET_KEY
from mongoengine import connect, disconnect
from io import BytesIO
import os
import time
from config import (
    S3_BUCKET,
)
import requests
from colorama import Fore, Style, init

init(autoreset=True)


# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
class ColorFormatter(logging.Formatter):
    # Define color mappings for log levels
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        # Add color to the log level name
        level_color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
        # Format the message
        return super().format(record)


# Configure logging with timestamps
handler = logging.StreamHandler()
handler.setFormatter(
    ColorFormatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


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
        self.test_building = Building(name="Test Building", user=self.test_user).save()

        self.test_image = Image(
            building=self.test_building,
            type="processed",
            url="http://example.com/image2.jpg",
            floor=2,
            imageWidth=1024,
            imageHeight=768,
        ).save()

        self.test_anchor1 = Anchor(image=self.test_image, x=10, y=20).save()
        self.test_anchor2 = Anchor(image=self.test_image, x=30, y=40).save()

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
            start_time = time.time()
            response = self.client.post(
                "/api/upload_image",
                headers={"Authorization": self.valid_token},
                data=data,
                content_type="multipart/form-data",
            )
            end_time = time.time()
            duration = end_time - start_time  # Calculate the duration
            logger.info(f"Finished upload_image test in {duration:.2f} seconds")

        self.assertEqual(response.status_code, 200)
        self.assertIn("File uploaded successfully", response.json["message"])

    @unittest.skip("Skipping test_upload_eb_real_image_success")
    def test_upload_eb_real_image_success(self):
        image_path = os.path.join(
            os.path.dirname(__file__), "assets", "ENG_Floor1_4.jpg"
        )

        with open(image_path, "rb") as img:
            data = {
                "building_id": str(self.test_building.id),
                "type": "raw",
                "floor": 1,
            }
            start_time = time.time()
            response = requests.post(
                "http://flask-env.eba-63h3zsef.us-east-2.elasticbeanstalk.com/api/upload_image",
                headers={
                    "Authorization": self.valid_token,
                    "Origin": "http://localhost:3000",
                    # "Content-Type": "multipart/form-data",
                },
                data=data,
                files={
                    "file": (
                        "ENG_Floor1_4.jpg",
                        img,
                        "image/jpeg",
                    ),
                },
            )
            end_time = time.time()
            duration = end_time - start_time  # Calculate the duration

            logger.info(
                f"Finished upload_image test in {duration:.2f} seconds: {response.json()}"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("File uploaded successfully", response.json()["message"])

    @unittest.skip("Skipping this test for now")
    def test_upload_local_real_image_success(self):
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
            start_time = time.time()
            response = self.client.post(
                "http://http://127.0.0.1:8000/api/upload_image",
                headers={"Authorization": self.valid_token},
                data=data,
                content_type="multipart/form-data",
            )
            end_time = time.time()
            duration = end_time - start_time  # Calculate the duration

            logger.info(
                f"Finished upload_image test in {duration:.2f} seconds: {response.get_json()}"
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

    def test_get_image_with_anchors_2(self):
        # Create an image for the building
        image = Image(
            building=self.test_building,
            type="raw",
            url="http://example.com/image.jpg",
            floor=1,
            imageWidth=800,
            imageHeight=600,
        )
        image.save()

        # Create anchors for the image
        anchor1 = Anchor(image=image, label="Anchor 1", x=100.0, y=200.0)
        anchor1.tagData = [
            Tag(
                text="MEN",
                x=0.7616557478904724,
                y=0.7039927244186401,
                width=0.015559792518615723,
                height=0.007955033332109451,
            ),
        ]
        anchor2 = Anchor(image=image, label="Anchor 2", x=300.0, y=400.0)
        anchor1.save()
        anchor2.save()

        # Get the image with anchors
        response = self.client.get(
            f"/api/image/{str(image.id)}", headers={"Authorization": self.valid_token}
        )
        # logger.debug("response: %s", response.json)
        # print(f"response data: {response.json}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.json)
        self.assertEqual(response.json["image"]["id"], str(image.id))
        self.assertEqual(len(response.json["image"]["anchors"]), 2)
        self.assertEqual(
            response.json["image"]["building"]["id"], str(self.test_building.id)
        )
        self.assertEqual(
            response.json["image"]["building"]["name"], str(self.test_building.name)
        )

        anchor_labels = [
            anchor["label"] for anchor in response.json["image"]["anchors"]
        ]

        self.assertIn("Anchor 1", anchor_labels)
        self.assertIn("Anchor 2", anchor_labels)

        Image.objects(id=image.id).delete()
        Anchor.objects(id=anchor2.id).delete()
        Anchor.objects(id=anchor1.id).delete()

    def test_calculate_path_success(self):

        data = {
            "s3_image_url": f"https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg",
            "start_point": [0, 0],
            "end_point": [0, 1],
        }
        response = self.client.post(
            "/api/calculate_path",
            headers={"Authorization": self.valid_token},
            json=data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("path_image_url", response.json)

    # @unittest.skip("Skipping test_real_calculate_path_success")
    def test_real_local_calculate_path_success(self):
        data = {
            "s3_image_url": f"https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg",
            "start_point": [0, 0],
            "end_point": [0, 1],
        }
        response = self.client.post(
            "/api/calculate_path_v2",
            headers={"Authorization": self.valid_token},
            json=data,
        )

        print("response:", response.json)
        self.assertEqual(response.status_code, 200)
        self.assertIn("path_image_url", response.json)

    @unittest.skip("Skipping test_real_calculate_path_success")
    def test_real_calculate_path_success(self):
        data = {
            "s3_image_url": f"https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg",
            "start_point": [0, 0],
            "end_point": [0, 1],
        }

        response = requests.post(
            "http://flask-env.eba-63h3zsef.us-east-2.elasticbeanstalk.com/api/calculate_path",
            headers={
                "Authorization": self.valid_token,
                "Origin": "http://localhost:3000",
            },
            json=data,
        )

        print("response:", response.json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("path_image_url", response.json())

    def test_calculate_path_missing_params(self):
        data = {
            "s3_image_url": f"https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg"
        }
        response = self.client.post(
            "/api/calculate_path",
            headers={"Authorization": self.valid_token},
            json=data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_download_image_success(self):
        response = self.client.get(
            f"/api/download_image?s3_image_url=https://{S3_BUCKET}.s3.amazonaws.com/images/ENG_Floor1_4.jpg",
            headers={"Authorization": self.valid_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/jpeg")

    def test_download_image_missing_url(self):
        response = self.client.get(
            "/api/download_image", headers={"Authorization": self.valid_token}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_get_image_with_anchors(self):
        response = self.client.get(
            f"/api/image/{self.test_image.id}",
            headers={"Authorization": self.valid_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.json)
        self.assertEqual(response.json["image"]["url"], self.test_image.url)

    def test_delete_image(self):
        # Create an image for the building
        image = Image(
            building=self.test_building,
            type="raw",
            url="http://example.com/image.jpg",
            floor=1,
            imageWidth=800,
            imageHeight=600,
        ).save()

        # Create an anchor for the image
        anchor = Anchor(image=image, x=10, y=20).save()

        # Delete the image
        response = self.client.delete(
            f"/api/image/{str(image.id)}",
            headers={"Authorization": self.valid_token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["message"],
            "Image and associated anchors deleted successfully",
        )

        # Verify the image and associated anchors were deleted
        deleted_image = Image.objects(id=image.id).first()
        self.assertIsNone(deleted_image)

        deleted_anchor = Anchor.objects(id=anchor.id).first()
        self.assertIsNone(deleted_anchor)


class ColoredTextTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(Fore.GREEN + "✔ " + str(test) + Style.RESET_ALL + "\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(Fore.RED + "✘ " + str(test) + Style.RESET_ALL + "\n")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(Fore.YELLOW + "⚠ " + str(test) + Style.RESET_ALL + "\n")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    unittest.main(verbosity=1)
