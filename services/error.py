import jwt
from functools import wraps
from flask import request, jsonify
from config import TOKEN_SECRET_KEY


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"message": "An error occurred", "error": str(e)}), 500

    return decorated_function
