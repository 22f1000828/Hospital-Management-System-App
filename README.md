# Hospital Management System

A web-based hospital management system built with Flask REST API and Vue.js frontend, featuring role-based access control for Admin, Doctor, and Patient users.

## Tech Stack

- Flask: REST API backend using Flask-RESTful
- Vue.js: Frontend framework (CDN-based)
- Jinja2: Single entry point HTML template only
- Bootstrap 5: UI styling framework
- SQLite: Database
- Redis: Caching and message broker for Celery
- Celery: Background job processing

## Features

- Role-based authentication system with separate login pages for Admin, Doctor, and Patient
- Admin dashboard for managing doctors, patients, and appointments
- Doctor dashboard for managing appointments, entering treatment details, and setting availability
- Patient dashboard for booking appointments, viewing treatment history, and exporting CSV reports
- Appointment scheduling with conflict prevention
- Background jobs for daily appointment reminders and monthly doctor reports
- Asynchronous CSV export of patient treatment history with email notification
- Redis caching for API performance optimization

## Installation

1. Clone the repository or navigate to the project directory

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

If you encounter an "externally-managed-environment" error:
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

5. Start MailHog for email testing (optional):

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

The application will be available at http://127.0.0.1:5000

## Default Credentials

- Admin Username: admin
- Admin Password: admin123

## Project Structure

```
.
├── app/
│   ├── api/              # Flask-RESTful API endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── admin.py      # Admin endpoints
│   │   ├── doctor.py     # Doctor endpoints
│   │   ├── patient.py    # Patient endpoints
│   │   ├── common.py     # Common endpoints
│   │   └── utils.py      # API utilities and decorators
│   ├── main/             # Main blueprint
│   ├── models.py         # SQLAlchemy models
│   ├── tasks.py          # Celery background tasks
│   └── templates/        # Jinja2 templates
│       └── index.html    # Single entry point
├── static/
│   └── js/
│       ├── app.js        # Vue.js application and router
│       ├── api/          # API client modules
│       └── components/   # Vue.js components
├── instance/
│   ├── hospital.db       # SQLite database
│   └── exports/          # CSV export files
├── app.py                # Application entry point
├── celery_app.py         # Celery configuration
├── config.py             # Application configuration
└── init_admin.py         # Database initialization script
```

## API Endpoints

All API endpoints are prefixed with `/api` and use Flask-RESTful Resource classes:

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/register` - Patient registration
- `GET /api/auth/me` - Get current user information

### Admin
- `GET /api/admin/dashboard` - Dashboard statistics
- `GET /api/admin/doctors` - List all doctors
- `POST /api/admin/doctors` - Add new doctor
- `PUT /api/admin/doctors/<id>` - Update doctor information
- `POST /api/admin/doctors/<id>/deactivate` - Deactivate doctor account
- `GET /api/admin/patients` - List all patients
- `POST /api/admin/patients/<id>/deactivate` - Deactivate patient account
- `GET /api/admin/appointments` - List all appointments
- `GET /api/admin/patients/<id>/history` - View patient treatment history

### Doctor
- `GET /api/doctor/dashboard` - Dashboard with today's and week's appointments
- `GET /api/doctor/appointments` - List doctor's appointments
- `GET /api/doctor/appointments/<id>` - Get appointment details
- `PUT /api/doctor/appointments/<id>/status` - Update appointment status
- `POST /api/doctor/appointments/<id>/treatment` - Add treatment details
- `GET /api/doctor/patients` - List assigned patients
- `GET /api/doctor/patients/<id>/history` - View patient history
- `GET /api/doctor/availability` - Get doctor availability schedule
- `POST /api/doctor/availability` - Set availability slot
- `DELETE /api/doctor/availability/<id>` - Delete availability slot

### Patient
- `GET /api/patient/dashboard` - Dashboard with upcoming appointments
- `GET /api/patient/profile` - Get patient profile
- `PUT /api/patient/profile` - Update patient profile
- `GET /api/patient/doctors` - Search and list available doctors
- `GET /api/patient/doctors/<id>/availability` - Get doctor availability
- `POST /api/patient/appointments` - Book new appointment
- `GET /api/patient/appointments` - List patient's appointments
- `GET /api/patient/appointments/<id>` - Get appointment details
- `POST /api/patient/appointments/<id>/cancel` - Cancel appointment
- `PUT /api/patient/appointments/<id>` - Reschedule appointment
- `GET /api/patient/history` - View treatment history
- `POST /api/patient/history/export` - Export treatment history as CSV
- `GET /api/patient/exports/<path:filename>` - Download exported CSV file

### Common
- `GET /api/departments` - List all departments

## Background Jobs

The system uses Celery for asynchronous task processing:

- **Daily Reminders**: Sends email reminders to patients with same-day appointments (runs daily at 8:00 AM IST)
- **Monthly Reports**: Generates HTML and PDF reports for doctors summarizing their monthly activities (runs on 1st of each month at 9:00 AM IST)
- **CSV Export**: Asynchronous patient treatment history export with email notification containing secure download link

## Configuration

Set environment variables or modify `config.py`:

- `BASE_URL`: Base URL for email links (default: http://127.0.0.1:5000)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379/0)
- `MAIL_SERVER`: Email server address (default: localhost)
- `MAIL_PORT`: Email server port (default: 1025 for MailHog)
- `SECRET_KEY`: Flask secret key for session management


## Usage

1. Access the application at http://127.0.0.1:5000
2. Use the home page to navigate to role-specific login pages
3. Admin can manage doctors, patients, and view all appointments
4. Doctors can manage their appointments, add treatment details, and set availability
5. Patients can book appointments, view treatment history, and export CSV reports
6. Background jobs run automatically via Celery Beat scheduler
