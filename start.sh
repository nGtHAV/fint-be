#!/bin/bash

# Fint Backend Start Script
# Usage: ./start.sh [development|production]

set -e

MODE=${1:-development}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Create necessary directories
mkdir -p uploads
mkdir -p staticfiles

# Set environment variables
if [ "$MODE" = "production" ]; then
    export DJANGO_SETTINGS_MODULE=fint_backend.settings
    echo "🚀 Starting Fint Backend (Django) in PRODUCTION mode..."
    
    # Run migrations
    python3 manage.py migrate --no-input
    
    # Collect static files
    python3 manage.py collectstatic --no-input
    
    # Seed data
    python3 seed_data.py
    
    # Run with Gunicorn
    gunicorn --config gunicorn.conf.py fint_backend.wsgi:application
else
    export DJANGO_SETTINGS_MODULE=fint_backend.settings
    export DEBUG=True
    echo "🚀 Starting Fint Backend (Django) in DEVELOPMENT mode..."
    
    # Run migrations
    python3 manage.py migrate
    
    # Seed data
    python3 seed_data.py
    
    # Run development server
    python3 manage.py runserver 0.0.0.0:5000
fi
