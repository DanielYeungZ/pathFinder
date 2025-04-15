import copy
from bson import Binary
from flask import Blueprint, request, jsonify, send_file
import boto3
import cv2
import concurrent.futures
import numpy as np
import requests
from io import BytesIO
from models import Building, Image, Anchor, Path
from services import token_required, logs, handle_errors, detail_logs, path_logs
from pathCalculator.graph_utils import create_graph, shortest_path, create_graph_origin
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
from services.roboflow import analysis, saveData
from factory import celery
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

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
        detail_logs(f"\n Uploaded to S3: {s3_url} ")
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
            width = bbox["Width"]
            height = bbox["Height"]
            text_data.append(
                {"text": text, "x": x, "y": y, "width": width, "height": height}
            )
    return text_data


def convert_normalized_to_pixel(normalized_coords, image_width, image_height):
    return {
        "x": int(normalized_coords["x"] * image_width),
        "y": int(normalized_coords["y"] * image_height),
        "width": int(normalized_coords["width"] * image_width),
        "height": int(normalized_coords["height"] * image_height),
    }


def convert_roboflow_bbox(roboflow_box):
    """Convert Roboflow bbox from center format to (xmin, ymin, xmax, ymax)."""
    x_center, y_center, width, height = (
        roboflow_box["x"],
        roboflow_box["y"],
        roboflow_box["width"],
        roboflow_box["height"],
    )
    xmin = x_center - (width / 2)
    ymin = y_center - (height / 2)
    xmax = x_center + (width / 2)
    ymax = y_center + (height / 2)
    return xmin, ymin, xmax, ymax


def convert_textract_bbox(textract_box, image_width, image_height):
    """Convert Textract bbox from normalized format to pixel format."""
    xmin = textract_box["x"] * image_width
    ymin = textract_box["y"] * image_height
    xmax = xmin + (textract_box["width"] * image_width)
    ymax = ymin + (textract_box["height"] * image_height)
    return xmin, ymin, xmax, ymax


def is_text_inside_object(textract_box, roboflow_box):
    """Check if the text bounding box is inside the object bounding box."""
    tx_min, ty_min, tx_max, ty_max = textract_box
    rx_min, ry_min, rx_max, ry_max = roboflow_box

    return (
        rx_min <= tx_min <= rx_max
        and ry_min <= ty_min <= ry_max
        and rx_min <= tx_max <= rx_max
        and ry_min <= ty_max <= ry_max
    )


def filter_text_in_roboflow_boxes_v2(
    text_data, roboflow_boxes, image_width, image_height
):
    for text_item in text_data:
        textract_box = convert_textract_bbox(text_item, image_width, image_height)
        # print(f"Text item: {text_item}")
        for box in roboflow_boxes:
            roboflow_box = convert_roboflow_bbox(box)

            # print(f"Box: {box}")
            if is_text_inside_object(textract_box, roboflow_box):
                box.setdefault("tags", []).append(text_item)
                # break
    # for box in roboflow_boxes:
    #     if box["class"] == "classroom":
    #         detail_logs(f"Box: {box}")
    return


def filter_text_in_roboflow_boxes(text_data, roboflow_boxes, image_width, image_height):
    filtered_text = []
    for text_item in text_data:
        pixel_coords = convert_normalized_to_pixel(text_item, image_width, image_height)
        x, y = pixel_coords["x"], pixel_coords["y"]
        width, height = pixel_coords["width"], pixel_coords["height"]
        # print(f"Text item: {text_item}")
        for box in roboflow_boxes:
            # print(f"Box: {box}")
            if (
                box["class"] == "classroom"
                and box["x"] <= x <= box["x"] + box["width"]
                # and box["x"] <= x + width <= box["x"] + box["width"]
                and box["y"] <= y <= box["y"] + box["height"]
                # and box["y"] <= y + height <= box["y"] + box["height"]
            ):
                box.setdefault("tags", []).append(text_item)
                # break
    for box in roboflow_boxes:
        if box["class"] == "classroom":
            detail_logs(f"Box: {box}")
    return filtered_text


def decode_image(file_content):
    image = cv2.imdecode(np.frombuffer(file_content, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return None, 0, 0
    image_height, image_width = image.shape[:2]
    logs(f"image_height: {image_height}, image_width: {image_width}")
    return image, image_height, image_width


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
        future_image = executor.submit(decode_image, copy.deepcopy(file_content))

        s3_url = future_s3.result()
        roboflow_data = future_roboflow.result()
        image, image_height, image_width = future_image.result()

    # Analyze with Textract
    try:
        if s3_url and image is not None:
            textract_response = analyze_with_textract(S3_BUCKET, s3_key)
            text_data = extract_text_and_coordinates(textract_response)
            detail_logs(f"Textract response: {text_data}")

            filter_text_in_roboflow_boxes_v2(
                text_data, roboflow_data["predictions"], image_width, image_height
            )
        # print(f"Textract response: {text_data}")
    except Exception as e:
        logs(f"Textract error: {e}")
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

    path_logs(
        f"calculate_path=====> Start point: {start_point}, End point: {end_point}"
    )

    try:

        image_doc = Image.objects(url=s3_image_url).first()
        if not image_doc:
            return jsonify({"error": "Image not found"}), 404

        path_doc = Path.objects(
            start=start_point,
            end=end_point,
            image=image_doc,
        ).first()

        # download_and_process_image.delay(s3_image_url, start_point, end_point)
        if path_doc and path_doc.url:
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
        path_logs(f"calculate_path=====> Downloading image from S3: {s3_image_url}")

        s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
        image_stream = BytesIO()
        s3_client.download_fileobj(S3_BUCKET, s3_key, image_stream)
        if image_stream.getbuffer().nbytes == 0:
            return jsonify({"error": "Downloaded image is empty"}), 500

        path_logs(f"calculate_path=====> done downloading image from S3")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    path_logs(
        f"calculate_pathss=====> Image stream size: {image_stream.getbuffer().nbytes} bytes"
    )

    image_stream.seek(0)
    path_logs(f"calculate_path=====> Image seek")
    image_array = np.frombuffer(image_stream.read(), dtype=np.uint8)
    path_logs(f"calculate_path=====> Image start")
    if image_array.size == 0:
        return jsonify({"error": "Failed to decode image, empty buffer"}), 500
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    path_logs(f"calculate_path=====> Image cv2 start")
    if image is None:
        return jsonify({"error": "Failed to decode image"}), 500

    path_logs(f"calculate_path=====> Image done")

    # Process image
    gray_image = convert_to_grayscale(image)
    binary_image = apply_threshold(gray_image, threshold_value=170)
    path_logs(f"calculate_path=====> Binary image shape: {binary_image.shape}")

    # Create graph and calculate the shortest path
    graph = create_graph(binary_image)
    path_logs(f"Graph node====> {len(graph.nodes())}")
    path = shortest_path(graph, start_point, end_point)
    path_logs(f"calculate_path=====> shortest path: {len(path)}")

    # Visualize path
    path_image = visualize_path(image, path, is_original=True)
    path_logs(f"calculate_path=====> Visualize path: {path_image.shape}")

    # Save to memory
    _, img_encoded = cv2.imencode(".jpg", path_image)
    img_buffer = BytesIO(img_encoded.tobytes())
    output_s3_key = f"processed_images/path_result.jpg"
    path_logs(f"calculate_path=====> Uploading path image to S3: {output_s3_key}")

    # Upload result back to S3
    s3_client.upload_fileobj(
        img_buffer, S3_BUCKET, output_s3_key, ExtraArgs={"ContentType": "image/jpeg"}
    )
    output_s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{output_s3_key}"
    path_logs(f"calculate_path=====> Uploaded path image to S3: {output_s3_url}")

    if output_s3_url:
        path_doc = Path(
            start=start_point,
            end=end_point,
            url=output_s3_url,
            image=image_doc,
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


@image_bp.route("/calculate_path_v2", methods=["POST"])
@token_required
def calculate_path_v2(current_user):
    data = request.get_json()

    if not all(
        [data, "s3_image_url" in data, "start_point" in data, "end_point" in data]
    ):
        return jsonify({"error": "Missing required parameters"}), 400

    s3_image_url = data.get("s3_image_url")
    start_point = tuple(data.get("start_point"))
    end_point = tuple(data.get("end_point"))

    if not start_point or not end_point:
        return jsonify({"error": "Start and end points are required"}), 400

    if not s3_image_url or not start_point or not end_point:
        return jsonify({"error": "Missing required parameters"}), 400

    path_logs(
        f"calculate_path=====> Start point: {start_point}, End point: {end_point}, image: {s3_image_url}"
    )

    try:

        image_doc = Image.objects(url=s3_image_url).first()
        if not image_doc:
            return jsonify({"error": "Image not found"}), 404

        path_doc = Path.objects(
            start=start_point,
            end=end_point,
            image=image_doc,
        ).first()

        # download_and_process_image.delay(s3_image_url, start_point, end_point)
        useCache = False
        if path_doc and path_doc.url and useCache:
            return (
                jsonify(
                    {
                        "message": "Path calculated and saved successfully",
                        "path_doc": path_doc.to_dict(),
                        "path_image_url": path_doc.url,
                    }
                ),
                200,
            )
        else:
            if not path_doc:
                path_doc = Path(
                    start=start_point,
                    end=end_point,
                    image=image_doc,
                )
                path_doc.save()

            path_logs(
                f"process_image new=====> Path doc ID: {str(path_doc.id)}, "
                f"S3 Image URL: {s3_image_url}, "
                f"Start Point: {start_point}, "
                f"End Point: {end_point}"
            )

            path_dict = path_doc.to_dict()
            task = process_image.delay(path_dict, s3_image_url, start_point, end_point)
            path_logs(f"task=====> {task}")
            return (
                jsonify(
                    {
                        "message": "Path calculated and saved successfully",
                        "path_doc": path_doc.to_dict(),
                        "task_id": task.id,
                    }
                ),
                200,
            )
    except Exception as e:
        path_logs(f"e=====>{e}")
        return jsonify({"image query error": str(e)}), 500


@celery.task
def process_image(path_doc, s3_image_url, start_point, end_point):
    # Download image from S3
    try:
        logging.info(f"calculate_path=====> Downloading image from S3: {s3_image_url}")

        s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
        image_stream = BytesIO()
        s3_client.download_fileobj(S3_BUCKET, s3_key, image_stream)
        if image_stream.getbuffer().nbytes == 0:
            return jsonify({"error": "Downloaded image is empty"}), 500

        logging.info(f"calculate_path=====> done downloading image from S3")

        logging.info(
            f"calculate_path=====> Image stream size: {image_stream.getbuffer().nbytes} bytes"
        )

        image_stream.seek(0)
        logging.info(f"calculate_path=====> Image seek")
        image_array = np.frombuffer(image_stream.read(), dtype=np.uint8)
        logging.info(f"calculate_path=====> image_array")
        if image_array.size == 0:
            return jsonify({"error": "Failed to decode image, empty buffer"}), 500
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        logging.info(f"calculate_path=====> cv2")
        if image is None:
            return jsonify({"error": "Failed to decode image"}), 500

        # Process image
        # gray_image = convert_to_grayscale(image)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        logging.info(f"calculate_path=====> gray_image")
        binary_image = apply_threshold(gray_image, threshold_value=170)
        logging.info(f"calculate_path=====> Binary image shape: {binary_image.shape}")

        # Create graph and calculate the shortest path
        graph = create_graph_origin(binary_image)
        logging.info(f"Graph nodes: {len(graph.nodes())}")
        path = shortest_path(graph, start_point, end_point)
        logging.info(f"calculate_path=====> shortest path: {len(path)}")

        # Visualize path
        path_image = visualize_path(image, path, is_original=True)
        logging.info(f"calculate_path=====> Visualize path: {path_image.shape}")

        # Save to memory
        _, img_encoded = cv2.imencode(".jpg", path_image)
        img_buffer = BytesIO(img_encoded.tobytes())
        output_s3_key = f"processed_images/{path_doc}.jpg"
        logging.info(
            f"calculate_path=====> Uploading path image to S3: {output_s3_key}"
        )

        # Upload result back to S3
        s3_client.upload_fileobj(
            img_buffer,
            S3_BUCKET,
            output_s3_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        output_s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{output_s3_key}"
        logging.info(f"calculate_path=====> Uploaded path image to S3: {output_s3_url}")

        # TODO: save & update related information in database (image & request)

        if output_s3_url:
            Path.objects(id=path_doc["id"]).update_one(
                set__url=output_s3_url,
                set__updatedAt=datetime.now(timezone.utc),
            )

        return {
            "status": "success",
            "path_doc_id": path_doc["id"],
            "output_s3_url": output_s3_url,
        }
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
        # print(f"Image data: {image_data}")
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


@image_bp.route("/task_status/<task_id>", methods=["GET"])
def task_status(task_id):
    task = process_image.AsyncResult(task_id)
    if task.state == "PENDING":
        return {"status": "pending"}
    elif task.state == "SUCCESS":
        return {"status": "done", "result": task.result}
    else:
        return {"status": task.state}


@image_bp.route("/path/<path_id>", methods=["GET"])
def path_fetch(path_id):
    try:

        path = Path.objects(id=path_id).first()

        if not path:
            return jsonify({"error": "Path not found"}), 404

        path_data = Path.to_dict()

        # print(f"Image data: {image_data}")
        return jsonify({"path": path_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@image_bp.route("/get_binary_image", methods=["POST"])
@token_required
def get_binary_image(current_user):
    try:
        data = request.get_json()
        if (
            not data
            or "image_id" not in data
            or "start_point" not in data
            or "end_point" not in data
        ):
            return jsonify({"error": "Missing required parameters"}), 400

        image_id = data.get("image_id")
        image_doc = Image.objects(id=image_id).first()
        if not image_doc:
            return jsonify({"error": "Image not found"}), 404
        elif not image_doc.binary_image:
            return (
                jsonify(
                    {
                        "message": "Binary already saved successfully",
                        "image_doc": image_doc.to_dict(),
                    }
                ),
                200,
            )
        s3_image_url = image_doc.url
        image_doc = Image.objects(url=s3_image_url).first()
        if not image_doc:
            return jsonify({"error": "Image not found"}), 404

        # Download image from S3
        s3_key = s3_image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[-1]
        image_stream = BytesIO()
        s3_client.download_fileobj(S3_BUCKET, s3_key, image_stream)

        if image_stream.getbuffer().nbytes == 0:
            return jsonify({"error": "Downloaded image is empty"}), 500

        # Process image
        image_stream.seek(0)
        image_array = np.frombuffer(image_stream.read(), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({"error": "Failed to decode image"}), 500

        # Convert to grayscale and binary
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary_image = apply_threshold(gray_image, threshold_value=170)

        # Save binary image data to MongoDB
        binary_image_list = binary_image.tolist()
        image_binary = Binary(image.tobytes())
        image_doc.update(
            set__binary_image=binary_image_list,
            set__image_binary=image_binary,
            set__image_shape=image.shape,
            set__updatedAt=datetime.now(timezone.utc),
        )

        return (
            jsonify(
                {
                    "message": "Binary image saved successfully",
                    "image_doc": image_doc.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@image_bp.route("/calculate_and_save_path", methods=["POST"])
@token_required
def calculate_and_save_path(current_user):
    try:
        data = request.get_json()
        if not all(
            [data, "image_id" in data, "start_point" in data, "end_point" in data]
        ):
            return jsonify({"error": "Missing required parameters"}), 400

        image_id = data.get("image_id")
        start_point = tuple(data.get("start_point"))
        end_point = tuple(data.get("end_point"))

        image_doc = Image.objects(id=image_id).first()
        if not image_doc:
            return jsonify({"error": "Image not found"}), 404

        if not image_doc.binary_image:
            return (
                jsonify(
                    {
                        "error": "Binary image not found. Please run save_binary_image first"
                    }
                ),
                400,
            )

        path_doc = Path.objects(
            start=start_point,
            end=end_point,
            image=image_doc,
        ).first()

        # download_and_process_image.delay(s3_image_url, start_point, end_point)
        useCache = False
        if path_doc and path_doc.url and useCache:
            return (
                jsonify(
                    {
                        "message": "Path calculated and saved successfully",
                        "path_doc": path_doc.to_dict(),
                        "path_image_url": path_doc.url,
                    }
                ),
                200,
            )
        else:
            if not path_doc:
                path_doc = Path(
                    start=start_point,
                    end=end_point,
                    image=image_doc,
                )
                path_doc.save()
        # Create graph and calculate path
        binary_image = np.array(image_doc.binary_image)
        graph = create_graph_origin(binary_image)
        path = shortest_path(graph, start_point, end_point)

        # Visualize path
        image_binary = image_doc.image_binary
        image_shape = image_doc.image_shape
        image = np.frombuffer(image_binary, dtype=np.uint8).reshape(image_shape)

        path_image = visualize_path(image, path, is_original=True)
        path_logs(f"calculate_path=====> Visualize path: {path_image.shape}")

        # Save to memory
        _, img_encoded = cv2.imencode(".jpg", path_image)
        img_buffer = BytesIO(img_encoded.tobytes())
        output_s3_key = f"processed_images/{path_doc}.jpg"
        path_logs(f"calculate_path=====> Uploading path image to S3: {output_s3_key}")

        # Upload result back to S3
        s3_client.upload_fileobj(
            img_buffer,
            S3_BUCKET,
            output_s3_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        output_s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{output_s3_key}"

        if output_s3_url:
            path_doc.update(
                set__url=output_s3_url,
                set__updatedAt=datetime.now(timezone.utc),
            )
        return (
            jsonify(
                {
                    "message": "Path calculated and saved successfully",
                    "path_doc": path_doc.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
