from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from app.models import User, Doctor, Department

class DoctorForm(FlaskForm):
    """Form to add/edit doctor"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    specialization_id = SelectField('Specialization', coerce=int, validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    license_number = StringField('License Number', validators=[DataRequired()])
    submit = SubmitField('Save Doctor')
    
    def __init__(self, *args, **kwargs):
        super(DoctorForm, self).__init__(*args, **kwargs)
        self.specialization_id.choices = []
    
    def validate_username(self, username):
        doctor_id = getattr(self, 'doctor_id', None)
        user = User.query.filter_by(username=username.data).first()
        if user:
            if not doctor_id:
                if user:
                    raise ValidationError('Username already exists.')
            else:
                if user.doctor_profile is None or user.doctor_profile.id != doctor_id:
                    raise ValidationError('Username already exists.')
    
    def validate_email(self, email):
        doctor_id = getattr(self, 'doctor_id', None)
        user = User.query.filter_by(email=email.data).first()
        if user:
            if not doctor_id:
                if user:
                    raise ValidationError('Email already exists.')
            else:
                if user.doctor_profile is None or user.doctor_profile.id != doctor_id:
                    raise ValidationError('Email already exists.')

class PatientSearchForm(FlaskForm):
    """Form to search patients"""
    search_query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')

class DoctorSearchForm(FlaskForm):
    """Form to search doctors"""
    search_query = StringField('Search', validators=[Optional()])
    specialization_id = SelectField(
        'Specialization',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )
    submit = SubmitField('Search')
    
    def __init__(self, *args, **kwargs):
        super(DoctorSearchForm, self).__init__(*args, **kwargs)
        self.specialization_id.choices = [('', 'All')]

class AppointmentSearchForm(FlaskForm):
    """Form to search appointments"""
    search_query = StringField('Search by Patient/Doctor', validators=[Optional()])
    status = SelectField('Status', choices=[('', 'All'), ('Booked', 'Booked'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], validators=[Optional()])
    submit = SubmitField('Search')

