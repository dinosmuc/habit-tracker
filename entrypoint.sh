#!/bin/bash
set -e

echo "Starting Habit Tracker Application..."

# Wait a moment for any system initialization
sleep 1

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Check if database has any habits (fresh start every time due to no volume)
echo "Initializing with sample data..."
python seed.py

# Start the Flask application
echo "Starting Flask server on port 5000..."
echo "Application ready! Visit http://localhost:5000"
python -m flask run --host=0.0.0.0 --port=5000
