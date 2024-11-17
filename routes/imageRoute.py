from flask import Blueprint, request, jsonify, send_file
import boto3
import cv2
import numpy as np
import requests
from io import BytesIO
from models import Building, Image
from services import token_required
from pathCalculator.graph_utils import create_graph, shortest_path
from pathCalculator.image_processing import read_image, convert_to_grayscale, apply_threshold
from pathCalculator import visualize_path
from config import (
    ROBOFLOW_API_KEY,
    ROBOFLOW_UPLOAD_URL,
    ROBOFLOW_FEATURE,
    S3_KEY,
    S3_KEY_ID,
    AWS_DEFAULT_REGION,
    S3_BUCKET,
)

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

    # Upload to S3
    s3_key = f"images/{file.filename}"
    s3_client.upload_fileobj(
        file,
        S3_BUCKET,
        s3_key,
    )
    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
    print(f"\n Uploaded to S3: {s3_url} ")

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


@image_bp.route("/calculate_path", methods=["POST"])
@token_required
def calculate_path(current_user):
    data = request.get_json()
    s3_image_url = data.get("s3_image_url")
    start_point = tuple(data.get("start_point"))
    end_point = tuple(data.get("end_point"))

    if not s3_image_url or not start_point or not end_point:
        return jsonify({"error": "Missing required parameters"}), 400

    # Download image from S3
    s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
    image_stream = BytesIO()
    s3_client.download_fileobj(S3_BUCKET, s3_key, image_stream)
    image_stream.seek(0)
    image_array = np.frombuffer(image_stream.read(), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Process image
    gray_image = convert_to_grayscale(image)
    binary_image = apply_threshold(gray_image, threshold_value=170)

    # Create graph and calculate the shortest path
    graph = create_graph(binary_image)
    path = shortest_path(graph, start_point, end_point)

    # Visualize path
    path_image = visualize_path(image, path, is_original=True)

    # Save to memory
    _, img_encoded = cv2.imencode(".jpg", path_image)
    img_buffer = BytesIO(img_encoded.tobytes())
    output_s3_key = f"processed_images/path_result.jpg"

    # Upload result back to S3
    s3_client.upload_fileobj(img_buffer, S3_BUCKET, output_s3_key, ExtraArgs={"ContentType": "image/jpeg"})
    output_s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{output_s3_key}"

    # TODO: save & update related information in database (image & request)

    return jsonify({
        "message": "Path calculated and saved successfully",
        "path_image_url": output_s3_url
    }), 200


@image_bp.route("/download_image", methods=["GET"])
@token_required
def download_image(current_user):
    s3_image_url = request.args.get("s3_image_url")
    if not s3_image_url:
        return jsonify({"error": "Missing s3_image_url parameter"}), 400

    # Extract S3 key from URL
    s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
    image_stream = BytesIO()

    try:
        s3_client.download_fileobj(S3_BUCKET, s3_key, image_stream)
        image_stream.seek(0)
        return send_file(image_stream, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
