from flask import render_template, redirect, url_for, flash, request, send_file, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from sqlalchemy.orm import joinedload
from app import db, cache
from app.models import User, Doctor, Patient, Appointment, Treatment, Department, DoctorAvailability
from app.patient.forms import PatientProfileForm, AppointmentBookingForm, DoctorSearchForm
from app.patient import bp
import os

def patient_required(f):
    """Decorator to require patient role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Patient':
            flash('Access denied. Patient privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@patient_required
def dashboard():
    """Patient dashboard"""
    try:
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        
        upcoming_appointments = Appointment.query.filter_by(
            patient_id=patient.id,
            status='Booked'
        ).filter(
            Appointment.appointment_date >= date.today()
        ).options(
            joinedload(Appointment.doctor).joinedload(Doctor.department),
            joinedload(Appointment.doctor).joinedload(Doctor.user)
        ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
        
        past_appointments = Appointment.query.filter_by(
            patient_id=patient.id
        ).filter(
            (Appointment.appointment_date < date.today()) |
            (Appointment.status.in_(['Completed', 'Cancelled']))
        ).options(
            joinedload(Appointment.doctor).joinedload(Doctor.department),
            joinedload(Appointment.doctor).joinedload(Doctor.user)
        ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).limit(10).all()
        
        departments = Department.query.order_by(Department.name).all()
        
        today = date.today()
        next_7_days = today + timedelta(days=7)
        
        available_doctors = Doctor.query.filter_by(is_active=True).options(
            joinedload(Doctor.department),
            joinedload(Doctor.user)
        ).all()
        
        doctor_availability_summary = []
        for doctor in available_doctors:
            availabilities = DoctorAvailability.query.filter(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.date >= today,
                DoctorAvailability.date <= next_7_days,
                DoctorAvailability.is_available == True
            ).count()
            if availabilities > 0:
                doctor_availability_summary.append({
                    'doctor': doctor,
                    'available_slots': availabilities
                })
        
        return render_template('patient/dashboard.html',
                             patient=patient,
                             upcoming_appointments=upcoming_appointments,
                             past_appointments=past_appointments,
                             departments=departments,
                             doctor_availability_summary=doctor_availability_summary,
                             today=today,
                             next_7_days=next_7_days)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        current_app.logger.error(f'Error in patient dashboard: {str(e)}', exc_info=True)
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        return render_template('patient/dashboard.html',
                             patient=patient,
                             upcoming_appointments=[],
                             past_appointments=[],
                             departments=[],
                             doctor_availability_summary=[],
                             today=date.today(),
                             next_7_days=date.today() + timedelta(days=7))

@bp.route('/profile', methods=['GET', 'POST'])
@patient_required
def profile():
    """View and update patient profile"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    form = PatientProfileForm(obj=patient)
    if request.method == 'GET':
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        patient.first_name = form.first_name.data
        patient.last_name = form.last_name.data
        patient.date_of_birth = form.date_of_birth.data
        patient.gender = form.gender.data
        patient.phone = form.phone.data
        patient.address = form.address.data
        patient.emergency_contact = form.emergency_contact.data
        patient.emergency_phone = form.emergency_phone.data
        current_user.email = form.email.data
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('patient.profile'))
    
    return render_template('patient/profile.html', form=form, patient=patient)

@bp.route('/doctors', methods=['GET', 'POST'])
@patient_required
def doctors():
    """Search and view doctors"""
    try:
        form = DoctorSearchForm()
        departments = Department.query.order_by(Department.name).all()
        form.specialization_id.choices = [('', 'All')] + [(d.id, d.name) for d in departments]
        
        query = form.search_query.data if form.validate_on_submit() else request.args.get('query', '')
        specialization_id = form.specialization_id.data if form.validate_on_submit() else request.args.get('specialization_id', type=int)
        if specialization_id == '':
            specialization_id = None
        
        doctors_query = Doctor.query.filter_by(is_active=True).options(
            joinedload(Doctor.user),
            joinedload(Doctor.department)
        )
        
        if query:
            doctors_query = doctors_query.join(User).filter(
                (Doctor.first_name.contains(query)) |
                (Doctor.last_name.contains(query)) |
                (User.username.contains(query))
            )
        
        doctors_list = doctors_query.all()
        
        if specialization_id is not None:
            doctors_list = [d for d in doctors_list if d.specialization_id == specialization_id]
        
        return render_template('patient/doctors.html', doctors=doctors_list, form=form)
    except Exception as e:
        flash(f'Error loading doctors: {str(e)}', 'danger')
        current_app.logger.error(f'Error in doctors route: {str(e)}', exc_info=True)
        return render_template('patient/doctors.html', doctors=[], form=form)

@bp.route('/doctors/<int:doctor_id>/book', methods=['GET', 'POST'])
@patient_required
def book_appointment(doctor_id):
    """Book appointment with doctor"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if not doctor.is_active:
        flash('Doctor is not available', 'danger')
        return redirect(url_for('patient.doctors'))
    
    form = AppointmentBookingForm()
    form.doctor_id.data = doctor_id
    
    selected_date = form.appointment_date.data
    if request.method == 'GET':
        selected_date_str = request.args.get('date')
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = date.today()
        if not selected_date:
            selected_date = date.today()
        form.appointment_date.data = selected_date
    
    available_times = []
    if selected_date:
        cache_key = f'doctor_{doctor_id}_availability_{selected_date}'
        availabilities = cache.get(cache_key)
        
        if availabilities is None:
            availabilities = DoctorAvailability.query.filter_by(
                doctor_id=doctor_id,
                date=selected_date,
                is_available=True
            ).all()
            cache.set(cache_key, availabilities, timeout=1800)
        
        appointments_cache_key = f'doctor_{doctor_id}_appointments_{selected_date}'
        existing_appointments = cache.get(appointments_cache_key)
        
        if existing_appointments is None:
            existing_appointments = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=selected_date,
                status='Booked'
            ).all()
            cache.set(appointments_cache_key, existing_appointments, timeout=300)
        
        booked_times = {a.appointment_time for a in existing_appointments}
        
        for avail in availabilities:
            start = datetime.combine(selected_date, avail.start_time)
            end = datetime.combine(selected_date, avail.end_time)
            current = start
            
            while current < end:
                time_str = current.time().strftime('%H:%M')
                if current.time() not in booked_times:
                    available_times.append((time_str, time_str))
                current += timedelta(minutes=30)
        
        form.appointment_time.choices = available_times
    else:
        form.appointment_time.choices = []
    
    if form.validate_on_submit():
        # Validate doctor_id matches
        try:
            form_doctor_id = int(form.doctor_id.data)
            if form_doctor_id != doctor_id:
                flash('Invalid doctor selection', 'danger')
                return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        except (ValueError, TypeError):
            flash('Invalid doctor selection', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        appointment_time_obj = datetime.strptime(form.appointment_time.data, '%H:%M').time()
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=form.appointment_date.data,
            appointment_time=appointment_time_obj,
            status='Booked'
        ).first()
        
        if existing:
            flash('This time slot is already booked. Please choose another time.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        if form.appointment_date.data < date.today():
            flash('Cannot book appointments in the past', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))
        
        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            appointment_date=form.appointment_date.data,
            appointment_time=appointment_time_obj,
            status='Booked',
            reason=form.reason.data
        )
        db.session.add(appointment)
        db.session.commit()
        
        cache_key = f'doctor_{doctor_id}_appointments_{form.appointment_date.data}'
        cache.delete(cache_key)
        cache_key_avail = f'doctor_{doctor_id}_availability_{form.appointment_date.data}'
        cache.delete(cache_key_avail)
        cache.delete('patient_dashboard')
        
        flash('Appointment booked successfully', 'success')
        return redirect(url_for('patient.dashboard'))
    
    return render_template('patient/book_appointment.html',
                         form=form,
                         doctor=doctor,
                         available_times=available_times)

@bp.route('/appointments')
@patient_required
def appointments():
    """View all appointments"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    
    status = request.args.get('status', '')
    appointments_list = Appointment.query.filter_by(patient_id=patient.id)
    
    if status:
        appointments_list = appointments_list.filter_by(status=status)
    
    appointments_list = appointments_list.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('patient/appointments.html',
                         appointments=appointments_list,
                         patient=patient,
                         current_status=status)

@bp.route('/appointments/<int:appointment_id>')
@patient_required
def appointment_detail(appointment_id):
    """View appointment details"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != patient.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient.appointments'))
    
    treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    
    return render_template('patient/appointment_detail.html',
                         appointment=appointment,
                         treatment=treatment)

@bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@patient_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != patient.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'Booked':
        flash('Only booked appointments can be cancelled', 'danger')
        return redirect(url_for('patient.appointment_detail', appointment_id=appointment_id))
    
    appointment.status = 'Cancelled'
    appointment.updated_at = datetime.utcnow()
    db.session.commit()
    
    cache_key = f'doctor_{appointment.doctor_id}_appointments_{appointment.appointment_date}'
    cache.delete(cache_key)
    cache.delete('patient_dashboard')
    
    flash('Appointment cancelled successfully', 'success')
    return redirect(url_for('patient.appointments'))

@bp.route('/appointments/<int:appointment_id>/reschedule', methods=['GET', 'POST'])
@patient_required
def reschedule_appointment(appointment_id):
    """Reschedule appointment"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != patient.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'Booked':
        flash('Only booked appointments can be rescheduled', 'danger')
        return redirect(url_for('patient.appointment_detail', appointment_id=appointment_id))
    
    form = AppointmentBookingForm()
    form.doctor_id.data = appointment.doctor_id
    
    if request.method == 'GET':
        form.appointment_date.data = appointment.appointment_date
        form.appointment_time.data = appointment.appointment_time.strftime('%H:%M')
        form.reason.data = appointment.reason
    
    selected_date = form.appointment_date.data
    if request.method == 'GET':
        selected_date_str = request.args.get('date')
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = appointment.appointment_date
            form.appointment_date.data = selected_date
    
    available_times = []
    if selected_date:
        availabilities = DoctorAvailability.query.filter_by(
            doctor_id=appointment.doctor_id,
            date=selected_date,
            is_available=True
        ).all()
        
        existing_appointments = Appointment.query.filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == selected_date,
            Appointment.status == 'Booked',
            Appointment.id != appointment_id
        ).all()
        booked_times = {a.appointment_time for a in existing_appointments}
        
        for avail in availabilities:
            start = datetime.combine(selected_date, avail.start_time)
            end = datetime.combine(selected_date, avail.end_time)
            current = start
            
            while current < end:
                time_str = current.time().strftime('%H:%M')
                if current.time() not in booked_times:
                    available_times.append((time_str, time_str))
                current += timedelta(minutes=30)
        
        form.appointment_time.choices = available_times
    else:
        form.appointment_time.choices = []
    
    if form.validate_on_submit():
        existing = Appointment.query.filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == form.appointment_date.data,
            Appointment.appointment_time == datetime.strptime(form.appointment_time.data, '%H:%M').time(),
            Appointment.status == 'Booked',
            Appointment.id != appointment_id
        ).first()
        
        if existing:
            flash('This time slot is already booked. Please choose another time.', 'danger')
            return redirect(url_for('patient.reschedule_appointment', appointment_id=appointment_id))
        
        appointment_time_obj = datetime.strptime(form.appointment_time.data, '%H:%M').time()
        appointment.appointment_date = form.appointment_date.data
        appointment.appointment_time = appointment_time_obj
        appointment.reason = form.reason.data
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        cache_key = f'doctor_{appointment.doctor_id}_appointments_{form.appointment_date.data}'
        cache.delete(cache_key)
        cache.delete('patient_dashboard')
        
        flash('Appointment rescheduled successfully', 'success')
        return redirect(url_for('patient.appointments'))
    
    return render_template('patient/reschedule_appointment.html',
                         form=form,
                         appointment=appointment,
                         available_times=available_times)

@bp.route('/history')
@patient_required
def history():
    """View treatment history"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('patient/history.html', appointments=appointments, patient=patient)

@bp.route('/history/export', methods=['POST'])
@patient_required
def export_history():
    """Trigger CSV export of treatment history"""
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    
    try:
        from celery_app import celery
        
        task = celery.send_task('app.tasks.export_patient_history_csv', args=[patient.id])
        
        flash('Export started. You will receive an email when it is ready.', 'info')
        return jsonify({
            'status': 'success',
            'message': 'Export started',
            'task_id': task.id
        })
    except Exception as e:
        flash(f'Failed to start export: {str(e)}', 'danger')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/exports/<filename>')
@patient_required
def download_export(filename):
    patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
    
    if not filename.startswith(f'patient_{patient.id}_'):
        flash('Access denied', 'danger')
        return redirect(url_for('patient.history'))
    
    from flask import current_app
    exports_dir = os.path.join(current_app.instance_path, 'exports')
    file_path = os.path.join(exports_dir, filename)
    
    if not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('patient.history'))
    
    return send_file(file_path, as_attachment=True, download_name=filename)

