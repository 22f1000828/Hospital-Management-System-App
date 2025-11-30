# Hospital Management System

A Flask-based web application for managing hospital operations with role-based access control for Admin, Doctor, and Patient users.

## Features

- Role-based authentication system (Admin, Doctor, Patient)
- Admin dashboard for managing doctors, patients, and appointments
- Doctor dashboard for managing appointments and entering treatment details
- Patient dashboard for booking appointments and viewing treatment history
- Appointment scheduling with conflict prevention
- Background jobs for daily reminders and monthly reports
- CSV export of patient treatment history
- Redis caching for performance optimization

## Installation

1. Clone the repository or navigate to the project directory

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

For WSL users, if you encounter an "externally-managed-environment" error:
```bash
python -m pip install -r requirements.txt
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install and start Redis:

```bash
sudo apt-get install redis-server
redis-server
```

5. Start MailHog for email testing :

```bash
wget https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64
chmod +x MailHog_linux_amd64
sudo mv MailHog_linux_amd64 /usr/local/bin/mailhog
mailhog
```

6. Initialize the database:

```bash
python init_admin.py
```

This creates the database tables, default admin user (username: admin, password: admin123), and default departments.

7. Start the application:

Terminal 1 - Flask Application:
```bash
python app.py
```

Terminal 2 - Celery Worker:
```bash
celery -A celery_app worker --loglevel=info
```

Terminal 3 - Celery Beat (for scheduled tasks):
```bash
celery -A celery_app beat --loglevel=info
```

The application will be available at http://localhost:5000

## Default Credentials

- Admin Username: admin
- Admin Password: admin123

## Technologies Used

- Flask: Web framework
- SQLAlchemy: ORM for database operations
- Flask-Login: User session management
- Flask-WTF: Form handling and CSRF protection
- Bootstrap 5: UI framework
- SQLite: Database
- Celery: Distributed task queue for background jobs
- Redis: Message broker and caching layer
- Flask-Mail: Email functionality
- Flask-Caching: Redis-based caching
- Pandas: Data processing for CSV exports
- WeasyPrint: PDF generation for monthly reports

## Background Jobs

- Daily Reminders: Sends email reminders to patients with same-day appointments (runs daily at 8:00 AM IST)
- Monthly Reports: Generates HTML and PDF reports for doctors (runs on 1st of each month at 9:00 AM IST)
- CSV Export: Asynchronous patient treatment history export with email notification

## Configuration

Set environment variables or modify config.py:
- BASE_URL: Base URL for email links (default: http://localhost:5000)
- DATABASE_URL: Database connection string
- REDIS_URL: Redis connection string
- MAIL_SERVER: Email server address
- SECRET_KEY: Flask secret key
