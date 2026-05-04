#!/usr/bin/env bash
# Render build script — runs once on every deploy

set -o errexit   # exit on any error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
