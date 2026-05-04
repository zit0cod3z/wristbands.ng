#!/usr/bin/env bash
# Render build script — runs once on every deploy
# rootDir is set to eventpro/ in render.yaml so this runs from inside eventpro/

set -o errexit

echo "==> Python version"
python --version

echo "==> Working directory"
pwd
ls -la

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Creating staticfiles directory"
mkdir -p staticfiles

echo "==> Running collectstatic"
python manage.py collectstatic --no-input --clear

echo "==> Verifying static files"
ls -la staticfiles/
find staticfiles -name "main.css" | head -5

echo "==> Running migrations"
python manage.py migrate

echo "==> Build complete"
