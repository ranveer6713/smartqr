#!/bin/bash
echo "Installing project dependencies..."
python3 -m pip install -r requirements.txt --break-system-packages

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Running migrations..."
python3 manage.py migrate --noinput
