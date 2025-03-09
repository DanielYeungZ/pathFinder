from flask import Blueprint, request, jsonify, send_file
import boto3
import cv2
import concurrent.futures
import numpy as np
import requests
from io import BytesIO
from models import Building, Image, Anchor, Path
from services import token_required, logs, handle_errors
from pathCalculator.graph_utils import create_graph, shortest_path
from pathCalculator.image_processing import (
    read_image,
    convert_to_grayscale,
    apply_threshold,
)
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
from services.roboflow import analysis, analysisV2, saveData
from factory import celery


image_bp = Blueprint("image", __name__)

# Configure S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=S3_KEY_ID,
    aws_secret_access_key=S3_KEY,
    region_name=AWS_DEFAULT_REGION,
)

# Configure Textract
textract_client = boto3.client(
    "textract",
    aws_access_key_id=S3_KEY_ID,
    aws_secret_access_key=S3_KEY,
    region_name=AWS_DEFAULT_REGION,
)


def upload_to_s3(file, s3_key):
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, s3_key)
        s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
        print(f"\n Uploaded to S3: {s3_url} ")
        return s3_url
    except Exception as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")


def run_roboflow_analysis(file_content):
    try:
        roboflow_data = analysis(file_content)
        return roboflow_data
    except Exception as e:
        raise Exception(f"Failed to run Roboflow analysis: {str(e)}")


def analyze_with_textract(s3_bucket, s3_key):
    try:
        response = textract_client.analyze_document(
            Document={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}},
            FeatureTypes=["TABLES", "FORMS"],
        )
        return response
    except Exception as e:
        raise Exception(f"Failed to analyze document with Textract: {str(e)}")


def extract_text_and_coordinates(textract_response):
    text_data = []
    for block in textract_response["Blocks"]:
        if block["BlockType"] == "LINE":
            text = block["Text"]
            bbox = block["Geometry"]["BoundingBox"]
            x = bbox["Left"]
            y = bbox["Top"]
            text_data.append({"text": text, "x": x, "y": y})
    return text_data


def filter_text_in_roboflow_boxes(text_data, roboflow_boxes):
    filtered_text = []
    for text_item in text_data:
        x, y = text_item["x"], text_item["y"]
        for box in roboflow_boxes:
            if (
                box["x"] <= x <= box["x"] + box["width"]
                and box["y"] <= y <= box["y"] + box["height"]
            ):
                filtered_text.append(text_item)
                break
    return filtered_text


@image_bp.route("/upload_image", methods=["POST"])
@token_required
def upload_image(current_user):
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_content = file.read()
    logs(f"File content size: {len(file_content)} bytes")
    # Upload to S3
    s3_key = f"images/{str(current_user.id)}_{file.filename}"
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_s3 = executor.submit(upload_to_s3, BytesIO(file_content), s3_key)
        future_roboflow = executor.submit(run_roboflow_analysis, file_content)

        s3_url = future_s3.result()
        roboflow_data = future_roboflow.result()

    # Analyze with Textract
    try:
        textract_response = analyze_with_textract(S3_BUCKET, s3_key)
        text_data = extract_text_and_coordinates(textract_response)
        logs(f"Textract response: {text_data}")
        # filtered_text_data = filter_text_in_roboflow_boxes(text_data, roboflow_data['boxes'])
        # print(f"Textract response: {text_data}")
    except Exception as e:
        logs(f"Textract error: {str(e)}")
        textract_response = None

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

    # Upload to Roboflow
    if ROBOFLOW_FEATURE and roboflow_data:
        saveData(image, roboflow_data)

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


@image_bp.route("/calculate_path", methods=["POST"])
@token_required
def calculate_path(current_user):
    data = request.get_json()

    if (
        not data
        or "s3_image_url" not in data
        or "start_point" not in data
        or "end_point" not in data
    ):
        return jsonify({"error": "Missing required parameters"}), 400

    s3_image_url = data.get("s3_image_url")
    start_point = tuple(data.get("start_point"))
    end_point = tuple(data.get("end_point"))

    if not start_point or not end_point:
        return jsonify({"error": "Start and end points are required"}), 400

    if not s3_image_url or not start_point or not end_point:
        return jsonify({"error": "Missing required parameters"}), 400

    try:

        image_doc = Image.objects(url=s3_image_url).first()
        if not image_doc:
            return jsonify({"error": "Image not found"}), 404

        path_doc = Path.objects(start=start_point, end=end_point).first()

        # download_and_process_image.delay(s3_image_url, start_point, end_point)
        if path_doc:
            return (
                jsonify(
                    {
                        "message": "Path calculated and saved successfully",
                        "path_image_url": path_doc.url,
                    }
                ),
                200,
            )
    except Exception as e:
        return jsonify({"image query error": str(e)}), 500

    # Download image from S3
    try:
        s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
        image_stream = BytesIO()
        s3_client.download_fileobj(S3_BUCKET, s3_key, image_stream)
        if image_stream.getbuffer().nbytes == 0:
            return jsonify({"error": "Downloaded image is empty"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    image_stream.seek(0)
    image_array = np.frombuffer(image_stream.read(), dtype=np.uint8)
    if image_array.size == 0:
        return jsonify({"error": "Failed to decode image, empty buffer"}), 500
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        return jsonify({"error": "Failed to decode image"}), 500

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
    s3_client.upload_fileobj(
        img_buffer, S3_BUCKET, output_s3_key, ExtraArgs={"ContentType": "image/jpeg"}
    )
    output_s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{output_s3_key}"

    # TODO: save & update related information in database (image & request)

    if output_s3_url:
        path_doc = Path(
            start=start_point, end=end_point, url=output_s3_url, image=image_doc
        )
        path_doc.save()

    return (
        jsonify(
            {
                "message": "Path calculated and saved successfully",
                "path_image_url": output_s3_url,
            }
        ),
        200,
    )


@celery.task
def download_and_process_image(s3_image_url, start_point, end_point):

    print("celery task started====================>")

    # Extract S3 key from URL
    s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]

    # Download image from S3
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
    s3_client.upload_fileobj(
        img_buffer, S3_BUCKET, output_s3_key, ExtraArgs={"ContentType": "image/jpeg"}
    )
    output_s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{output_s3_key}"

    return output_s3_url


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
        return send_file(image_stream, mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get an image with anchors by ID (GET request)
@image_bp.route("/image/<image_id>", methods=["GET"])
@token_required
def get_image_with_anchors(current_user, image_id):
    try:
        image = Image.objects(id=image_id).first()

        if not image:
            return jsonify({"error": "Image not found"}), 404

        anchors = Anchor.objects(image=image)

        image_data = image.to_dict()
        image_data["anchors"] = [anchor.to_dict() for anchor in anchors]
        image_data["building"] = image.building.to_dict()
        return jsonify({"image": image_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@image_bp.route("/image/<image_id>", methods=["DELETE"])
@handle_errors
@token_required
def delete_image(current_user, image_id):
    # Retrieve the image by ID
    image = Image.objects(id=image_id).first()
    if not image:
        return jsonify({"error": "Image not found"}), 404

    # Delete associated anchors
    Anchor.objects(image=image).delete()

    # Delete the image from S3
    # s3_key = image.url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
    # try:
    #     s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
    # except Exception as e:
    #     return jsonify({"error": f"Failed to delete image from S3: {str(e)}"}), 500

    # Delete the image from the database
    image.delete()

    return (
        jsonify({"message": "Image and associated anchors deleted successfully"}),
        200,
    )
