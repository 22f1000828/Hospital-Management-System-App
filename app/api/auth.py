from flask import request
from flask_login import login_user, logout_user, login_required, current_user
from flask_restful import Resource
from app import db
from app.models import User, Patient
from app.api import api

def get_dashboard_route(role):
    routes = {
        'Admin': '/admin/dashboard',
        'Doctor': '/doctor/dashboard',
        'Patient': '/patient/dashboard'
    }
    return routes.get(role, '/')

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        remember = data.get('remember', False)
        
        if not username or not password or not role:
            return {'error': 'Username, password, and role are required'}, 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return {'error': 'Account has been deactivated'}, 403
            
            if user.role != role:
                return {'error': f'Invalid login. Please use {user.role.lower()} login'}, 403
            
            login_user(user, remember=remember)
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                },
                'redirect': get_dashboard_route(user.role)
            }
        
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    @login_required
    def post(self):
        logout_user()
        return {'success': True}

class Register(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        date_of_birth = data.get('date_of_birth')
        address = data.get('address')
        emergency_contact_name = data.get('emergency_contact_name')
        emergency_contact_phone = data.get('emergency_contact_phone')
        
        if not all([username, password, email, first_name, last_name, phone]):
            return {'error': 'Missing required fields'}, 400
        
        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists'}, 400
        
        if User.query.filter_by(email=email).first():
            return {'error': 'Email already exists'}, 400
        
        user = User(username=username, email=email, role='Patient', is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            date_of_birth=date_of_birth,
            address=address,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            is_active=True
        )
        db.session.add(patient)
        db.session.commit()
        
        login_user(user)
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'redirect': '/patient/dashboard'
        }

class CurrentUser(Resource):
    @login_required
    def get(self):
        return {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'is_active': current_user.is_active
        }

api.add_resource(Login, '/auth/login')
api.add_resource(Logout, '/auth/logout')
api.add_resource(Register, '/auth/register')
api.add_resource(CurrentUser, '/auth/me')
