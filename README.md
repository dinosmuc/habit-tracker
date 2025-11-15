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
✅ Includes simple web UI for habit management

---

## 🐳 Alternative Docker Commands

```bash
# Run in background
docker run -d -p 5000:5000 --name habit-tracker dinosmuc/habit-tracker:latest

# Build locally
git clone https://github.com/dinosmuc/habit-tracker.git
cd habit-tracker
docker build -t habit-tracker .
docker run -p 5000:5000 habit-tracker

# Development with docker-compose
docker-compose up
```

---

## 💻 Local Development (Without Docker)

**Prerequisites:** Python 3.10 or 3.11

```bash
# Clone and setup
git clone https://github.com/dinosmuc/habit-tracker.git
cd habit-tracker

## Linux

# Option 1: With pip (no Poetry required) 
pip install flask sqlalchemy alembic pandas python-dotenv pytest
python3 -m alembic upgrade head
python3 seed.py
flask --app habittracker.app:create_app run

# Option 2: With Poetry
poetry install
poetry run alembic upgrade head
poetry run python seed.py
poetry run flask --app habittracker.app:create_app run

## Windows

# Option 1: With pip (no Poetry requred)
pip install flask sqlalchemy alembic pandas python-dotenv pytest
python -m alembic upgrade head
python seed.py
flask --app habittracker.app:create_app run

# Option 2: With Poetry
poetry install
poetry run alembic upgrade head
poetry run python seed.py
poetry run flask --app habittracker.app:create_app run

```

**Visit:** http://localhost:5000

---

## Features

- Create, update, delete daily/weekly habits
- Mark habits as complete with duplicate prevention within the defined period
- Analytics:
  - Overall completion rates per habit
  - Current and longest streak calculation per habit
  - Identification of struggling habits based on customizable thresholds
  - Best and worst day analysis for weekly habits
- REST API for programmatic access and integration
- Simple web interface for easy interaction
- Web Interface:
  - View all habits with real-time completion status
  - Add, edit, and delete habits
  - One-click habit check-off
  - Visual analytics dashboard
- Sample data generation included for quick testing and demonstration

## Tech Stack

- **Backend:** Flask, SQLAlchemy (ORM), Alembic (Migrations)
- **Database:** SQLite (with enforced foreign key constraints)
- **Analytics:** Pandas
- **Testing:** Pytest (94 tests covering models, services, API, and analytics)
- **Frontend:** HTML, CSS, JavaScript (Vanilla) - served by Flask
- **Deployment:** Docker, Docker Compose
- **CI/CD:** GitHub Actions (Python 3.11, linting with Ruff & Black, 94 tests with Pytest)

## Testing 🧪

To ensure the reliability and robustness of the Habit Tracker application, a comprehensive suite of unit tests has been developed using Pytest. These tests cover critical components, including:

- **API Endpoints:** Verifying correct request/response handling, status codes, and data integrity.
- **Service Layer:** Ensuring business logic functions as expected (e.g., habit creation, completion, updates, streak logic).
- **Database Models & Interactions:** Validating data storage, relationships, and constraints.
- **Analytics Module:** Confirming accuracy of calculations (e.g., streaks, completion rates, struggled habits, day analysis).

### How to Run Tests:

Ensure you have installed the development dependencies (pytest). Navigate to the project's root directory and use one of the following commands:

**With pip (if pytest installed globally or in venv):**
```bash
pytest
```

**With Poetry:**
```bash
poetry run pytest
```

Continuous integration (CI) is also configured via GitHub Actions to automatically run linters (ruff, black) and the full pytest suite on every push and pull request to the main branch, ensuring code quality and test coverage throughout development.

## API Endpoints

- `GET /api/habits` - List all habits (optionally filter by ?periodicity=daily|weekly)
- `POST /api/habits` - Create a new habit (Body: {"name": "...", "periodicity": "daily|weekly"})
- `GET /api/habits/{id}` - Get details of a single habit
- `PUT /api/habits/{id}` - Update a habit (Body: {"name": "...", "periodicity": "..."})
- `DELETE /api/habits/{id}` - Delete a habit
- `POST /api/habits/{id}/checkoff` - Mark a habit as complete for the current period
- `GET /api/habits/{id}/completed` - Check if a habit is completed for the current period
- `GET /api/analytics/habits` - Get habits list including analytics data
- `GET /api/analytics/habits/{id}/streaks` - Get current and longest streak for a habit
- `GET /api/analytics/habits/struggled` - Get struggling habits (uses stored or query param thresholds)
- `GET /api/analytics/habits/completion-rates` - Get overall completion rates for all habits
- `GET /api/analytics/habits/{id}/best-worst-day` - Get best/worst completion day for a weekly habit
- `GET /api/preferences` - Get user analytics preferences
- `PUT /api/preferences` - Update user analytics preferences (Body: {"struggle_threshold": 0.X, "show_bottom_percent": 0.Y})

---
