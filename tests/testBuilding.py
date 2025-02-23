import unittest
import warnings
from flask import Flask
from routes.buildingRoute import building_bp
from models import User, Building, Image
import jwt
from config import TOKEN_SECRET_KEY
from mongoengine import connect, disconnect
from utils.common import printMsg
from bson import ObjectId


class BuildingRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(building_bp, url_prefix="/api")
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True
        self.debug = False

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

        # Generate a valid token for the test user
        self.valid_token = jwt.encode(
            {"user_id": str(self.test_user.id)}, TOKEN_SECRET_KEY, algorithm="HS256"
        )

    def tearDown(self):
        # Clean up the database
        if self.debug:
            printMsg(self.test_user)
        User.objects(id=self.test_user.id).delete()
        Building.objects(user=self.test_user).delete()
        disconnect()

    def test_create_building_success(self):
        response = self.client.post(
            "/api/building",
            headers={"Authorization": self.valid_token},
            json={"name": "Test Building"},
        )
        if self.debug:
            print(f"Error: {response.json.get('error')}" + "\n")

        self.assertEqual(response.status_code, 201)
        self.assertIn("Building created!", response.json["message"])

    def test_create_building_missing_token(self):
        response = self.client.post("/api/building", json={"name": "Test Building"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token is missing", response.json["message"])

    def test_create_building_invalid_token(self):
        response = self.client.post(
            "/api/building",
            headers={"Authorization": "invalid_token"},
            json={"name": "Test Building"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid token", response.json["message"])

    def test_create_building_user_not_found(self):
        temp_object_id = str(ObjectId())
        invalid_token = jwt.encode(
            {"user_id": temp_object_id}, TOKEN_SECRET_KEY, algorithm="HS256"
        )
        response = self.client.post(
            "/api/building",
            headers={"Authorization": invalid_token},
            json={"name": "Test Building"},
        )

        if self.debug:
            print(f"Error: {response.json.get('error')}" + "\n")

        self.assertEqual(response.status_code, 404)
        self.assertIn("User not found", response.json["message"])

    def test_get_all_buildings(self):
        # Create buildings for the user
        building1 = Building(name="Building 1", user=self.test_user)
        building2 = Building(name="Building 2", user=self.test_user)
        building1.save()
        building2.save()

        # Generate a valid token for the user
        token = jwt.encode(
            {"user_id": str(self.test_user.id)}, TOKEN_SECRET_KEY, algorithm="HS256"
        )

        # Get all buildings for the user
        response = self.client.get(
            "/api/buildings",
            headers={"Authorization": token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["buildings"]), 2)
        self.assertIn("Building 1", [b["name"] for b in response.json["buildings"]])
        self.assertIn("Building 2", [b["name"] for b in response.json["buildings"]])

        Building.objects(user=self.test_user).delete()

    def test_get_building_by_id(self):
        # Create a building for the user
        building = Building(name="Building 1", user=self.test_user)
        building.save()

        # Generate a valid token for the user
        token = jwt.encode(
            {"user_id": str(self.test_user.id)}, TOKEN_SECRET_KEY, algorithm="HS256"
        )

        # Get the building by ID
        response = self.client.get(
            f"/api/building/{str(building.id)}",
            headers={"Authorization": token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["building"]["name"], "Building 1")

        Building.objects(user=self.test_user).delete()

    def test_get_all_buildings_with_images(self):
        # Create buildings for the user
        building1 = Building(name="Building 1", user=self.test_user)
        building2 = Building(name="Building 2", user=self.test_user)
        building1.save()
        building2.save()

        # Create images for the buildings
        image1 = Image(
            building=building1,
            type="raw",
            url="http://example.com/image1.jpg",
            floor=1,
            imageWidth=800,
            imageHeight=600,
        )
        image2 = Image(
            building=building2,
            type="processed",
            url="http://example.com/image2.jpg",
            floor=2,
            imageWidth=1024,
            imageHeight=768,
        )
        image1.save()
        image2.save()

        # Generate a valid token for the user
        token = jwt.encode(
            {"user_id": str(self.test_user.id)}, TOKEN_SECRET_KEY, algorithm="HS256"
        )

        # Get all buildings with images for the user
        response = self.client.get(
            "/api/buildings_with_images",
            headers={"Authorization": token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["buildings"]), 2)

        building1_data = next(
            (b for b in response.json["buildings"] if b["name"] == "Building 1"), None
        )
        building2_data = next(
            (b for b in response.json["buildings"] if b["name"] == "Building 2"), None
        )

        self.assertIsNotNone(building1_data)
        self.assertIsNotNone(building2_data)

        self.assertEqual(len(building1_data["images"]), 1)
        self.assertEqual(
            building1_data["images"][0]["url"], "http://example.com/image1.jpg"
        )

        self.assertEqual(len(building2_data["images"]), 1)
        self.assertEqual(
            building2_data["images"][0]["url"], "http://example.com/image2.jpg"
        )
        Building.objects(user=self.test_user).delete()
        Image.objects(id=image1.id).delete()
        Image.objects(id=image2.id).delete()


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    unittest.main(verbosity=2)
