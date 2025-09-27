# Habit Tracker

A habit tracking application with web interface and REST API.

## 🚀 Quick Start (Docker)

**One command to run everything:**

```bash
docker run -p 5000:5000 dinosmuc/habit-tracker:latest
```

**Then visit:** http://localhost:5000

✅ Automatic database setup and sample data
✅ Fresh start every time
✅ No configuration needed

---

## 🐳 Alternative Docker Commands

```bash
# Run in background
docker run -d -p 5000:5000 --name habit-tracker dinosmuc/habit-tracker:latest

# Build locally
git clone <repository-url>
cd habit-tracker
docker build -t habit-tracker .
docker run -p 5000:5000 habit-tracker

# Development with docker-compose
docker-compose up
```

---

## 💻 Local Development (Without Docker)

**Prerequisites:** Python 3.10+

```bash
# Clone and setup
git clone https://github.com/dinosmuc/habit-tracker.git
cd habit-tracker

# Option 1: With pip (no Poetry required)
pip install flask sqlalchemy alembic pandas python-dotenv
python -m alembic upgrade head
python seed.py
flask run

# Option 2: With Poetry
poetry install
poetry run alembic upgrade head
poetry run python seed.py
poetry run flask run
```

**Visit:** http://localhost:5000

**Run tests:** `pytest` (with pip) or `poetry run pytest` (with Poetry)

---

## Features

- Create, update, delete daily/weekly habits
- Mark habits as complete with duplicate prevention
- Analytics: completion rates, streaks, struggling habits
- REST API for programmatic access
- Sample data included for testing

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Alembic
- **Database:** SQLite with foreign key constraints
- **Analytics:** Pandas for data analysis
- **Testing:** Pytest (94 tests)
- **Deployment:** Docker

## Main API Endpoints

- `GET /api/habits` - List all habits
- `POST /api/habits` - Create new habit
- `POST /api/habits/{id}/checkoff` - Mark habit complete
- `GET /api/analytics/habits` - Get habits with analytics
- `GET /api/analytics/habits/struggled` - Get struggling habits

---
