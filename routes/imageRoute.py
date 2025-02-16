from flask import Blueprint, request, jsonify
import boto3
import requests
from models import Building, Image
from services import token_required
from config import (
    ROBOFLOW_API_KEY,
    ROBOFLOW_UPLOAD_URL,
    ROBOFLOW_FEATURE,
    S3_KEY,
    S3_KEY_ID,
    AWS_DEFAULT_REGION,
    S3_BUCKET,
)
from services.roboflow import analysis, analysisV2, saveData

image_bp = Blueprint("image", __name__)

# Configure S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=S3_KEY_ID,
    aws_secret_access_key=S3_KEY,
    region_name=AWS_DEFAULT_REGION,
)


@image_bp.route("/upload_image", methods=["POST"])
@token_required
def upload_image(current_user):
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    fileContent = file.read()

    # Upload to S3
    s3_key = f"images/{file.filename}"
    s3_client.upload_fileobj(
        file,
        S3_BUCKET,
        s3_key,
    )
    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
    print(f"\n Uploaded to S3: {s3_url} ")

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

    # Initialize roboflow_data
    roboflowData = {}
    inferenceId = None

    # Upload to Roboflow
    if ROBOFLOW_FEATURE:
        roboflowData = analysis(fileContent)
        if roboflowData:
            saveData(image, roboflowData)

    return (
        jsonify(
            {
                "message": "File uploaded successfully",
                "s3_url": s3_url,
                "imageData": image.to_json(),
            }
        ),
        200,
    )
