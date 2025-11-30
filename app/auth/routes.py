from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Patient
from app.auth.forms import LoginForm, PatientRegistrationForm
from app.auth import bp

def handle_login(form, expected_role, dashboard_route):
    """Helper function to handle login for a specific role"""
    if current_user.is_authenticated:
        if current_user.role == expected_role:
            return redirect(url_for(dashboard_route))
        else:
            flash(f'Please use the {current_user.role.lower()} login page.', 'warning')
            return redirect(url_for(f'auth.{current_user.role.lower()}_login'))
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'danger')
                return redirect(url_for(f'auth.{expected_role.lower()}_login'))
            
            if user.role != expected_role:
                flash(f'Invalid login page. Please use the {user.role.lower()} login page.', 'danger')
                return redirect(url_for(f'auth.{user.role.lower()}_login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for(dashboard_route))
        else:
            flash('Invalid username or password', 'danger')
    
    return None

@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    form = LoginForm()
    result = handle_login(form, 'Admin', 'admin.dashboard')
    if result:
        return result
    return render_template('auth/admin_login.html', form=form)

@bp.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    """Doctor login page"""
    form = LoginForm()
    result = handle_login(form, 'Doctor', 'doctor.dashboard')
    if result:
        return result
    return render_template('auth/doctor_login.html', form=form)

@bp.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    """Patient login page"""
    form = LoginForm()
    result = handle_login(form, 'Patient', 'patient.dashboard')
    if result:
        return result
    return render_template('auth/patient_login.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """General login page - redirects to role selection"""
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == 'Admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'Doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'Patient':
            return redirect(url_for('patient.dashboard'))
    
    return render_template('auth/login_selector.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Patient registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
    
    form = PatientRegistrationForm()
    if form.validate_on_submit():
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='Patient',
            is_active=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        
        # Create patient profile
        patient = Patient(
            user_id=user.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            phone=form.phone.data,
            address=form.address.data,
            emergency_contact=form.emergency_contact.data,
            emergency_phone=form.emergency_phone.data,
            is_active=True
        )
        db.session.add(patient)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.patient_login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

