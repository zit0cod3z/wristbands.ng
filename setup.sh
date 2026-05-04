#!/bin/bash
# WristbandsNG – Quick Setup Script

echo "=== WristbandsNG Setup ==="

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file
cp .env.example .env
echo ">> Edit .env with your database and email credentials"

# 4. Create MySQL database (run these in MySQL)
# CREATE DATABASE eventpro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# CREATE USER 'eventpro_user'@'localhost' IDENTIFIED BY 'your_password';
# GRANT ALL PRIVILEGES ON eventpro_db.* TO 'eventpro_user'@'localhost';
# FLUSH PRIVILEGES;

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Create media directories
mkdir -p media/qrcodes media/event_banners media/avatars

echo "=== Setup complete! Run: python manage.py runserver ==="
