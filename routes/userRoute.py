from flask import Blueprint, request, jsonify
from models import User
from datetime import datetime, timezone, timedelta
import jwt
from config import TOKEN_SECRET_KEY


# Create a Blueprint for User routes
user_bp = Blueprint("user", __name__)


# Create a user with an address and profile (POST request)
@user_bp.route("/user", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    user = User(username=username, email=email, password=password)
    user.save()

    return jsonify({"message": "User created!", "user_id": str(user.id)}), 201


@user_bp.route("/user/sample", methods=["GET"])
def create_sample_user():
    username = "test" + datetime.now(timezone.utc).isoformat()
    email = username + "@test.com"
    password = "test"

    user = User(username=username, email=email)
    user.set_password(password)
    user.save()

    user_count = User.objects.count()
    return jsonify({"user": user.to_json(), "count": user_count})


@user_bp.route("/user/login", methods=["POST"])
def login_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid input"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = User.objects(email=email).first()
        if user and user.check_password(password):
            # Generate JWT token
            token = jwt.encode(
                {
                    "user_id": str(user.id),
                    "exp": datetime.now(timezone.utc)
                    + timedelta(hours=12),  # Use timedelta correctly
                },
                TOKEN_SECRET_KEY,
                algorithm="HS256",
            )

            return jsonify({"message": "Login successful!", "token": token}), 200
        else:
            return jsonify({"message": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@user_bp.route("/user/info", methods=["GET"])
def get_user_info():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    try:
        # Decode the token
        decoded_token = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")

        # Retrieve the user information
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        return jsonify({"user": user.to_json()}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500
