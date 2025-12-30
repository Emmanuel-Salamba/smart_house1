web: gunicorn smart_house_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --worker-class sync
worker: daphne smart_house_backend.asgi:application --port $PORT --bind 0.0.0.0