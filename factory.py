# celery_app.py
from celery import Celery
from flask import Flask
from flaskConfig import Config
from flask_cors import CORS


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"],
    )
    celery.conf.update(app.config)
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
    app.config.from_object(Config)

    return app


app = create_app()
celery = make_celery(app)
