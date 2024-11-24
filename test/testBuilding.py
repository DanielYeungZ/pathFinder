import unittest
from flask import Flask
from routes.buildingRoute import building_bp
from models import User, Building
import jwt
from config import TOKEN_SECRET_KEY
from mongoengine import connect
from utils.common import printMsg
from bson import ObjectId


class BuildingRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(building_bp, url_prefix='/api')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        self.debug = True

        connect(db='pathFinder',
                host='mongodb+srv://db1:VIotwHFXr3WA1JiT@cluster0.ohmao.mongodb.net/',
                tls=True,
                tlsAllowInvalidCertificates=True,
                uuidRepresentation='standard')

        # Create a test user
        password = "testPassword"
        self.test_user = User(username="test", email="test@gmail.com")
        self.test_user.set_password(password)
        self.test_user.save()

        # Generate a valid token for the test user
        self.valid_token = jwt.encode({'user_id': str(self.test_user.id)}, TOKEN_SECRET_KEY, algorithm='HS256')

    def tearDown(self):
        # Clean up the database
        if self.debug:
            printMsg(self.test_user)
        User.objects(id=self.test_user.id).delete()
        Building.objects(user=self.test_user).delete()

    def test_create_building_success(self):
        response = self.client.post('/api/building', headers={'Authorization': self.valid_token},
                                    json={'name': 'Test Building'})
        if self.debug:
            print(f"Error: {response.json.get('error')}" + "\n")

        self.assertEqual(response.status_code, 201)
        self.assertIn('Building created!', response.json['message'])

    def test_create_building_missing_token(self):
        response = self.client.post('/api/building', json={'name': 'Test Building'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('Token is missing', response.json['message'])

    def test_create_building_invalid_token(self):
        response = self.client.post('/api/building', headers={'Authorization': 'invalid_token'},
                                    json={'name': 'Test Building'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid token', response.json['message'])

    def test_create_building_user_not_found(self):
        temp_object_id = str(ObjectId())
        invalid_token = jwt.encode({'user_id': temp_object_id}, TOKEN_SECRET_KEY, algorithm='HS256')
        response = self.client.post('/api/building', headers={'Authorization': invalid_token},
                                    json={'name': 'Test Building'})

        if self.debug:
            print(f"Error: {response.json.get('error')}" + "\n")

        self.assertEqual(response.status_code, 404)
        self.assertIn('User not found', response.json['message'])

if __name__ == '__main__':
    unittest.main()
