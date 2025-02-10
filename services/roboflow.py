import requests
from config import ROBOFLOW_API_KEY, ROBOFLOW_MODEL


def analysis(file):
    # Define the API endpoint and parameters
    api_url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}"

    # Make the POST request to the Roboflow API
    response = requests.post(
        api_url, files={"file": file}, params={"api_key": ROBOFLOW_API_KEY}
    )

    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        # Print the response
        print(f"Roboflow upload result: {result}")
        return result
    else:
        print(f"Failed to upload image to Roboflow: {response.status_code}")
        return None
