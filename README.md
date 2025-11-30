# Hospital Management System (HMS)

A comprehensive Flask-based Hospital Management System with role-based access control for Admin, Doctor, and Patient users.

## Features

### Milestone 1: Database Models and Schema ✅

- **User Model**: Role-based user system (Admin/Doctor/Patient)
- **Doctor Model**: Specialization, availability, contact information
- **Patient Model**: Profile, contact, emergency contact details
- **Appointment Model**: Links doctors and patients with date, time, and status
- **Treatment Model**: Diagnosis, prescription, and notes for appointments
- **Department Model**: Specializations/departments
- **Relationships**: Proper 1:N and N:N relationships implemented
- **Admin Initialization**: Script to pre-create Admin user

### Milestone 2: Authentication and Role-Based Access ✅

- Flask-Login based authentication
- Patient self-registration
- Doctor and Admin login only (doctors added by Admin)
- Role-specific dashboard redirects after login
- Session management with remember me functionality

### Milestone 3: Admin Dashboard and Management ✅

- Dashboard with statistics (patients, doctors, appointments)
- Add and update doctor profiles
- Search doctors by name/specialization
- Search patients by name/ID/contact
- View and manage all appointments
- Blacklist/deactivate doctors and patients
- View patient treatment history

### Milestone 4: Doctor Dashboard & Management ✅

- Dashboard showing upcoming appointments (day/week)
- View list of assigned patients
- Mark appointments as completed or cancelled
- Enter diagnosis, prescriptions, and notes
- Update availability for next 7 days
- Access full patient medical history

### Milestone 5: Patient Dashboard and Appointment System ✅

- Patient registration and profile management
- View and search doctors by specialization or name
- Book appointments (based on doctor availability)
- Reschedule appointments
- Cancel appointments
- View upcoming and past appointments
- View treatment history with diagnosis and prescriptions

### Milestone 6: Appointment History and Conflict Prevention ✅

- Complete appointment and treatment history storage
- Double booking prevention (unique constraint on doctor + date + time)
- Status management (Booked / Completed / Cancelled)
- Access control: Admin and Doctor can view patient records; Patients view own records

### Milestone 7: Backend Jobs - Daily Reminders & Monthly Reports ✅

- **Celery + Redis Setup**: Configured Celery workers and Beat scheduler with Redis
- **Daily Reminder Job**: Automatically sends email reminders to patients with same-day appointments (runs daily at 8:00 AM)
- **Monthly Report Job**: Generates HTML/PDF monthly reports for doctors with appointments, treatments, and diagnosis summary (runs on 1st of each month)
- **CSV Export Job**: Asynchronous patient treatment history export with email notification when complete
- **Task Management**: All background jobs run asynchronously using Celery workers

### Milestone 8: API Performance Optimization & Caching ✅

- **Redis Caching**: Implemented Redis caching for frequently accessed endpoints
- **Cached Endpoints**:
  - Doctor availability queries (cached for 30 minutes - 1 hour)
  - Patient search results (cached for 5-10 minutes)
  - Doctor search results (cached for 10 minutes)
  - Patient dashboard data (cached for 5 minutes)
- **Cache Invalidation**: Automatic cache invalidation when appointments, availability, or patient data changes
- **Performance**: Significantly reduced database queries and improved response times

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment** (recommended):

```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
python -m pip install -r requirements.txt(wsl)
```

4. **Install and start Redis**:

   ```bash
   sudo apt-get install redis-server
   redis-server
   ```

5. **Start MailHog (for email testing)**:

   ```bash
   wget https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64
   chmod +x MailHog_linux_amd64
   sudo mv MailHog_linux_amd64 /usr/local/bin/mailhog
   mailhog
   ```

   Access web UI: <http://localhost:8025>

6. **Initialize the database and create admin user**:

```bash
python init_admin.py
```

This will:

- Create all database tables
- Create default admin user (username: `admin`, password: `admin123`)
- Create default departments (Cardiology, Neurology, Orthopedics, Pediatrics, Dermatology, General Medicine)

7. **Start the application**:

   **Option A: Development (all in one terminal)**

   ```bash
   python app.py
   ```

   **Option B: Production (separate terminals)**

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

The application will be available at `http://localhost:5000`

## Default Credentials

- **Admin**:
  - Username: `admin`
  - Password: `admin123`

## Usage

### For Admins

1. Login with admin credentials
2. Add doctors through "Doctors" menu
3. Manage patients and appointments
4. View system statistics on dashboard

### For Doctors

1. Login with credentials provided by Admin
2. Set availability for next 7 days
3. View and manage appointments
4. Enter treatment details after appointments
5. View patient medical history

### For Patients

1. Register as a new patient
2. Login with your credentials
3. Search for doctors
4. Book appointments based on doctor availability
5. View appointment history and treatment records

## Project Structure

```
MAD2 PROJ/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── admin/               # Admin blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── doctor/              # Doctor blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── patient/             # Patient blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── auth/                # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── main/                # Main routes
│   │   ├── __init__.py
│   │   └── routes.py
│   └── templates/           # HTML templates
│       ├── base.html
│       ├── auth/
│       ├── admin/
│       ├── doctor/
│       └── patient/
├── config.py                # Configuration
├── init_admin.py            # Database initialization script
├── app.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Database Models

- **User**: Authentication and role management
- **Doctor**: Doctor profiles with specialization
- **Patient**: Patient profiles with contact information
- **Department**: Specializations/departments
- **Appointment**: Links doctors and patients
- **Treatment**: Diagnosis, prescription, notes
- **DoctorAvailability**: Doctor availability slots

## Security Features

- Password hashing using Werkzeug
- Role-based access control
- CSRF protection (Flask-WTF)
- Session management
- Account deactivation capability

## Technologies Used

- **Flask**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Flask-Login**: User session management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation
- **Bootstrap 5**: UI framework
- **SQLite**: Database (default, can be changed to PostgreSQL/MySQL)
- **Celery**: Distributed task queue for background jobs
- **Redis**: Message broker and caching layer
- **Flask-Mail**: Email functionality for reminders and notifications
- **Flask-Caching**: Redis-based caching for API optimization
- **Pandas**: Data processing for CSV exports
- **WeasyPrint**: PDF generation for monthly reports

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start Redis**: `redis-server` (in a separate terminal)
3. **Initialize database**: `python init_admin.py`
4. **Start Celery Worker**:

   ```bash
   celery -A celery_app worker --loglevel=info
   ```

5. **Start Celery Beat**: `celery -A celery_app beat --loglevel=info` (for scheduled tasks)
6. **Run application**: `python app.py`
7. **Access**: <http://localhost:5000>

**Default Admin**: username: `admin`, password: `admin123`

## Background Jobs

### Daily Reminders

- Runs automatically every day at 8:00 AM IST
- Sends email reminders to patients with appointments scheduled for the same day
- Configure email settings in `.env` file or `config.py`

### Monthly Reports

- Runs automatically on the 1st of each month at 9:00 AM IST
- Generates HTML and PDF reports for all active doctors
- Reports include:
  - Appointment statistics (total, completed, cancelled, booked)
  - Treatment details and diagnoses
  - Diagnosis summary
- Reports are emailed to doctors and saved in `instance/reports/`

### CSV Export

- Triggered by patients from their treatment history page
- Exports complete treatment history as CSV
- Email notification sent when export is ready
- Files saved in `instance/exports/`

## Caching

The application uses Redis caching to optimize frequently accessed endpoints:

- **Doctor Availability**: Cached for 30 minutes - 1 hour
- **Patient Search**: Cached for 5 minutes
- **Doctor Search**: Cached for 10 minutes
- **Dashboard Data**: Cached for 5 minutes

Cache is automatically invalidated when:

- Appointments are created, updated, or cancelled
- Doctor availability is modified
- Patient or doctor data changes
