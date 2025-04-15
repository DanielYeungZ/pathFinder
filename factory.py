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
        broker="rediss://pathfinding-anptdp.serverless.use2.cache.amazonaws.com:6379/0",
        backend="rediss://pathfinding-anptdp.serverless.use2.cache.amazonaws.com:6379/0",
    )

    celery.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}

    celery.conf.result_backend = (
        "rediss://pathfinding-anptdp.serverless.use2.cache.amazonaws.com:6379/0"
    )
    celery.conf.task_default_queue = "{celery}"
    celery.conf.result_backend_transport_options = {"key_prefix": "{celery}-"}

    logging.basicConfig(level=logging.INFO)

    # 🧠 Only include app.config AFTER setting the ssl parameters
    celery.conf.update(app.config)
    print(f"app.config: {app.config}")

    # celery.conf.task_key_prefix = "{celery}"
    # celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
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

from routes.imageRoute import process_image
