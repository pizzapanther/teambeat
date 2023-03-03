web: gunicorn tbeat.wsgi:application -c gconfig.py
worker: python manage.py rundramatiq
cron: python manage.py run_cron
