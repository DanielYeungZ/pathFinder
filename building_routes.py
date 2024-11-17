from flask import Blueprint, request, jsonify
from models import Building, User
from datetime import datetime, timezone, timedelta
import jwt
from config import TOKEN_SECRET_KEY as AC_TOKEN_SECRET_KEY

# Create a Blueprint for Building routes
building_bp = Blueprint('building', __name__)

# Create a building with a user linked from the token (POST request)
@building_bp.route('/building', methods=['POST'])
def create_building():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    try:
        # Decode the token
        decoded_token = jwt.decode(token, AC_TOKEN_SECRET_KEY, algorithms=['HS256'])
        user_id = decoded_token.get('user_id')

        # Retrieve the user information
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Get building data from request
        data = request.get_json()
        name = data.get("name")

        # Create and save the building
        building = Building(name=name, user=user)
        building.save()

        return jsonify({"message": "Building created!", "building_id": str(building.id)}), 201
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500