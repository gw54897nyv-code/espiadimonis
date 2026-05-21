web: gunicorn espiadimonis.wsgi --bind 0.0.0.0:$PORT --workers 2 --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
