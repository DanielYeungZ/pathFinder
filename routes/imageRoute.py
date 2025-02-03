from flask import Blueprint, request, jsonify
import boto3
import requests
from models import Building, Image
from .auth import token_required
from config import (
    ROBOFLOW_API_KEY,
    ROBOFLOW_UPLOAD_URL,
    ROBOFLOW_FEATURE,
    S3_KEY,
    S3_KEY_ID,
    AWS_DEFAULT_REGION,
)

image_bp = Blueprint("image", __name__)

# Configure S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=S3_KEY_ID,
    aws_secret_access_key=S3_KEY,
    region_name=AWS_DEFAULT_REGION,
)
S3_BUCKET = "your-s3-bucket-name"


@image_bp.route("/upload_image", methods=["POST"])
@token_required
def upload_image(current_user):
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Upload to S3
    s3_key = f"images/{file.filename}"
    s3_client.upload_fileobj(file, S3_BUCKET, s3_key)
    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"

    # Initialize roboflow_data
    roboflow_data = {}

    # Upload to Roboflow
    if ROBOFLOW_FEATURE:
        roboflow_response = requests.post(
            ROBOFLOW_UPLOAD_URL,
            files={"file": file},
            params={"api_key": ROBOFLOW_API_KEY},
        )
        roboflow_data = roboflow_response.json()

    # Save image data to MongoDB
    building_id = request.form.get("building_id")
    building = Building.objects(id=building_id).first()
    if not building:
        return jsonify({"error": "Building not found"}), 404

    image = Image(
        building=building,
        type=request.form.get("type"),
        url=s3_url,
        floor=int(request.form.get("floor")),
    )
    image.save()

    return (
        jsonify(
            {
                "message": "File uploaded successfully",
                "s3_url": s3_url,
                "roboflow_data": roboflow_data,
            }
        ),
        200,
    )
