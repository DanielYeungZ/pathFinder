from flask import Blueprint, request, jsonify
from models import Building, User, Image
from datetime import datetime, timezone, timedelta
import jwt
from config import TOKEN_SECRET_KEY
from services.error import handle_errors
from services import token_required, logs

# Create a Blueprint for Building routes
building_bp = Blueprint("building", __name__)


# Create a building with a user linked from the token (POST request)
@building_bp.route("/building", methods=["POST"])
@handle_errors
@token_required
def create_building(current_user):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401

        # Decode the token
    decoded_token = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    user_id = decoded_token.get("user_id")

    # Get building data from request
    data = request.get_json()
    name = data.get("name")

    # Create and save the building
    building = Building(name=name, user=current_user)
    building.save()

    return (
        jsonify({"message": "Building created!", "building_id": str(building.id)}),
        201,
    )


@building_bp.route("/building/<building_id>", methods=["PUT"])
@handle_errors
@token_required
def update_building(building_id, current_user):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    # Decode the token
    decoded_token = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    user_id = decoded_token.get("user_id")

    # Retrieve the building by ID
    building = Building.objects(id=building_id, user=current_user).first()
    if not building:
        return jsonify({"message": "Building not found"}), 404

    # Get new building name from request
    data = request.get_json()
    new_name = data.get("name")
    if not new_name:
        return jsonify({"message": "New name is missing"}), 400

    # Update the building name
    building.name = new_name
    building.save()

    return (
        jsonify({"message": "Building updated!", "building_id": str(building.id)}),
        200,
    )


# Get all buildings for the authenticated user (GET request)
@building_bp.route("/buildings", methods=["GET"])
@handle_errors
def get_all_buildings():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    # Decode the token
    decoded_token = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    user_id = decoded_token.get("user_id")

    # Retrieve the user information
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Retrieve all buildings for the user
    buildings = Building.objects(user=user)
    buildings_list = [
        {"id": str(building.id), "name": building.name} for building in buildings
    ]

    return jsonify({"buildings": buildings_list}), 200


@building_bp.route("/buildings_with_images", methods=["GET"])
@handle_errors
def get_all_buildings_with_images():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    # Decode the token
    decoded_token = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    user_id = decoded_token.get("user_id")

    # Retrieve the user information
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Retrieve all buildings for the user
    buildings = Building.objects(user=user)
    buildings_list = []
    for building in buildings:
        images = Image.objects(building=building)
        images_list = [image.to_dict() for image in images]
        building_dict = building.to_dict()
        building_dict["images"] = images_list
        buildings_list.append(building_dict)

    return jsonify({"buildings": buildings_list}), 200


# Get a specific building by ID (GET request)
@building_bp.route("/building/<building_id>", methods=["GET"])
@handle_errors
def get_building(building_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    # Decode the token
    decoded_token = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    user_id = decoded_token.get("user_id")

    # Retrieve the user information
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Retrieve the building by ID
    building = Building.objects(id=building_id, user=user).first()
    if not building:
        return jsonify({"message": "Building not found"}), 404

    images = Image.objects(building=building)
    images_list = [image.simple_dict() for image in images]
    building_dict = building.to_dict()
    building_dict["images"] = images_list

    return jsonify({"building": building_dict}), 200


# Delete a specific building by ID (DELETE request)
@building_bp.route("/building/<building_id>", methods=["DELETE"])
@handle_errors
@token_required
def delete_building(current_user, building_id):
    # Retrieve the building by ID
    building = Building.objects(id=building_id, user=current_user).first()
    if not building:
        return jsonify({"message": "Building not found"}), 404

    # Delete associated images
    Image.objects(building=building).delete()

    # Delete the building
    building.delete()

    return (
        jsonify({"message": "Building and associated images deleted successfully"}),
        200,
    )
