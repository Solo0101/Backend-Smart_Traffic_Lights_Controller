#!/bin/bash

set -e

echo "${0}: making migrations for admin, auth, contenttypes."
python manage.py makemigrations webcam
echo "${0}: running migrations."
python manage.py migrate

python manage.py runserver 0.0.0.0:8000 --noreload