from flask import request, send_file, current_app
from flask_restful import Resource
from flask_login import current_user
from sqlalchemy.orm import joinedload
from datetime import date, datetime, timedelta
from app import db, cache
from app.models import User, Doctor, Patient, Appointment, Treatment, Department, DoctorAvailability
from app.api import api
from app.api.utils import patient_required_api, serialize_doctor, serialize_appointment
import os
import hashlib
import hmac

class PatientDashboard(Resource):
    @patient_required_api
    def get(self):
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
                    'doctor': serialize_doctor(doctor),
                    'available_slots': availabilities
                })
        
        return {
            'patient': {
                'id': patient.id,
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'full_name': patient.full_name
            },
            'upcoming_appointments': [serialize_appointment(a) for a in upcoming_appointments],
            'past_appointments': [serialize_appointment(a) for a in past_appointments],
            'departments': [{'id': d.id, 'name': d.name} for d in departments],
            'doctor_availability_summary': doctor_availability_summary
        }

class PatientProfile(Resource):
    @patient_required_api
    def get(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        
        return {
            'id': patient.id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            'gender': patient.gender,
            'phone': patient.phone,
            'address': patient.address,
            'emergency_contact': patient.emergency_contact_name,
            'emergency_phone': patient.emergency_contact_phone,
            'email': current_user.email
        }
    
    @patient_required_api
    def put(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        data = request.get_json()
        
        if data.get('first_name'):
            patient.first_name = data['first_name']
        if data.get('last_name'):
            patient.last_name = data['last_name']
        if data.get('date_of_birth'):
            patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        if data.get('gender'):
            patient.gender = data['gender']
        if data.get('phone'):
            patient.phone = data['phone']
        if data.get('address'):
            patient.address = data['address']
        if data.get('emergency_contact'):
            patient.emergency_contact_name = data['emergency_contact']
        if data.get('emergency_phone'):
            patient.emergency_contact_phone = data['emergency_phone']
        if data.get('email'):
            current_user.email = data['email']
        
        db.session.commit()
        
        return {'success': True}

class PatientDoctors(Resource):
    @patient_required_api
    def get(self):
        search = request.args.get('search', '')
        specialization_id = request.args.get('specialization_id', type=int)
        
        doctors_query = Doctor.query.filter_by(is_active=True).options(
            joinedload(Doctor.user),
            joinedload(Doctor.department)
        )
        
        if search:
            doctors_query = doctors_query.join(User).filter(
                (Doctor.first_name.contains(search)) |
                (Doctor.last_name.contains(search)) |
                (User.username.contains(search))
            )
        
        doctors_list = doctors_query.all()
        
        if specialization_id:
            doctors_list = [d for d in doctors_list if d.specialization_id == specialization_id]
        
        return {
            'doctors': [serialize_doctor(d) for d in doctors_list]
        }

class PatientDoctorAvailability(Resource):
    @patient_required_api
    def get(self, doctor_id):
        doctor = Doctor.query.get_or_404(doctor_id)
        selected_date_str = request.args.get('date')
        
        if not selected_date_str:
            return {'error': 'Date parameter required'}, 400
        
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        
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
        available_times = []
        
        for avail in availabilities:
            start = datetime.combine(selected_date, avail.start_time)
            end = datetime.combine(selected_date, avail.end_time)
            current = start
            
            while current < end:
                time_str = current.time().strftime('%H:%M')
                if current.time() not in booked_times:
                    available_times.append(time_str)
                current += timedelta(minutes=30)
        
        return {
            'available_times': available_times
        }

class PatientAppointments(Resource):
    @patient_required_api
    def get(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        
        status = request.args.get('status', '')
        appointments_list = Appointment.query.filter_by(patient_id=patient.id)
        
        if status:
            appointments_list = appointments_list.filter_by(status=status)
        
        appointments_list = appointments_list.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        return {
            'appointments': [serialize_appointment(a) for a in appointments_list]
        }
    
    @patient_required_api
    def post(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        req_data = request.get_json()
        
        doctor_id = req_data.get('doctor_id')
        appointment_date = datetime.strptime(req_data.get('appointment_date'), '%Y-%m-%d').date()
        appointment_time = datetime.strptime(req_data.get('appointment_time'), '%H:%M').time()
        reason = req_data.get('reason', '')
        
        if appointment_date < date.today():
            return {'error': 'Cannot book appointments in the past'}, 400
        
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='Booked'
        ).first()
        
        if existing:
            return {'error': 'This time slot is already booked'}, 400
        
        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='Booked',
            reason=reason
        )
        db.session.add(appointment)
        db.session.commit()
        
        cache_key = f'doctor_{doctor_id}_appointments_{appointment_date}'
        cache.delete(cache_key)
        cache_key_avail = f'doctor_{doctor_id}_availability_{appointment_date}'
        cache.delete(cache_key_avail)
        cache.delete('patient_dashboard')
        
        return {
            'success': True,
            'appointment': serialize_appointment(appointment)
        }, 201

class PatientAppointment(Resource):
    @patient_required_api
    def get(self, appointment_id):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.patient_id != patient.id:
            return {'error': 'Access denied'}, 403
        
        treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
        result = serialize_appointment(appointment)
        if treatment:
            result['treatment'] = {
                'id': treatment.id,
                'diagnosis': treatment.diagnosis,
                'prescription': treatment.prescription,
                'notes': treatment.notes,
                'created_at': treatment.created_at.isoformat() if treatment.created_at else None
            }
        
        return result
    
    @patient_required_api
    def put(self, appointment_id):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.patient_id != patient.id:
            return {'error': 'Access denied'}, 403
        
        if appointment.status != 'Booked':
            return {'error': 'Only booked appointments can be rescheduled'}, 400
        
        data = request.get_json()
        new_date = datetime.strptime(data.get('appointment_date'), '%Y-%m-%d').date()
        new_time = datetime.strptime(data.get('appointment_time'), '%H:%M').time()
        
        existing = Appointment.query.filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == new_date,
            Appointment.appointment_time == new_time,
            Appointment.status == 'Booked',
            Appointment.id != appointment_id
        ).first()
        
        if existing:
            return {'error': 'This time slot is already booked'}, 400
        
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.reason = data.get('reason', appointment.reason)
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        cache_key = f'doctor_{appointment.doctor_id}_appointments_{new_date}'
        cache.delete(cache_key)
        cache.delete('patient_dashboard')
        
        return {
            'success': True,
            'appointment': serialize_appointment(appointment)
        }

class PatientAppointmentCancel(Resource):
    @patient_required_api
    def post(self, appointment_id):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.patient_id != patient.id:
            return {'error': 'Access denied'}, 403
        
        if appointment.status != 'Booked':
            return {'error': 'Only booked appointments can be cancelled'}, 400
        
        appointment.status = 'Cancelled'
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        cache_key = f'doctor_{appointment.doctor_id}_appointments_{appointment.appointment_date}'
        cache.delete(cache_key)
        cache.delete('patient_dashboard')
        
        return {'success': True}

class PatientHistory(Resource):
    @patient_required_api
    def get(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        
        appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        return {
            'appointments': [serialize_appointment(a) for a in appointments]
        }

class PatientHistoryExport(Resource):
    @patient_required_api
    def post(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        
        try:
            from celery_app import celery
            current_app.logger.info(f"Starting export task for patient {patient.id}")
            task = celery.send_task('app.tasks.export_patient_history_csv', args=[patient.id])
            current_app.logger.info(f"Export task sent with ID: {task.id}")
            
            return {
                'status': 'success',
                'message': 'Export started',
                'task_id': task.id
            }
        except Exception as e:
            current_app.logger.error(f"Failed to start export task: {str(e)}")
            current_app.logger.exception(e)
            return {
                'status': 'error',
                'message': str(e)
            }, 500

class PatientExports(Resource):
    @patient_required_api
    def get(self):
        patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
        
        exports_dir = os.path.join(current_app.instance_path, 'exports')
        
        if not os.path.exists(exports_dir):
            return {'exports': []}
        
        exports = []
        prefix = f'patient_{patient.id}_'
        current_app.logger.info(f"Filtering exports for patient {patient.id} with prefix: {prefix}")
        
        for filename in os.listdir(exports_dir):
            if filename.startswith(prefix) and filename.endswith('.csv'):
                file_path = os.path.join(exports_dir, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    exports.append({
                        'filename': filename,
                        'created_at': file_stat.st_mtime,
                        'size': file_stat.st_size
                    })
        
        exports.sort(key=lambda x: x['created_at'], reverse=True)
        current_app.logger.info(f"Found {len(exports)} exports for patient {patient.id}")
        
        return {'exports': exports}

class PatientExportDownload(Resource):
    def get(self, filename):
        token = request.args.get('token')
        current_app.logger.info(f"Download request for filename: {filename}, token present: {bool(token)}")
        
        if token:
            exports_dir = os.path.join(current_app.instance_path, 'exports')
            file_path = os.path.join(exports_dir, filename)
            
            if not os.path.exists(file_path):
                return {'error': 'File not found'}, 404
            
            if not filename.startswith('patient_') or not filename.endswith('.csv'):
                return {'error': 'Invalid file'}, 400
            
            try:
                patient_id = int(filename.split('_')[1])
                patient = Patient.query.get_or_404(patient_id)
                
                secret_key = current_app.config.get('SECRET_KEY')
                expected_token = hashlib.sha256(f"{secret_key}{filename}{patient.id}".encode()).hexdigest()
                
                current_app.logger.info(f"Token validation - provided: {token[:10]}..., expected: {expected_token[:10]}...")
                
                if not hmac.compare_digest(token, expected_token):
                    current_app.logger.warning(f"Invalid token for filename: {filename}")
                    return {'error': 'Invalid token'}, 403
                
                current_app.logger.info(f"Token validated, sending file: {file_path}")
                return send_file(file_path, as_attachment=True, download_name=filename)
            except (ValueError, IndexError) as e:
                current_app.logger.error(f"Error parsing filename {filename}: {str(e)}")
                return {'error': 'Invalid filename format'}, 400
            except Exception as e:
                current_app.logger.error(f"Error downloading file {filename}: {str(e)}")
                return {'error': 'Download failed'}, 500
        
        try:
            if current_user.is_authenticated and current_user.role == 'Patient':
                patient = Patient.query.filter_by(user_id=current_user.id).first_or_404()
                
                if not filename.startswith(f'patient_{patient.id}_'):
                    return {'error': 'Access denied'}, 403
                
                exports_dir = os.path.join(current_app.instance_path, 'exports')
                file_path = os.path.join(exports_dir, filename)
                
                if not os.path.exists(file_path):
                    return {'error': 'File not found'}, 404
                
                return send_file(file_path, as_attachment=True, download_name=filename)
        except:
            pass
        
        return {'error': 'Token required. Please use the link from your email or log in first.'}, 401

api.add_resource(PatientDashboard, '/patient/dashboard')
api.add_resource(PatientProfile, '/patient/profile')
api.add_resource(PatientDoctors, '/patient/doctors')
api.add_resource(PatientDoctorAvailability, '/patient/doctors/<int:doctor_id>/availability')
api.add_resource(PatientAppointments, '/patient/appointments')
api.add_resource(PatientAppointment, '/patient/appointments/<int:appointment_id>')
api.add_resource(PatientAppointmentCancel, '/patient/appointments/<int:appointment_id>/cancel')
api.add_resource(PatientHistory, '/patient/history')
api.add_resource(PatientHistoryExport, '/patient/history/export')
api.add_resource(PatientExports, '/patient/exports')
api.add_resource(PatientExportDownload, '/patient/exports/<path:filename>')
