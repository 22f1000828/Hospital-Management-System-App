from datetime import date, timedelta
from flask import current_app, render_template
from flask_mail import Message
from sqlalchemy.orm import joinedload
from app import db, mail
from app.models import Appointment, Doctor, Patient, Treatment, User
from app.utils import get_ist_now
import os
import pandas as pd

# Tasks will be registered after celery is created
def register_tasks(celery_app):
    @celery_app.task(bind=True, name='app.tasks.send_daily_reminders')
    def send_daily_reminders(self):
        try:
            today = date.today()
            current_app.logger.info(f"Starting daily reminders job for {today.isoformat()}")
            
            patients = Patient.query.filter_by(is_active=True).all()
            current_app.logger.info(f"Found {len(patients)} active patients")
            
            sent_count = 0
            failed_count = 0
            no_email_count = 0
            no_appointments_count = 0
            
            current_app.logger.info(f"Mail server: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}")
            
            for patient in patients:
                try:
                    user = patient.user
                    
                    if not user or not user.email:
                        current_app.logger.warning(f"Patient {patient.full_name} (ID: {patient.id}) has no email address")
                        no_email_count += 1
                        continue
                    
                    upcoming_appointments = Appointment.query.filter_by(
                        patient_id=patient.id,
                        status='Booked'
                    ).filter(
                        Appointment.appointment_date >= today
                    ).options(
                        joinedload(Appointment.doctor).joinedload(Doctor.department),
                        joinedload(Appointment.doctor).joinedload(Doctor.user)
                    ).order_by(
                        Appointment.appointment_date,
                        Appointment.appointment_time
                    ).all()
                    
                    if not upcoming_appointments:
                        no_appointments_count += 1
                        continue
                    
                    appointments_list = []
                    for appointment in upcoming_appointments:
                        try:
                            doctor = appointment.doctor
                            if not doctor:
                                current_app.logger.warning(f"Appointment {appointment.id} has no doctor assigned")
                                continue
                            
                            appointment_time = appointment.appointment_time.strftime('%I:%M %p')
                            days_until = (appointment.appointment_date - today).days
                            
                            if days_until == 0:
                                day_info = "TODAY"
                            elif days_until == 1:
                                day_info = "TOMORROW"
                            else:
                                day_info = f"in {days_until} days"
                            
                            dept_name = doctor.department.name if doctor.department else 'N/A'
                            doctor_name = doctor.full_name if doctor.full_name else 'N/A'
                            
                            appointments_list.append(f"""
  • Date: {appointment.appointment_date.strftime('%B %d, %Y')} ({day_info})
    Time: {appointment_time}
    Doctor: Dr. {doctor_name}
    Specialization: {dept_name}
    Reason: {appointment.reason or 'General consultation'}""")
                        except Exception as apt_error:
                            current_app.logger.error(f"Error processing appointment {appointment.id}: {str(apt_error)}")
                            current_app.logger.exception(apt_error)
                            continue
                    
                    if not appointments_list:
                        current_app.logger.warning(f"No valid appointments found for patient {patient.id} after processing")
                        no_appointments_count += 1
                        continue
                    
                    reminder_message = f"""
Dear {patient.full_name},

This is your daily reminder of upcoming appointments:

You have {len(appointments_list)} upcoming appointment(s):

{''.join(appointments_list)}

Please arrive 10 minutes before your scheduled time.

If you need to reschedule or cancel any appointment, please log in to your account.

Thank you,
Hospital Management System
"""
                    
                    try:
                        mail_server = current_app.config.get('MAIL_SERVER')
                        mail_port = current_app.config.get('MAIL_PORT')
                        current_app.logger.info(f"Mail config: {mail_server}:{mail_port}")
                        
                        msg = Message(
                            subject=f'Daily Appointment Reminder - {len(appointments_list)} Upcoming Appointment(s)',
                            recipients=[user.email],
                            body=reminder_message,
                            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
                        )
                        current_app.logger.info(f"Attempting to send daily reminder to {user.email} for {len(appointments_list)} appointments")
                        
                        mail.send(msg)
                        sent_count += 1
                        current_app.logger.info(f"✓ Daily reminder sent successfully to {user.email} ({len(appointments_list)} appointments)")
                    except Exception as email_error:
                        current_app.logger.error(f"✗ Failed to send reminder to {user.email}: {str(email_error)}")
                        current_app.logger.error(f"Mail server: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}")
                        current_app.logger.exception(email_error)
                        failed_count += 1
                    
                except Exception as e:
                    current_app.logger.error(f"Failed to process patient {patient.id}: {str(e)}")
                    current_app.logger.exception(e)
                    failed_count += 1
            
            result = {
                'status': 'completed',
                'total_patients': len(patients),
                'sent_count': sent_count,
                'failed_count': failed_count,
                'no_email_count': no_email_count,
                'no_appointments_count': no_appointments_count,
                'date': today.isoformat()
            }
            
            current_app.logger.info(f"Daily reminders job completed: {result}")
            return result
        
        except Exception as e:
            current_app.logger.error(f"Daily reminder job failed: {str(e)}")
            current_app.logger.exception(e)
            raise
    
    @celery_app.task(bind=True, name='app.tasks.generate_monthly_report')
    def generate_monthly_report(self, doctor_id, year=None, month=None):
        try:
            doctor = Doctor.query.get_or_404(doctor_id)
            
            if not year or not month:
                last_month = date.today().replace(day=1) - timedelta(days=1)
                year = last_month.year
                month = last_month.month
            
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date
            ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
            
            total_appointments = len(appointments)
            completed_appointments = [a for a in appointments if a.status == 'Completed']
            cancelled_appointments = [a for a in appointments if a.status == 'Cancelled']
            booked_appointments = [a for a in appointments if a.status == 'Booked']
            
            treatments = []
            diagnoses_summary = {}
            
            for appointment in completed_appointments:
                if appointment.treatment:
                    treatment = appointment.treatment
                    treatments.append({
                        'appointment_date': appointment.appointment_date,
                        'patient': appointment.patient.full_name,
                        'diagnosis': treatment.diagnosis or 'N/A',
                        'prescription': treatment.prescription or 'N/A',
                        'notes': treatment.notes or 'N/A'
                    })
                    
                    if treatment.diagnosis:
                        diagnosis_key = treatment.diagnosis[:50]  # First 50 chars
                        diagnoses_summary[diagnosis_key] = diagnoses_summary.get(diagnosis_key, 0) + 1
            
            report_data = {
                'doctor': doctor,
                'month': start_date.strftime('%B %Y'),
                'start_date': start_date,
                'end_date': end_date,
                'total_appointments': total_appointments,
                'completed_count': len(completed_appointments),
                'cancelled_count': len(cancelled_appointments),
                'booked_count': len(booked_appointments),
                'appointments': appointments,
                'treatments': treatments,
                'diagnoses_summary': diagnoses_summary
            }
            
            html_content = render_template('reports/monthly_report.html', **report_data)
            
            reports_dir = os.path.join(current_app.instance_path, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            html_filename = f"doctor_{doctor_id}_report_{year}_{month:02d}.html"
            html_path = os.path.join(reports_dir, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            try:
                from weasyprint import HTML
                pdf_filename = f"doctor_{doctor_id}_report_{year}_{month:02d}.pdf"
                pdf_path = os.path.join(reports_dir, pdf_filename)
                HTML(string=html_content).write_pdf(pdf_path)
            except Exception as e:
                current_app.logger.warning(f"PDF generation failed: {str(e)}")
                pdf_path = None
            
            doctor_user = doctor.user
            if doctor_user and doctor_user.email:
                try:
                    msg = Message(
                        subject=f'Monthly Report - {start_date.strftime("%B %Y")}',
                        recipients=[doctor_user.email],
                        html=html_content
                    )
                    
                    if pdf_path and os.path.exists(pdf_path):
                        with current_app.open_resource(pdf_path) as pdf_file:
                            msg.attach(
                                pdf_filename,
                                'application/pdf',
                                pdf_file.read()
                            )
                    
                    mail.send(msg)
                    current_app.logger.info(f"Monthly report email sent to {doctor_user.email}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send monthly report email: {str(email_error)}")
                    current_app.logger.warning(f"Report generated but email failed. Files: {html_path}, {pdf_path if pdf_path else 'N/A'}")
            
            return {
                'status': 'completed',
                'doctor_id': doctor_id,
                'month': f"{year}-{month:02d}",
                'total_appointments': total_appointments,
                'html_path': html_path,
                'pdf_path': pdf_path if pdf_path and os.path.exists(pdf_path) else None
            }
        
        except Exception as e:
            current_app.logger.error(f"Monthly report generation failed: {str(e)}")
            raise
    
    @celery_app.task(bind=True, name='app.tasks.generate_monthly_report_for_patient')
    def generate_monthly_report_for_patient(self, patient_id, year=None, month=None):
        try:
            patient = Patient.query.get_or_404(patient_id)
            user = patient.user
            
            if not year or not month:
                last_month = date.today().replace(day=1) - timedelta(days=1)
                year = last_month.year
                month = last_month.month
            
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            appointments = Appointment.query.filter(
                Appointment.patient_id == patient_id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date
            ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
            
            total_appointments = len(appointments)
            completed_appointments = [a for a in appointments if a.status == 'Completed']
            cancelled_appointments = [a for a in appointments if a.status == 'Cancelled']
            booked_appointments = [a for a in appointments if a.status == 'Booked']
            
            treatments = []
            for appointment in completed_appointments:
                if appointment.treatment:
                    treatment = appointment.treatment
                    treatments.append({
                        'date': appointment.appointment_date,
                        'doctor': appointment.doctor.full_name,
                        'specialization': appointment.doctor.department.name if appointment.doctor.department else 'N/A',
                        'diagnosis': treatment.diagnosis or 'N/A',
                        'prescription': treatment.prescription or 'N/A',
                        'notes': treatment.notes or 'N/A'
                    })
            
            report_message = f"""
Dear {patient.full_name},

Your Monthly Visit Summary for {start_date.strftime('%B %Y')}:

Total Appointments: {total_appointments}
  • Completed: {len(completed_appointments)}
  • Cancelled: {len(cancelled_appointments)}
  • Booked: {len(booked_appointments)}

"""
            
            if treatments:
                report_message += "Treatment Summary:\n"
                for treatment in treatments:
                    report_message += f"""
  • Date: {treatment['date'].strftime('%B %d, %Y')}
    Doctor: Dr. {treatment['doctor']} ({treatment['specialization']})
    Diagnosis: {treatment['diagnosis']}
    Prescription: {treatment['prescription']}
"""
            else:
                report_message += "No completed treatments this month.\n"
            
            report_message += """
Thank you for choosing our hospital.

Hospital Management System
"""
            
            if user and user.email:
                try:
                    msg = Message(
                        subject=f'Monthly Visit Summary - {start_date.strftime("%B %Y")}',
                        recipients=[user.email],
                        body=report_message
                    )
                    mail.send(msg)
                    current_app.logger.info(f"Monthly report email sent to patient {user.email}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send monthly report email: {str(email_error)}")
            
            return {
                'status': 'completed',
                'patient_id': patient_id,
                'month': f"{year}-{month:02d}",
                'total_appointments': total_appointments
            }
        
        except Exception as e:
            current_app.logger.error(f"Patient monthly report generation failed: {str(e)}")
            raise
    
    @celery_app.task(bind=True, name='app.tasks.generate_monthly_report_for_admin')
    def generate_monthly_report_for_admin(self, admin_user_id, year=None, month=None):
        try:
            admin_user = User.query.get_or_404(admin_user_id)
            if admin_user.role != 'Admin':
                raise ValueError(f"User {admin_user_id} is not an admin")
            
            if not year or not month:
                last_month = date.today().replace(day=1) - timedelta(days=1)
                year = last_month.year
                month = last_month.month
            
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            total_appointments = Appointment.query.filter(
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date
            ).count()
            
            completed_appointments = Appointment.query.filter(
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
                Appointment.status == 'Completed'
            ).count()
            
            cancelled_appointments = Appointment.query.filter(
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
                Appointment.status == 'Cancelled'
            ).count()
            
            booked_appointments = Appointment.query.filter(
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
                Appointment.status == 'Booked'
            ).count()
            
            total_patients = Patient.query.filter_by(is_active=True).count()
            total_doctors = Doctor.query.filter_by(is_active=True).count()
            
            report_message = f"""
Dear {admin_user.username},

Monthly System Report for {start_date.strftime('%B %Y')}:

System Statistics:
  • Total Active Patients: {total_patients}
  • Total Active Doctors: {total_doctors}

Appointment Statistics:
  • Total Appointments: {total_appointments}
  • Completed: {completed_appointments}
  • Cancelled: {cancelled_appointments}
  • Booked: {booked_appointments}

Thank you,
Hospital Management System
"""
            
            if admin_user.email:
                try:
                    msg = Message(
                        subject=f'Monthly System Report - {start_date.strftime("%B %Y")}',
                        recipients=[admin_user.email],
                        body=report_message
                    )
                    mail.send(msg)
                    current_app.logger.info(f"Monthly system report email sent to admin {admin_user.email}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send monthly system report email: {str(email_error)}")
            
            return {
                'status': 'completed',
                'admin_id': admin_user_id,
                'month': f"{year}-{month:02d}",
                'total_appointments': total_appointments
            }
        
        except Exception as e:
            current_app.logger.error(f"Admin monthly report generation failed: {str(e)}")
            raise
    
    @celery_app.task(bind=True, name='app.tasks.generate_monthly_reports_for_all_users')
    def generate_monthly_reports_for_all_users(self):
        try:
            last_month = date.today().replace(day=1) - timedelta(days=1)
            year = last_month.year
            month = last_month.month
            
            results = {
                'patients': [],
                'doctors': [],
                'admins': []
            }
            
            patients = Patient.query.filter_by(is_active=True).all()
            for patient in patients:
                try:
                    result = celery_app.send_task(
                        'app.tasks.generate_monthly_report_for_patient',
                        args=[patient.id, year, month]
                    )
                    results['patients'].append({
                        'patient_id': patient.id,
                        'patient_name': patient.full_name,
                        'task_id': result.id
                    })
                except Exception as e:
                    current_app.logger.error(f"Failed to queue report for patient {patient.id}: {str(e)}")
            
            doctors = Doctor.query.filter_by(is_active=True).all()
            for doctor in doctors:
                try:
                    result = celery_app.send_task(
                        'app.tasks.generate_monthly_report',
                        args=[doctor.id, year, month]
                    )
                    results['doctors'].append({
                        'doctor_id': doctor.id,
                        'doctor_name': doctor.full_name,
                        'task_id': result.id
                    })
                except Exception as e:
                    current_app.logger.error(f"Failed to queue report for doctor {doctor.id}: {str(e)}")
            
            admins = User.query.filter_by(role='Admin', is_active=True).all()
            for admin in admins:
                try:
                    result = celery_app.send_task(
                        'app.tasks.generate_monthly_report_for_admin',
                        args=[admin.id, year, month]
                    )
                    results['admins'].append({
                        'admin_id': admin.id,
                        'admin_name': admin.username,
                        'task_id': result.id
                    })
                except Exception as e:
                    current_app.logger.error(f"Failed to queue report for admin {admin.id}: {str(e)}")
            
            return {
                'status': 'completed',
                'month': f"{year}-{month:02d}",
                'total_patients': len(patients),
                'total_doctors': len(doctors),
                'total_admins': len(admins),
                'queued_patient_reports': len(results['patients']),
                'queued_doctor_reports': len(results['doctors']),
                'queued_admin_reports': len(results['admins']),
                'results': results
            }
        
        except Exception as e:
            current_app.logger.error(f"Monthly reports generation failed: {str(e)}")
            raise
    
    @celery_app.task(bind=True, name='app.tasks.export_patient_history_csv')
    def export_patient_history_csv(self, patient_id):
        try:
            patient = Patient.query.get_or_404(patient_id)
            user = patient.user
            
            appointments = Appointment.query.filter_by(
                patient_id=patient_id
            ).order_by(
                Appointment.appointment_date.desc(),
                Appointment.appointment_time.desc()
            ).all()
            
            # Prepare data for CSV
            csv_data = []
            for appointment in appointments:
                treatment = appointment.treatment
                csv_data.append({
                    'Appointment Date': appointment.appointment_date.strftime('%Y-%m-%d'),
                    'Appointment Time': appointment.appointment_time.strftime('%H:%M'),
                    'Doctor': appointment.doctor.full_name,
                    'Specialization': appointment.doctor.department.name if appointment.doctor.department else 'N/A',
                    'Status': appointment.status,
                    'Reason': appointment.reason or 'N/A',
                    'Diagnosis': treatment.diagnosis if treatment else 'N/A',
                    'Prescription': treatment.prescription if treatment else 'N/A',
                    'Notes': treatment.notes if treatment else 'N/A',
                    'Treatment Date': treatment.created_at.strftime('%Y-%m-%d %H:%M') if treatment else 'N/A'
                })
            
            exports_dir = os.path.join(current_app.instance_path, 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            
            timestamp = get_ist_now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"patient_{patient_id}_history_{timestamp}.csv"
            csv_path = os.path.join(exports_dir, csv_filename)
            
            # Write CSV using pandas
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_path, index=False)
            
            if user.email:
                try:
                    # Generate proper URL using Flask's url_for
                    from flask import url_for
                    with current_app.app_context():
                        # Set SERVER_NAME temporarily if BASE_URL is configured
                        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
                        original_server_name = current_app.config.get('SERVER_NAME')
                        
                        # Extract host from BASE_URL for SERVER_NAME
                        from urllib.parse import urlparse
                        parsed_url = urlparse(base_url)
                        if parsed_url.netloc:
                            current_app.config['SERVER_NAME'] = parsed_url.netloc
                        
                        try:
                            download_url = url_for('patient.download_export', filename=csv_filename, _external=True)
                        finally:
                            # Restore original SERVER_NAME
                            if original_server_name:
                                current_app.config['SERVER_NAME'] = original_server_name
                            elif 'SERVER_NAME' in current_app.config:
                                del current_app.config['SERVER_NAME']
                    
                    email_body = f"""
Dear {patient.full_name},

Your treatment history export has been completed.

You can download your CSV file by clicking the link below:
{download_url}

Note: You will need to be logged in to your account to download the file. If you are not logged in, you will be redirected to the login page first.

The file contains {len(csv_data)} appointment records.

Thank you,
Hospital Management System
"""
                    
                    msg = Message(
                        subject='Treatment History Export Ready',
                        recipients=[user.email],
                        body=email_body
                    )
                    mail.send(msg)
                    current_app.logger.info(f"Export notification email sent to {user.email}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send export notification email: {str(email_error)}")
                    current_app.logger.warning("CSV export completed but email notification failed. File is available at: " + csv_path)
            
            return {
                'status': 'completed',
                'patient_id': patient_id,
                'filename': csv_filename,
                'file_path': csv_path,
                'record_count': len(csv_data)
            }
        
        except Exception as e:
            current_app.logger.error(f"CSV export failed: {str(e)}")
            raise
    
    return {
        'send_daily_reminders': send_daily_reminders,
        'generate_monthly_report': generate_monthly_report,
        'generate_monthly_report_for_patient': generate_monthly_report_for_patient,
        'generate_monthly_report_for_admin': generate_monthly_report_for_admin,
        'generate_monthly_reports_for_all_users': generate_monthly_reports_for_all_users,
        'export_patient_history_csv': export_patient_history_csv
    }
