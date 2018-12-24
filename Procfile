web: gunicorn app.app:create_app\(\) -b 0.0.0.0:$PORT
worker: rq worker -u $REDIS_URL swt-tasks
