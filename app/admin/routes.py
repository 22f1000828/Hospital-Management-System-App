from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.orm import joinedload
from app import db, cache
from app.models import User, Doctor, Patient, Appointment, Treatment, Department
from app.admin.forms import DoctorForm, PatientSearchForm, DoctorSearchForm, AppointmentSearchForm
from app.admin import bp
from datetime import datetime, date, timedelta

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    total_patients = Patient.query.filter_by(is_active=True).count()
    total_doctors = Doctor.query.filter_by(is_active=True).count()
    total_appointments = Appointment.query.count()
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= date.today(),
        Appointment.status == 'Booked'
    ).count()
    past_appointments = Appointment.query.filter(
        Appointment.appointment_date < date.today()
    ).count()
    
    recent_appointments = Appointment.query.filter(
        Appointment.appointment_date >= date.today()
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_appointments=total_appointments,
                         upcoming_appointments=upcoming_appointments,
                         past_appointments=past_appointments,
                         recent_appointments=recent_appointments)

@bp.route('/doctors', methods=['GET', 'POST'])
@admin_required
def doctors():
    """View and manage doctors"""
    form = DoctorSearchForm()
    departments = Department.query.order_by(Department.name).all()
    form.specialization_id.choices = [('', 'All')] + [(d.id, d.name) for d in departments]
    
    doctors_query = Doctor.query.join(User).filter(Doctor.is_active.is_(True))
    
    if form.validate_on_submit():
        search_term = form.search_query.data
        specialization_id = form.specialization_id.data
        
        if search_term:
            doctors_query = doctors_query.filter(
                (Doctor.first_name.contains(search_term)) |
                (Doctor.last_name.contains(search_term)) |
                (User.username.contains(search_term))
            )
        
        if specialization_id is not None:
            doctors_query = doctors_query.filter(Doctor.specialization_id == specialization_id)
    
    doctors_list = doctors_query.options(
        joinedload(Doctor.user),
        joinedload(Doctor.department)
    ).all()
    
    return render_template('admin/doctors.html', doctors=doctors_list, form=form)

@bp.route('/doctors/add', methods=['GET', 'POST'])
@admin_required
def add_doctor():
    """Add new doctor"""
    form = DoctorForm()
    
    if not form.specialization_id.choices:
        departments = Department.query.order_by(Department.name).all()
        form.specialization_id.choices = [(d.id, d.name) for d in departments]
    
    if form.validate_on_submit():
        # Check if user exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('admin/doctor_form.html', form=form, title='Add Doctor')
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'danger')
            return render_template('admin/doctor_form.html', form=form, title='Add Doctor')
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='Doctor',
            is_active=True
        )
        password = form.password.data or 'doctor123'  # Default password
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            specialization_id=form.specialization_id.data,
            phone=form.phone.data,
            license_number=form.license_number.data,
            is_active=True
        )
        db.session.add(doctor)
        db.session.commit()
        
        flash(f'Doctor {doctor.full_name} added successfully. Default password: {password}', 'success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/doctor_form.html', form=form, title='Add Doctor')

@bp.route('/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_doctor(doctor_id):
    """Edit doctor"""
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm(obj=doctor.user)
    form.doctor_id = doctor_id
    
    if not form.specialization_id.choices:
        departments = Department.query.order_by(Department.name).all()
        form.specialization_id.choices = [(d.id, d.name) for d in departments]
    
    if request.method == 'GET':
        form.first_name.data = doctor.first_name
        form.last_name.data = doctor.last_name
        form.specialization_id.data = doctor.specialization_id
        form.phone.data = doctor.phone
        form.license_number.data = doctor.license_number
    
    if form.validate_on_submit():
        doctor.user.username = form.username.data
        doctor.user.email = form.email.data
        if form.password.data:
            doctor.user.set_password(form.password.data)
        
        doctor.first_name = form.first_name.data
        doctor.last_name = form.last_name.data
        doctor.specialization_id = form.specialization_id.data
        doctor.phone = form.phone.data
        doctor.license_number = form.license_number.data
        
        db.session.commit()
        flash('Doctor updated successfully', 'success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/doctor_form.html', form=form, doctor=doctor, title='Edit Doctor')

@bp.route('/doctors/<int:doctor_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_doctor(doctor_id):
    """Deactivate/blacklist doctor"""
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_active = False
    doctor.user.is_active = False
    db.session.commit()
    flash(f'Doctor {doctor.full_name} has been deactivated', 'success')
    return redirect(url_for('admin.doctors'))

@bp.route('/patients', methods=['GET', 'POST'])
@admin_required
def patients():
    """View and manage patients - with caching"""
    form = PatientSearchForm()
    
    query = form.search_query.data if form.validate_on_submit() else request.args.get('query', '')
    
    # Create cache key
    cache_key = f'admin_patient_search_{query}'
    patients_list = cache.get(cache_key)
    
    if patients_list is None:
        # Eagerly load user relationship to avoid N+1 queries
        if form.validate_on_submit() or query:
            if query:
                patients_list = Patient.query.join(User).filter(
                    (Patient.first_name.contains(query)) |
                    (Patient.last_name.contains(query)) |
                    (User.username.contains(query)) |
                    (Patient.phone.contains(query))
                ).filter_by(is_active=True).options(joinedload(Patient.user)).all()
            else:
                patients_list = Patient.query.filter_by(is_active=True).options(joinedload(Patient.user)).all()
        else:
            patients_list = Patient.query.filter_by(is_active=True).options(joinedload(Patient.user)).all()
        
        # Cache for 5 minutes
        cache.set(cache_key, patients_list, timeout=300)
    
    return render_template('admin/patients.html', patients=patients_list, form=form)

@bp.route('/patients/<int:patient_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_patient(patient_id):
    """Deactivate/blacklist patient"""
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = False
    patient.user.is_active = False
    db.session.commit()
    flash(f'Patient {patient.full_name} has been deactivated', 'success')
    return redirect(url_for('admin.patients'))

@bp.route('/appointments', methods=['GET', 'POST'])
@admin_required
def appointments():
    """View and manage all appointments"""
    form = AppointmentSearchForm()
    appointments_list = Appointment.query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    if form.validate_on_submit():
        query = form.search_query.data
        status = form.status.data
        
        if query:
            appointments_list = Appointment.query.join(Patient).join(Doctor).filter(
                (Patient.first_name.contains(query)) |
                (Patient.last_name.contains(query)) |
                (Doctor.first_name.contains(query)) |
                (Doctor.last_name.contains(query))
            ).all()
        
        if status:
            appointments_list = [a for a in appointments_list if a.status == status]
    
    return render_template('admin/appointments.html', appointments=appointments_list, form=form)

@bp.route('/patients/<int:patient_id>/history')
@admin_required
def patient_history(patient_id):
    """View patient treatment history"""
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('admin/patient_history.html', patient=patient, appointments=appointments)

