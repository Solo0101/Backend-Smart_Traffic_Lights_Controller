#!/usr/bin/env bash
# #!/bin/bash
set -e

echo "${0}: making migrations for admin, auth, contenttypes."
python manage.py makemigrations webcam --noinput
echo "${0}: running migrations."
python manage.py migrate --noinput
export RUN_MAIN=True
python manage.py runserver 0.0.0.0:8000 --noreload