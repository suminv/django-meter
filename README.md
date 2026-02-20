# Meter Management System

Meter Management System is a Django web app for tracking utility meter readings.
It supports user accounts, profile management, meter history, and period-based consumption analytics.

## Tech Stack

- Python 3.11+ (project tested with 3.13)
- Django 5.x
- SQLite (default)
- django-crispy-forms + crispy-bootstrap5
- Chart.js (history charts)

## Main Features

- User registration, login, logout
- Create and edit meter readings (`meter_1 ... meter_5`)
- Validation rules:
  - values must be non-negative
  - new readings cannot be less than previous readings
- Profile create/edit (with sync to Django `User` identity fields)
- Profile dashboard:
  - latest and previous readings
  - difference statuses (`Normal`, `High spike`, `Low usage`, `Decrease`)
  - 30-day totals and average/day
  - latest 5 records
- History page:
  - period filter (`7/30/90/180/365/all`)
  - grouped consumption chart by period
  - per-meter summary (`total`, `average/day`, `trend`)

## Installation

1. Clone repository:

```bash
git clone https://github.com/suminv/django-meter.git
cd django-meter
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables (optional for local dev):

```bash
export SECRET_KEY='your-secret-key'
export DEBUG='True'
export ALLOWED_HOSTS='localhost,127.0.0.1'
```

5. Apply migrations:

```bash
python manage.py migrate
```

6. Create superuser (optional):

```bash
python manage.py createsuperuser
```

7. Run dev server:

```bash
python manage.py runserver
```

## Tests

Run all tests:

```bash
python manage.py test
```

Run app tests only:

```bash
python manage.py test add_meters.tests -v 2
```

## License

MIT License. See `LICENCE`.


