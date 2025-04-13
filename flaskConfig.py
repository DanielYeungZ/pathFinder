class Config:
    CELERY_BROKER_URL = (
        "redis://pathfinding-anptdp.serverless.use2.cache.amazonaws.com:6379/0"
    )
    CELERY_RESULT_BACKEND = (
        "redis://pathfinding-anptdp.serverless.use2.cache.amazonaws.com:6379/0"
    )
