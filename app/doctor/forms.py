from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional
from datetime import date

class AvailabilityForm(FlaskForm):
    """Form to update doctor availability"""
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    submit = SubmitField('Add Availability')

class TreatmentForm(FlaskForm):
    """Form to enter treatment details"""
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    prescription = TextAreaField('Prescription', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit_treatment = SubmitField('Save Treatment')

class AppointmentStatusForm(FlaskForm):
    """Form to update appointment status"""
    status = SelectField(
        'Status',
        choices=[('Booked', 'Booked'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')],
        validators=[DataRequired()]
    )
    submit_status = SubmitField('Update Status')

