import requests
import json
import tempfile
import time
from config import ROBOFLOW_API_KEY, ROBOFLOW_MODEL
from roboflow import Roboflow
from services.utils import logs, detail_logs
from models import Anchor

rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project("indoor-map")
model = project.version("18").model

# Define retry parameters
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def analysis(file_content):
    # Define the API endpoint and parameters
    api_url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}"
    for attempt in range(MAX_RETRIES):
        try:
            # Make the POST request to the Roboflow API
            response = requests.post(
                api_url,
                files={"file": ("image.jpg", file_content)},
                params={"api_key": ROBOFLOW_API_KEY},
            )

            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                # Print the response
                detail_logs(f"Roboflow upload result: {json.dumps(result, indent=4)}")
                return result
            else:
                result = response.json()
                logs(
                    f"Failed to upload image to Roboflow: {result} === {response.status_code}"
                )
                return None
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logs(f"Retrying... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                return None


def saveData(image, roboflowData):
    inferenceId = roboflowData.get("inference_id")
    imageWidth = roboflowData.get("image.width")
    imageHeight = roboflowData.get("image.height")

    image.inferenceId = inferenceId
    image.imageWidth = imageWidth
    image.imageHeight = imageHeight
    image.save()

    predictions = roboflowData.get("predictions")
    for prediction in predictions:
        # print("prediction====>", prediction)
        anchor = Anchor(
            image=image,
            x=prediction.get("x"),
            y=prediction.get("y"),
            width=prediction.get("width"),
            height=prediction.get("height"),
            confidence=prediction.get("confidence"),
            classType=prediction.get("class"),
            classId=prediction.get("class_id"),
            detectionId=prediction.get("detection_id"),
            tagData=prediction.get("tags"),
        )
        anchor.save()
    return


def analysisV2(file_content):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        result = model.predict(temp_file_path, confidence=40, overlap=30).json()

        logs(f"Roboflow V2 upload result: {json.dumps(result, indent=4)}")
        return result
    except Exception as e:
        logs(f"Exception occurred during analysisV2: {e}")
        return None
