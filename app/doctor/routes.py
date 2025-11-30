from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta, time
from app import db, cache
from app.models import Doctor, Patient, Appointment, Treatment, DoctorAvailability
from app.doctor.forms import AvailabilityForm, TreatmentForm, AppointmentStatusForm
from app.doctor import bp

def doctor_required(f):
    """Decorator to require doctor role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Doctor':
            flash('Access denied. Doctor privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@doctor_required
def dashboard():
    """Doctor dashboard with upcoming appointments"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    
    today = date.today()
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=today,
        status='Booked'
    ).order_by(Appointment.appointment_time).all()
    
    # Week's appointments
    week_start = today
    week_end = today + timedelta(days=7)
    week_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= week_start,
        Appointment.appointment_date <= week_end,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    # Assigned patients (unique patients with appointments)
    patient_ids = db.session.query(Appointment.patient_id).filter_by(
        doctor_id=doctor.id
    ).distinct().all()
    patient_ids = [p[0] for p in patient_ids]
    assigned_patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         week_appointments=week_appointments,
                         assigned_patients=assigned_patients)

@bp.route('/appointments')
@doctor_required
def appointments():
    """View all appointments"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    
    status = request.args.get('status', '')
    appointments_list = Appointment.query.filter_by(doctor_id=doctor.id)
    
    if status:
        appointments_list = appointments_list.filter_by(status=status)
    
    appointments_list = appointments_list.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('doctor/appointments.html',
                         appointments=appointments_list,
                         doctor=doctor,
                         current_status=status)

@bp.route('/appointments/<int:appointment_id>', methods=['GET', 'POST'])
@doctor_required
def appointment_detail(appointment_id):
    """View and manage appointment details"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != doctor.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    reset_form = request.args.get('reset_form') == '1'
    
    status_form = AppointmentStatusForm()
    treatment_form = TreatmentForm()
    
    if request.method == 'GET':
        status_form = AppointmentStatusForm(obj=appointment)
        if treatment and not reset_form:
            treatment_form = TreatmentForm(obj=treatment)
    
    status_submitted = 'submit_status' in request.form
    treatment_submitted = 'submit_treatment' in request.form
    
    if status_submitted and status_form.validate():
        appointment.status = status_form.status.data
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Appointment status updated', 'success')
        return redirect(url_for('doctor.appointment_detail', appointment_id=appointment_id))
    
    if treatment_submitted and treatment_form.validate():
        if treatment:
            treatment.diagnosis = treatment_form.diagnosis.data
            treatment.prescription = treatment_form.prescription.data
            treatment.notes = treatment_form.notes.data
            treatment.updated_at = datetime.utcnow()
        else:
            treatment = Treatment(
                appointment_id=appointment_id,
                diagnosis=treatment_form.diagnosis.data,
                prescription=treatment_form.prescription.data,
                notes=treatment_form.notes.data
            )
            db.session.add(treatment)
        
        # Mark appointment as completed if treatment is added
        if appointment.status == 'Booked':
            appointment.status = 'Completed'
            appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Treatment details saved', 'success')
        return redirect(url_for('doctor.appointment_detail', appointment_id=appointment_id, reset_form=1))
    
    return render_template('doctor/appointment_detail.html',
                         appointment=appointment,
                         treatment=treatment,
                         status_form=status_form,
                         treatment_form=treatment_form)

@bp.route('/patients')
@doctor_required
def patients():
    """View list of assigned patients"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    
    patient_ids = db.session.query(Appointment.patient_id).filter_by(
        doctor_id=doctor.id
    ).distinct().all()
    patient_ids = [p[0] for p in patient_ids]
    patients_list = Patient.query.filter(Patient.id.in_(patient_ids)).all()
    
    return render_template('doctor/patients.html', patients=patients_list, doctor=doctor)

@bp.route('/patients/<int:patient_id>/history')
@doctor_required
def patient_history(patient_id):
    """View patient medical history"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    patient = Patient.query.get_or_404(patient_id)
    
    appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        patient_id=patient_id
    ).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('doctor/patient_history.html',
                         patient=patient,
                         appointments=appointments,
                         doctor=doctor)

@bp.route('/availability', methods=['GET', 'POST'])
@doctor_required
def availability():
    """Manage availability for next 7 days"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    form = AvailabilityForm()
    
    today = date.today()
    next_7_days = today + timedelta(days=7)
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= next_7_days
    ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
    
    if form.validate_on_submit():
        # Check if date is within next 7 days
        if form.date.data < today or form.date.data > next_7_days:
            flash('Availability can only be set for the next 7 days', 'danger')
            return redirect(url_for('doctor.availability'))
        
        # Check for conflicts
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            date=form.date.data,
            start_time=form.start_time.data
        ).first()
        
        if existing:
            flash('This time slot already exists', 'danger')
            return redirect(url_for('doctor.availability'))
        
        availability = DoctorAvailability(
            doctor_id=doctor.id,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            is_available=True
        )
        db.session.add(availability)
        db.session.commit()
        
        # Invalidate cache for doctor availability
        cache_key = f'doctor_{doctor.id}_availability_{form.date.data}'
        cache.delete(cache_key)
        cache_key_summary = f'doctor_availability_{date.today().isoformat()}'
        cache.delete(cache_key_summary)
        
        flash('Availability added successfully', 'success')
        return redirect(url_for('doctor.availability'))
    
    return render_template('doctor/availability.html',
                         form=form,
                         availabilities=availabilities,
                         doctor=doctor)

@bp.route('/availability/<int:availability_id>/delete', methods=['POST'])
@doctor_required
def delete_availability(availability_id):
    """Delete availability slot"""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    availability = DoctorAvailability.query.get_or_404(availability_id)
    
    if availability.doctor_id != doctor.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor.availability'))
    
    db.session.delete(availability)
    db.session.commit()
    flash('Availability removed', 'success')
    return redirect(url_for('doctor.availability'))

