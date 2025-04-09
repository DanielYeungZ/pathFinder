import unittest
import warnings
import logging
from flask import Flask
from routes.userRoute import user_bp
from models import User, Building, Image
import jwt
from config import TOKEN_SECRET_KEY
from mongoengine import connect, disconnect
from utils.common import printMsg
from bson import ObjectId
import requests

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class UserRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(user_bp, url_prefix="/api")
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

    def test_real_user_login_success(self):
        response = requests.post(
            "http://flask-env.eba-63h3zsef.us-east-2.elasticbeanstalk.com/api/user/login",
            headers={
                "Authorization": self.valid_token,
                "Content-Type": "application/json",
                "Origin": "http://localhost:3000/",
            },
            json={"password": "testPassword", "email": "test@gmail.com"},
        )
        print("test_real_user_login_success: ", response.json())

        self.assertEqual(response.status_code, 200)
