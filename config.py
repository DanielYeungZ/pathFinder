import os

TOKEN_SECRET_KEY = "pathFinder_user"
S3_BUCKET = "robo-path-image"
S3_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
S3_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

S3_KEY_ID = "AKIA3ISBWCDTJCWL52XS"
S3_KEY = "4pvoxzPW7dysLE/AzuC8iHSKYveev1yjcixRczHr"
AWS_DEFAULT_REGION = "us-east-2"

# Configure Roboflow
ROBOFLOW_API_KEY = "Ym1IvaJmMhRLF9KtY6gK"
ROBOFLOW_UPLOAD_URL = "https://api.roboflow.com/dataset/your-dataset/upload"
ROBOFLOW_FEATURE = True
ROBOFLOW_MODEL = "indoor-map/21"

DEBUG = True
DETAIL_DEBUG = False
