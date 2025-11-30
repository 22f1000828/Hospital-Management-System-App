from functools import wraps
from flask_login import login_required, current_user

def admin_required_api(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            return {'error': 'Admin privileges required'}, 403
        return f(*args, **kwargs)
    return decorated_function

def doctor_required_api(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Doctor':
            return {'error': 'Doctor privileges required'}, 403
        return f(*args, **kwargs)
    return decorated_function

def patient_required_api(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Patient':
            return {'error': 'Patient privileges required'}, 403
        return f(*args, **kwargs)
    return decorated_function

def serialize_appointment(appointment):
    result = {
        'id': appointment.id,
        'doctor_id': appointment.doctor_id,
        'patient_id': appointment.patient_id,
        'appointment_date': appointment.appointment_date.isoformat() if appointment.appointment_date else None,
        'appointment_time': appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else None,
        'status': appointment.status,
        'reason': appointment.reason
    }
    
    if hasattr(appointment, 'doctor') and appointment.doctor:
        result['doctor'] = {
            'id': appointment.doctor.id,
            'first_name': appointment.doctor.first_name,
            'last_name': appointment.doctor.last_name,
            'full_name': appointment.doctor.full_name,
            'specialization': appointment.doctor.department.name if appointment.doctor.department else None
        }
    
    if hasattr(appointment, 'patient') and appointment.patient:
        result['patient'] = {
            'id': appointment.patient.id,
            'first_name': appointment.patient.first_name,
            'last_name': appointment.patient.last_name,
            'full_name': appointment.patient.full_name
        }
    
    if hasattr(appointment, 'treatment') and appointment.treatment:
        result['treatment'] = serialize_treatment(appointment.treatment)
    
    return result

def serialize_doctor(doctor):
    return {
        'id': doctor.id,
        'first_name': doctor.first_name,
        'last_name': doctor.last_name,
        'full_name': doctor.full_name,
        'specialization_id': doctor.specialization_id,
        'specialization': doctor.department.name if doctor.department else None,
        'phone': doctor.phone,
        'email': doctor.user.email if doctor.user else None,
        'username': doctor.user.username if doctor.user else None,
        'is_active': doctor.is_active
    }

def serialize_patient(patient):
    return {
        'id': patient.id,
        'first_name': patient.first_name,
        'last_name': patient.last_name,
        'full_name': patient.full_name,
        'phone': patient.phone,
        'email': patient.user.email if patient.user else None,
        'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        'address': patient.address,
        'is_active': patient.is_active
    }

def serialize_treatment(treatment):
    return {
        'id': treatment.id,
        'diagnosis': treatment.diagnosis,
        'prescription': treatment.prescription,
        'notes': treatment.notes,
        'created_at': treatment.created_at.isoformat() if treatment.created_at else None
    }
