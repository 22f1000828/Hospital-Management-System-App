from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Email

class PatientProfileForm(FlaskForm):
    """Form to update patient profile"""
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    emergency_contact = StringField('Emergency Contact Name', validators=[DataRequired()])
    emergency_phone = StringField('Emergency Contact Phone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

class AppointmentBookingForm(FlaskForm):
    """Form to book appointment"""
    doctor_id = StringField('Doctor ID', validators=[DataRequired()])  # Hidden field, not a select
    appointment_date = DateField('Date', validators=[DataRequired()])
    appointment_time = SelectField('Time', coerce=str, validators=[DataRequired()], choices=[])
    reason = TextAreaField('Reason for Visit', validators=[Optional()])
    submit = SubmitField('Book Appointment')

class DoctorSearchForm(FlaskForm):
    """Form to search doctors"""
    search_query = StringField('Search by Name', validators=[Optional()])
    specialization_id = SelectField(
        'Specialization',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )
    submit = SubmitField('Search')
    
    def __init__(self, *args, **kwargs):
        super(DoctorSearchForm, self).__init__(*args, **kwargs)
        self.specialization_id.choices = [('', 'All')]

