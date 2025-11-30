from flask import request
from flask_restful import Resource
from flask_login import current_user
from sqlalchemy.orm import joinedload
from datetime import date, datetime, timedelta
from app import db, cache
from app.models import Doctor, Patient, Appointment, Treatment, DoctorAvailability
from app.api import api
from app.api.utils import doctor_required_api, serialize_appointment, serialize_patient, serialize_treatment

class DoctorDashboard(Resource):
    @doctor_required_api
    def get(self):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        
        today = date.today()
        today_appointments = Appointment.query.filter_by(
            doctor_id=doctor.id,
            appointment_date=today,
            status='Booked'
        ).options(
            joinedload(Appointment.patient).joinedload(Patient.user)
        ).order_by(Appointment.appointment_time).all()
        
        week_start = today
        week_end = today + timedelta(days=7)
        week_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date >= week_start,
            Appointment.appointment_date <= week_end,
            Appointment.status == 'Booked'
        ).options(
            joinedload(Appointment.patient).joinedload(Patient.user)
        ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
        
        patient_ids = db.session.query(Appointment.patient_id).filter_by(
            doctor_id=doctor.id
        ).distinct().all()
        patient_ids = [p[0] for p in patient_ids]
        assigned_patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()
        
        return {
            'doctor': {
                'id': doctor.id,
                'first_name': doctor.first_name,
                'last_name': doctor.last_name,
                'full_name': doctor.full_name
            },
            'today_appointments': [serialize_appointment(a) for a in today_appointments],
            'week_appointments': [serialize_appointment(a) for a in week_appointments],
            'assigned_patients': [serialize_patient(p) for p in assigned_patients]
        }

class DoctorAppointments(Resource):
    @doctor_required_api
    def get(self):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        
        status = request.args.get('status', '')
        apts = Appointment.query.filter_by(doctor_id=doctor.id)
        
        if status:
            apts = apts.filter_by(status=status)
        
        apts = apts.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        return {
            'appointments': [serialize_appointment(a) for a in apts]
        }

class DoctorAppointment(Resource):
    @doctor_required_api
    def get(self, appointment_id):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.doctor_id != doctor.id:
            return {'error': 'Access denied'}, 403
        
        treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
        
        result = serialize_appointment(appointment)
        if treatment:
            result['treatment'] = serialize_treatment(treatment)
        
        return result

class DoctorAppointmentStatus(Resource):
    @doctor_required_api
    def put(self, appointment_id):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.doctor_id != doctor.id:
            return {'error': 'Access denied'}, 403
        
        data = request.get_json()
        appointment.status = data.get('status')
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        # TODO: maybe add validation here
        return {
            'success': True,
            'appointment': serialize_appointment(appointment)
        }

class DoctorAppointmentTreatment(Resource):
    @doctor_required_api
    def post(self, appointment_id):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if appointment.doctor_id != doctor.id:
            return {'error': 'Access denied'}, 403
        
        data = request.get_json()
        treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
        
        if treatment:
            treatment.diagnosis = data.get('diagnosis')
            treatment.prescription = data.get('prescription')
            treatment.notes = data.get('notes')
            treatment.updated_at = datetime.utcnow()
        else:
            treatment = Treatment(
                appointment_id=appointment_id,
                diagnosis=data.get('diagnosis'),
                prescription=data.get('prescription'),
                notes=data.get('notes')
            )
            db.session.add(treatment)
        
        if appointment.status == 'Booked':
            appointment.status = 'Completed'
            appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'success': True,
            'treatment': serialize_treatment(treatment)
        }

class DoctorTreatment(Resource):
    @doctor_required_api
    def put(self, treatment_id):
        treatment = Treatment.query.get_or_404(treatment_id)
        appointment = treatment.appointment
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        
        if appointment.doctor_id != doctor.id:
            return {'error': 'Access denied'}, 403
        
        data = request.get_json()
        treatment.diagnosis = data.get('diagnosis', treatment.diagnosis)
        treatment.prescription = data.get('prescription', treatment.prescription)
        treatment.notes = data.get('notes', treatment.notes)
        treatment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'treatment': serialize_treatment(treatment)
        }

class DoctorPatients(Resource):
    @doctor_required_api
    def get(self):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        
        patient_ids = db.session.query(Appointment.patient_id).filter_by(
            doctor_id=doctor.id
        ).distinct().all()
        patient_ids = [p[0] for p in patient_ids]
        patients_list = Patient.query.filter(Patient.id.in_(patient_ids)).all()
        
        return {
            'patients': [serialize_patient(p) for p in patients_list]
        }

class DoctorPatientHistory(Resource):
    @doctor_required_api
    def get(self, patient_id):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        patient = Patient.query.get_or_404(patient_id)
        
        appointments = Appointment.query.filter_by(
            doctor_id=doctor.id,
            patient_id=patient_id
        ).order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        return {
            'patient': serialize_patient(patient),
            'appointments': [serialize_appointment(a) for a in appointments]
        }

class DoctorAvailabilityList(Resource):
    @doctor_required_api
    def get(self):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        
        today = date.today()
        next_7_days = today + timedelta(days=7)
        availabilities = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date >= today,
            DoctorAvailability.date <= next_7_days
        ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
        
        return {
            'availabilities': [{
                'id': a.id,
                'date': a.date.isoformat(),
                'start_time': a.start_time.strftime('%H:%M'),
                'end_time': a.end_time.strftime('%H:%M'),
                'is_available': a.is_available
            } for a in availabilities]
        }
    
    @doctor_required_api
    def post(self):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        data = request.get_json()
        
        today = date.today()
        next_7_days = today + timedelta(days=7)
        avail_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        
        if avail_date < today or avail_date > next_7_days:
            return {'error': 'Availability can only be set for the next 7 days'}, 400
        
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            date=avail_date,
            start_time=datetime.strptime(data.get('start_time'), '%H:%M').time()
        ).first()
        
        if existing:
            return {'error': 'This time slot already exists'}, 400
        
        availability = DoctorAvailability(
            doctor_id=doctor.id,
            date=avail_date,
            start_time=datetime.strptime(data.get('start_time'), '%H:%M').time(),
            end_time=datetime.strptime(data.get('end_time'), '%H:%M').time(),
            is_available=True
        )
        db.session.add(availability)
        db.session.commit()
        
        cache_key = f'doctor_{doctor.id}_availability_{avail_date}'
        cache.delete(cache_key)
        cache_key_summary = f'doctor_availability_{today.isoformat()}'
        cache.delete(cache_key_summary)
        
        return {
            'success': True,
            'availability': {
                'id': availability.id,
                'date': availability.date.isoformat(),
                'start_time': availability.start_time.strftime('%H:%M'),
                'end_time': availability.end_time.strftime('%H:%M')
            }
        }, 201

class DoctorAvailabilityItem(Resource):
    @doctor_required_api
    def delete(self, availability_id):
        doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
        availability = DoctorAvailability.query.get_or_404(availability_id)
        
        if availability.doctor_id != doctor.id:
            return {'error': 'Access denied'}, 403
        
        db.session.delete(availability)
        db.session.commit()
        
        return {'success': True}

api.add_resource(DoctorDashboard, '/doctor/dashboard')
api.add_resource(DoctorAppointments, '/doctor/appointments')
api.add_resource(DoctorAppointment, '/doctor/appointments/<int:appointment_id>')
api.add_resource(DoctorAppointmentStatus, '/doctor/appointments/<int:appointment_id>/status')
api.add_resource(DoctorAppointmentTreatment, '/doctor/appointments/<int:appointment_id>/treatment')
api.add_resource(DoctorTreatment, '/doctor/treatments/<int:treatment_id>')
api.add_resource(DoctorPatients, '/doctor/patients')
api.add_resource(DoctorPatientHistory, '/doctor/patients/<int:patient_id>/history')
api.add_resource(DoctorAvailabilityList, '/doctor/availability')
api.add_resource(DoctorAvailabilityItem, '/doctor/availability/<int:availability_id>')
