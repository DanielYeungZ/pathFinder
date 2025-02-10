from functools import wraps
from flask import request, jsonify
import jwt
from config import TOKEN_SECRET_KEY
from models import User


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            data = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
            current_user = User.objects.get(id=data["user_id"])
        except Exception as e:
            return jsonify({"message": "Token is invalid!", "error": str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated
