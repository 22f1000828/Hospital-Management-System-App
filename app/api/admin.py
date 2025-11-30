from flask import request
from flask_restful import Resource
from flask_login import current_user
from sqlalchemy.orm import joinedload
from datetime import date
from app import db, cache
from app.models import User, Doctor, Patient, Appointment, Department
from app.api import api
from app.api.utils import admin_required_api, serialize_doctor, serialize_patient, serialize_appointment

class AdminDashboard(Resource):
    @admin_required_api
    def get(self):
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
        
        recent_apts = []
        for apt in recent_appointments:
            apt_data = {
                'id': apt.id,
                'doctor_id': apt.doctor_id,
                'patient_id': apt.patient_id,
                'appointment_date': apt.appointment_date.isoformat() if apt.appointment_date else None,
                'appointment_time': apt.appointment_time.strftime('%H:%M') if apt.appointment_time else None,
                'status': apt.status,
                'reason': apt.reason
            }
            if hasattr(apt, 'doctor') and apt.doctor:
                apt_data['doctor'] = {
                    'id': apt.doctor.id,
                    'first_name': apt.doctor.first_name,
                    'last_name': apt.doctor.last_name,
                    'full_name': apt.doctor.full_name,
                    'specialization': apt.doctor.department.name if apt.doctor.department else None
                }
            if hasattr(apt, 'patient') and apt.patient:
                apt_data['patient'] = {
                    'id': apt.patient.id,
                    'first_name': apt.patient.first_name,
                    'last_name': apt.patient.last_name,
                    'full_name': apt.patient.full_name
                }
            recent_apts.append(apt_data)
        
        return {
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_appointments': total_appointments,
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'recent_appointments': recent_apts
        }

class AdminDoctors(Resource):
    @admin_required_api
    def get(self):
        search = request.args.get('search', '')
        specialization_id = request.args.get('specialization_id', type=int)
        
        doctors_query = Doctor.query.join(User).filter(Doctor.is_active.is_(True))
        
        if search:
            doctors_query = doctors_query.filter(
                (Doctor.first_name.contains(search)) |
                (Doctor.last_name.contains(search)) |
                (User.username.contains(search))
            )
        
        if specialization_id:
            doctors_query = doctors_query.filter(Doctor.specialization_id == specialization_id)
        
        doctors_list = doctors_query.options(
            joinedload(Doctor.user),
            joinedload(Doctor.department)
        ).all()
        
        return {
            'doctors': [serialize_doctor(d) for d in doctors_list]
        }
    
    @admin_required_api
    def post(self):
        request_data = request.get_json()
        
        if User.query.filter_by(username=request_data.get('username')).first():
            return {'error': 'Username already exists'}, 400
        
        if User.query.filter_by(email=request_data.get('email')).first():
            return {'error': 'Email already exists'}, 400
        
        user = User(
            username=request_data.get('username'),
            email=request_data.get('email'),
            role='Doctor',
            is_active=True
        )
        password = request_data.get('password', 'doctor123')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        doctor = Doctor(
            user_id=user.id,
            first_name=request_data.get('first_name'),
            last_name=request_data.get('last_name'),
            specialization_id=request_data.get('specialization_id'),
            phone=request_data.get('phone'),
            license_number=request_data.get('license_number'),
            is_active=True
        )
        db.session.add(doctor)
        db.session.commit()
        
        return {
            'success': True,
            'doctor': serialize_doctor(doctor),
            'password': password
        }, 201

class AdminDoctor(Resource):
    @admin_required_api
    def put(self, doctor_id):
        doctor = Doctor.query.get_or_404(doctor_id)
        data = request.get_json()
        
        if data.get('username') and data['username'] != doctor.user.username:
            if User.query.filter_by(username=data['username']).first():
                return {'error': 'Username already exists'}, 400
        
        if data.get('email') and data['email'] != doctor.user.email:
            if User.query.filter_by(email=data['email']).first():
                return {'error': 'Email already exists'}, 400
        
        if data.get('username'):
            doctor.user.username = data['username']
        if data.get('email'):
            doctor.user.email = data['email']
        if data.get('password'):
            doctor.user.set_password(data['password'])
        if data.get('first_name'):
            doctor.first_name = data['first_name']
        if data.get('last_name'):
            doctor.last_name = data['last_name']
        if data.get('specialization_id'):
            doctor.specialization_id = data['specialization_id']
        if data.get('phone'):
            doctor.phone = data['phone']
        if data.get('license_number'):
            doctor.license_number = data['license_number']
        
        db.session.commit()
        
        return {
            'success': True,
            'doctor': serialize_doctor(doctor)
        }

class AdminDoctorDeactivate(Resource):
    @admin_required_api
    def post(self, doctor_id):
        doctor = Doctor.query.get_or_404(doctor_id)
        doctor.is_active = False
        doctor.user.is_active = False
        db.session.commit()
        
        return {'success': True}

class AdminPatients(Resource):
    @admin_required_api
    def get(self):
        search = request.args.get('search', '')
        
        cache_key = f'admin_patient_search_{search}'
        patients_list = cache.get(cache_key)
        
        if patients_list is None:
            if search:
                patients_list = Patient.query.join(User).filter(
                    (Patient.first_name.contains(search)) |
                    (Patient.last_name.contains(search)) |
                    (User.username.contains(search)) |
                    (Patient.phone.contains(search))
                ).filter_by(is_active=True).options(joinedload(Patient.user)).all()
            else:
                patients_list = Patient.query.filter_by(is_active=True).options(joinedload(Patient.user)).all()
            
            cache.set(cache_key, patients_list, timeout=300)
        
        return {
            'patients': [serialize_patient(p) for p in patients_list]
        }

class AdminPatientDeactivate(Resource):
    @admin_required_api
    def post(self, patient_id):
        patient = Patient.query.get_or_404(patient_id)
        patient.is_active = False
        patient.user.is_active = False
        db.session.commit()
        
        return {'success': True}

class AdminAppointments(Resource):
    @admin_required_api
    def get(self):
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        appointments_list = Appointment.query.options(
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.department),
            joinedload(Appointment.patient).joinedload(Patient.user)
        )
        
        if search:
            appointments_list = appointments_list.join(Patient).join(Doctor).filter(
                (Patient.first_name.contains(search)) |
                (Patient.last_name.contains(search)) |
                (Doctor.first_name.contains(search)) |
                (Doctor.last_name.contains(search))
            )
        
        if status:
            appointments_list = appointments_list.filter_by(status=status)
        
        appointments_list = appointments_list.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        return {
            'appointments': [serialize_appointment(a) for a in appointments_list]
        }

class AdminPatientHistory(Resource):
    @admin_required_api
    def get(self, patient_id):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            return {'error': 'Admin privileges required'}, 403
        
        patient = Patient.query.get_or_404(patient_id)
        appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        return {
            'patient': serialize_patient(patient),
            'appointments': [serialize_appointment(a) for a in appointments]
        }

api.add_resource(AdminDashboard, '/admin/dashboard')
api.add_resource(AdminDoctors, '/admin/doctors')
api.add_resource(AdminDoctor, '/admin/doctors/<int:doctor_id>')
api.add_resource(AdminDoctorDeactivate, '/admin/doctors/<int:doctor_id>/deactivate')
api.add_resource(AdminPatients, '/admin/patients')
api.add_resource(AdminPatientDeactivate, '/admin/patients/<int:patient_id>/deactivate')
api.add_resource(AdminAppointments, '/admin/appointments')
api.add_resource(AdminPatientHistory, '/admin/patients/<int:patient_id>/history')
