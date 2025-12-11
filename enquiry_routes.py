from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_mail import Message, Mail
from datetime import datetime
import re
from models import db, Enquiry, User, ActivityLog, Notification

# Create blueprint
enquiry_bp = Blueprint('enquiry', __name__)

# Enquiry Form
class EnquiryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])
    practice_area = SelectField('Practice Area', choices=[
        ('', 'Select a practice area'),
        ('family_law', 'Family Law'),
        ('criminal_law', 'Criminal Law'),
        ('corporate_law', 'Corporate Law'),
        ('property_law', 'Property Law'),
        ('immigration_law', 'Immigration Law'),
        ('employment_law', 'Employment Law'),
        ('intellectual_property', 'Intellectual Property'),
        ('tax_law', 'Tax Law'),
        ('environmental_law', 'Environmental Law'),
        ('other', 'Other')
    ], validators=[Optional()])
    urgency_level = SelectField('Urgency Level', choices=[
        ('low', 'Low - General consultation'),
        ('medium', 'Medium - Planning needed'),
        ('high', 'High - Time-sensitive matter'),
        ('urgent', 'Urgent - Immediate assistance required')
    ], default='medium', validators=[Optional()])
    preferred_contact = SelectField('Preferred Contact Method', choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Both')
    ], default='both', validators=[Optional()])

def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return True
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    # Check if it's a valid phone number (10-15 digits)
    return len(phone_digits) >= 10 and len(phone_digits) <= 15

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    # Basic HTML tag removal
    text = re.sub(r'<[^>]+>', '', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def send_enquiry_email(enquiry):
    """Send email notifications for new enquiry"""
    try:
        mail = Mail(current_app)
        
        # Get email recipients (admin users or configured email)
        admin_users = User.query.filter_by(role='admin', is_active=True).all()
        recipients = [user.email for user in admin_users if user.email]
        
        # Fallback to default email if no admin users
        if not recipients:
            recipients = [current_app.config.get('MAIL_DEFAULT_RECIPIENT', 'info@lawedge.com')]
        
        # Send email to admin/staff
        admin_subject = f"New Enquiry: {enquiry.subject}"
        admin_html = render_template('email/enquiry_admin.html', enquiry=enquiry)
        admin_msg = Message(
            admin_subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@lawedge.com'),
            recipients=recipients,
            html=admin_html
        )
        mail.send(admin_msg)
        
        # Send confirmation email to client
        if enquiry.email:
            client_subject = "Thank You for Your Enquiry - LawEdge"
            client_html = render_template('email/enquiry_client.html', enquiry=enquiry)
            client_msg = Message(
                client_subject,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@lawedge.com'),
                recipients=[enquiry.email],
                html=client_html
            )
            mail.send(client_msg)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending enquiry email: {str(e)}")
        return False

def create_enquiry_notification(enquiry):
    """Create notification for admin users about new enquiry"""
    try:
        admin_users = User.query.filter_by(role='admin', is_active=True).all()
        
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title="New Enquiry Received",
                message=f"New enquiry from {enquiry.name}: {enquiry.subject}",
                notification_type='enquiry'
            )
            db.session.add(notification)
        
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"Error creating enquiry notification: {str(e)}")
        return False

@enquiry_bp.route('/contact', methods=['GET'])
def contact():
    """Display enquiry form"""
    form = EnquiryForm()
    return render_template('enquiry.html', form=form)

@enquiry_bp.route('/enquiry/submit', methods=['POST'])
def submit_enquiry():
    """Handle enquiry form submission"""
    form = EnquiryForm()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request
        if form.validate_on_submit():
            try:
                # Sanitize input data
                name = sanitize_input(form.name.data)
                email = sanitize_input(form.email.data).lower()
                phone = sanitize_input(form.phone.data)
                subject = sanitize_input(form.subject.data)
                message = sanitize_input(form.message.data)
                practice_area = form.practice_area.data
                urgency_level = form.urgency_level.data
                preferred_contact = form.preferred_contact.data
                
                # Additional validation
                if not validate_phone_number(phone):
                    return jsonify({
                        'success': False,
                        'message': 'Please enter a valid phone number'
                    })
                
                # Create enquiry record
                enquiry = Enquiry(
                    name=name,
                    email=email,
                    phone=phone,
                    subject=subject,
                    message=message,
                    practice_area=practice_area,
                    urgency_level=urgency_level,
                    preferred_contact=preferred_contact,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                db.session.add(enquiry)
                db.session.commit()
                
                # Log activity
                log_activity = ActivityLog(
                    action='create_enquiry',
                    resource_type='enquiry',
                    resource_id=enquiry.id,
                    details=f'New enquiry from {name}: {subject}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(log_activity)
                
                # Send email notifications
                email_sent = send_enquiry_email(enquiry)
                
                # Create notifications
                create_enquiry_notification(enquiry)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Your enquiry has been submitted successfully!'
                })
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error submitting enquiry: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'An error occurred while submitting your enquiry. Please try again.'
                })
        else:
            # Return validation errors
            errors = {}
            for field, errors_list in form.errors.items():
                errors[field] = errors_list[0]
            
            return jsonify({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            })
    
    # Non-AJAX request - redirect to success page
    if form.validate_on_submit():
        try:
            # Sanitize input data
            name = sanitize_input(form.name.data)
            email = sanitize_input(form.email.data).lower()
            phone = sanitize_input(form.phone.data)
            subject = sanitize_input(form.subject.data)
            message = sanitize_input(form.message.data)
            practice_area = form.practice_area.data
            urgency_level = form.urgency_level.data
            preferred_contact = form.preferred_contact.data
            
            # Additional validation
            if not validate_phone_number(phone):
                flash('Please enter a valid phone number', 'danger')
                return render_template('enquiry.html', form=form)
            
            # Create enquiry record
            enquiry = Enquiry(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                practice_area=practice_area,
                urgency_level=urgency_level,
                preferred_contact=preferred_contact,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            db.session.add(enquiry)
            db.session.commit()
            
            # Log activity
            log_activity = ActivityLog(
                action='create_enquiry',
                resource_type='enquiry',
                resource_id=enquiry.id,
                details=f'New enquiry from {name}: {subject}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log_activity)
            
            # Send email notifications
            email_sent = send_enquiry_email(enquiry)
            
            # Create notifications
            create_enquiry_notification(enquiry)
            
            db.session.commit()
            
            flash('Your enquiry has been submitted successfully!', 'success')
            return redirect(url_for('enquiry.enquiry_success'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting enquiry: {str(e)}")
            flash('An error occurred while submitting your enquiry. Please try again.', 'danger')
    
    return render_template('enquiry.html', form=form)

@enquiry_bp.route('/enquiry/success')
def enquiry_success():
    """Display enquiry success page"""
    return render_template('enquiry_success.html')

# Admin routes for managing enquiries
@enquiry_bp.route('/admin/enquiries')
def admin_enquiries():
    """Display all enquiries for admin users"""
    # This would require login check - simplified for now
    enquiries = Enquiry.query.order_by(Enquiry.created_at.desc()).all()
    return render_template('admin/enquiries.html', enquiries=enquiries)

@enquiry_bp.route('/admin/enquiries/<int:enquiry_id>')
def view_enquiry(enquiry_id):
    """View specific enquiry details"""
    # This would require login check - simplified for now
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    return render_template('admin/view_enquiry.html', enquiry=enquiry)

@enquiry_bp.route('/admin/enquiries/<int:enquiry_id>/update', methods=['POST'])
def update_enquiry(enquiry_id):
    """Update enquiry status and notes"""
    # This would require login check - simplified for now
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    
    status = request.form.get('status')
    notes = request.form.get('notes')
    assigned_to = request.form.get('assigned_to', type=int)
    
    if status:
        enquiry.status = status
    if notes:
        enquiry.notes = notes
    if assigned_to:
        enquiry.assigned_to = assigned_to
    
    enquiry.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Enquiry updated successfully!', 'success')
    return redirect(url_for('enquiry.view_enquiry', enquiry_id=enquiry_id))
