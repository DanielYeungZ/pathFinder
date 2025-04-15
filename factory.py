# celery_app.py
import ssl
from celery import Celery
from flask import Flask
from flaskConfig import Config
from flask_cors import CORS
import logging

logger = logging.getLogger(__name__)


def make_celery(app):
    # print("Creating Celery instance...", app.config)
    celery = Celery(
        "tasks",
        broker="sqs://",
        backend=None,
    )

    # Configure SQS specific settings
    celery.conf.broker_transport_options = {
        "region": "us-east-2",
        "visibility_timeout": 3600,
        "polling_interval": 1,
        "predefined_queues": {
            "awseb-e-snhqgukvsc-stack-AWSEBWorkerQueue-7beyiLXX2yLZ": {
                "url": "https://sqs.us-east-2.amazonaws.com/774305616102/awseb-e-snhqgukvsc-stack-AWSEBWorkerQueue-7beyiLXX2yLZ"
            }
        },
    }

    celery.conf.task_default_queue = (
        "awseb-e-snhqgukvsc-stack-AWSEBWorkerQueue-7beyiLXX2yLZ"
    )

    # Add more logging
    celery.conf.worker_log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    celery.conf.worker_task_log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # celery.conf.worker_redirect_stdouts = True
    # celery.conf.worker_redirect_stdouts_level = "DEBUG"

    logging.basicConfig(level=logging.INFO)

    # 🧠 Only include app.config AFTER setting the ssl parameters
    celery.conf.update(app.config)
    print(f"app.config: {app.config}")

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    # celery.autodiscover_tasks(["routes"])
    return celery


def create_app():
    app = Flask(__name__)
    # Allow all cross-origin requests
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers="*",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 16 MB
    # app.config.from_object(Config)

    return app


app = create_app()
celery = make_celery(app)
