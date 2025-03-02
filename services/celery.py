from celery import Celery


class CeleryConfig:
    def __init__(self, app=None):
        self.celery = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.celery = Celery(
            app.import_name,
            backend=app.config["CELERY_RESULT_BACKEND"],
            broker=app.config["CELERY_BROKER_URL"],
        )
        self.celery.conf.update(app.config)
        TaskBase = self.celery.Task

        class ContextTask(TaskBase):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        self.celery.Task = ContextTask
