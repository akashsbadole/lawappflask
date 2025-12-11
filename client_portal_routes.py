"""
Client Portal Routes
Provides web interface for client portal with 2FA, document access, and communication
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, send_file
from functools import wraps
from werkzeug.security import check_password_hash
from models import db, User, Client, Case, Document, Appointment, ClientPortalUser, Message, ActivityLog
from client_portal import client_portal
from datetime import datetime, timedelta
import logging

# Create blueprint
client_portal_bp = Blueprint('client_portal', __name__)

# Configure logging
logger = logging.getLogger(__name__)

def portal_login_required(f):
    """Decorator to require portal login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'portal_user_id' not in session:
            return redirect(url_for('client_portal.login'))
        return f(*args, **kwargs)
    return decorated_function

# Main portal routes
@client_portal_bp.route('/')
def portal_home():
    """Portal home page - redirect to login or dashboard"""
    if 'portal_user_id' in session:
        return redirect(url_for('client_portal.dashboard'))
    else:
        return redirect(url_for('client_portal.login'))

@client_portal_bp.route('/login', methods=['GET', 'POST'])
def portal_login():
    """Portal login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('portal/login.html')
        
        # Authenticate user
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        result = client_portal.authenticate_portal_user(
            username, password, ip_address, user_agent
        )
        
        if isinstance(result, dict):
            # Login successful but requires 2FA setup or verification
            if result.get('requires_2fa_setup'):
                session['temp_user_id'] = result['user']['id']
                session['2fa_setup_data'] = result['setup_data']
                return redirect(url_for('client_portal.setup_2fa'))
            
            elif result.get('requires_2fa_verification'):
                session['temp_user_id'] = result['user']['id']
                return redirect(url_for('client_portal.verify_2fa'))
            
            # Login complete
            session['portal_user_id'] = result['user']['id']
            session['portal_username'] = result['user']['username']
            session['portal_client_id'] = result['user']['client_id']
            session['portal_login_time'] = datetime.utcnow()
            
            flash('Login successful!', 'success')
            return redirect(url_for('client_portal.dashboard'))
        
        else:
            # Login failed
            flash(result, 'danger')
            return render_template('portal/login.html')
    
    return render_template('portal/login.html')

@client_portal_bp.route('/logout')
def portal_logout():
    """Portal logout"""
    if 'portal_user_id' in session:
        # Log logout activity
        activity = ActivityLog(
            user_id=session.get('portal_user_id'),
            action="portal_logout",
            resource_type="client_portal",
            resource_id=session.get('portal_user_id'),
            details="User logged out of client portal",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
    
    # Clear session
    session.pop('portal_user_id', None)
    session.pop('portal_username', None)
    session.pop('portal_client_id', None)
    session.pop('portal_login_time', None)
    session.pop('temp_user_id', None)
    session.pop('2fa_setup_data', None)
    
    flash('You have been logged out', 'info')
    return redirect(url_for('client_portal.login'))

# 2FA Setup and Verification
@client_portal_bp.route('/setup-2fa', methods=['GET', 'POST'])
@portal_login_required
def setup_2fa():
    """Setup 2FA for user"""
    temp_user_id = session.get('temp_user_id')
    if not temp_user_id:
        return redirect(url_for('client_portal.login'))
    
    if request.method == 'POST':
        token = request.form.get('token')
        
        if not token:
            flash('Authentication token is required', 'danger')
            return render_template('portal/setup_2fa.html', 
                                 setup_data=session.get('2fa_setup_data'))
        
        # Verify token and enable 2FA
        result = client_portal.enable_2fa_for_user(temp_user_id, token)
        
        if result:
            # Clear temporary session data
            session.pop('temp_user_id', None)
            session.pop('2fa_setup_data', None)
            
            # Set permanent session
            user = ClientPortalUser.query.get(temp_user_id)
            session['portal_user_id'] = user.id
            session['portal_username'] = user.username
            session['portal_client_id'] = user.client_id
            session['portal_login_time'] = datetime.utcnow()
            
            flash('2FA enabled successfully!', 'success')
            return redirect(url_for('client_portal.dashboard'))
        else:
            flash('Invalid token. Please try again.', 'danger')
            return render_template('portal/setup_2fa.html', 
                                 setup_data=session.get('2fa_setup_data'))
    
    setup_data = session.get('2fa_setup_data')
    if not setup_data:
        return redirect(url_for('client_portal.login'))
    
    return render_template('portal/setup_2fa.html', setup_data=setup_data)

@client_portal_bp.route('/verify-2fa', methods=['GET', 'POST'])
@portal_login_required
def verify_2fa():
    """Verify 2FA token"""
    temp_user_id = session.get('temp_user_id')
    if not temp_user_id:
        return redirect(url_for('client_portal.login'))
    
    if request.method == 'POST':
        token = request.form.get('token')
        backup_code = request.form.get('backup_code')
        
        if not token and not backup_code:
            flash('Authentication token or backup code is required', 'danger')
            return render_template('portal/verify_2fa.html')
        
        # Verify 2FA token
        result = client_portal.verify_2fa_token(temp_user_id, token, backup_code)
        
        if result:
            # Clear temporary session data
            session.pop('temp_user_id', None)
            
            # Set permanent session
            user = ClientPortalUser.query.get(temp_user_id)
            session['portal_user_id'] = user.id
            session['portal_username'] = user.username
            session['portal_client_id'] = user.client_id
            session['portal_login_time'] = datetime.utcnow()
            
            flash('Authentication successful!', 'success')
            return redirect(url_for('client_portal.dashboard'))
        else:
            flash('Invalid token or backup code. Please try again.', 'danger')
            return render_template('portal/verify_2fa.html')
    
    return render_template('portal/verify_2fa.html')

# Dashboard
@client_portal_bp.route('/dashboard')
@portal_login_required
def portal_dashboard():
    """Client portal dashboard"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    if not user_id or not client_id:
        return redirect(url_for('client_portal.login'))
    
    # Get user and client info
    user = ClientPortalUser.query.get(user_id)
    client = Client.query.get(client_id)
    
    if not user or not client:
        flash('User or client not found', 'danger')
        return redirect(url_for('client_portal.logout'))
    
    # Get user's cases
    cases = client_portal.get_client_cases(client_id, user_id)
    
    # Get user's appointments
    appointments = client_portal.get_client_appointments(client_id, user_id)
    
    # Get recent messages
    messages = client_portal.get_portal_messages(user_id, limit=5)
    
    # Get recent documents
    documents = client_portal.get_client_documents(client_id, user_id)
    
    # Check for unread messages
    unread_messages = [msg for msg in messages if not msg.is_read and msg.recipient_id == user_id]
    
    return render_template('portal/dashboard.html',
                         user=user,
                         client=client,
                         cases=cases,
                         appointments=appointments,
                         messages=messages,
                         documents=documents[:5],  # Limit to 5 most recent
                         unread_count=len(unread_messages))

# Cases
@client_portal_bp.route('/cases')
@portal_login_required
def portal_cases():
    """Client cases page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    cases = client_portal.get_client_cases(client_id, user_id)
    
    return render_template('portal/cases.html', cases=cases)

@client_portal_bp.route('/case/<int:case_id>')
@portal_login_required
def portal_case_detail(case_id):
    """Case detail page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    case = Case.query.get_or_404(case_id)
    
    # Check if user has access to this case
    if case.client_id != client_id:
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.cases'))
    
    # Get case documents
    case_documents = Document.query.filter_by(case_id=case_id).all()
    
    return render_template('portal/case_detail.html', case=case, documents=case_documents)

# Documents
@client_portal_bp.route('/documents')
@portal_login_required
def portal_documents():
    """Client documents page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    documents = client_portal.get_client_documents(client_id, user_id)
    
    return render_template('portal/documents.html', documents=documents)

@client_portal_bp.route('/document/<int:document_id>')
@portal_login_required
def portal_document_detail(document_id):
    """Document detail page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    document = Document.query.get_or_404(document_id)
    
    # Check if user has access to this document
    if document.client_id != client_id:
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.documents'))
    
    # Check if document is confidential and user has permission
    if document.is_confidential:
        user = ClientPortalUser.query.get(user_id)
        if not client_portal._check_document_access(user, document):
            flash('Access denied', 'danger')
            return redirect(url_for('client_portal.documents'))
    
    return render_template('portal/document_detail.html', document=document)

@client_portal_bp.route('/download-document/<int:document_id>')
@portal_login_required
def portal_download_document(document_id):
    """Download document"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if document.client_id != client_id:
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.documents'))
    
    if document.is_confidential:
        user = ClientPortalUser.query.get(user_id)
        if not client_portal._check_document_access(user, document):
            flash('Access denied', 'danger')
            return redirect(url_for('client_portal.documents'))
    
    try:
        return send_file(document.file_path, as_attachment=True, download_name=document.filename)
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {str(e)}")
        flash('Error downloading document', 'danger')
        return redirect(url_for('client_portal.document_detail', document_id=document_id))

# Appointments
@client_portal_bp.route('/appointments')
@portal_login_required
def portal_appointments():
    """Client appointments page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    appointments = client_portal.get_client_appointments(client_id, user_id)
    
    return render_template('portal/appointments.html', appointments=appointments)

@client_portal_bp.route('/appointment/<int:appointment_id>')
@portal_login_required
def portal_appointment_detail(appointment_id):
    """Appointment detail page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if user has access to this appointment
    if appointment.client_id != client_id:
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.appointments'))
    
    return render_template('portal/appointment_detail.html', appointment=appointment)

@client_portal_bp.route('/schedule-appointment', methods=['GET', 'POST'])
@portal_login_required
def portal_schedule_appointment():
    """Schedule appointment page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        requested_time_str = request.form.get('requested_time')
        notes = request.form.get('notes')
        
        if not title or not requested_time_str:
            flash('Title and requested time are required', 'danger')
            return render_template('portal/schedule_appointment.html')
        
        try:
            requested_time = datetime.strptime(requested_time_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date/time format', 'danger')
            return render_template('portal/schedule_appointment.html')
        
        # Create appointment request
        result = client_portal.schedule_appointment_in_portal(
            None, client_id, requested_time, notes
        )
        
        if result:
            flash('Appointment request submitted successfully!', 'success')
            return redirect(url_for('client_portal.appointments'))
        else:
            flash('Failed to submit appointment request', 'danger')
    
    return render_template('portal/schedule_appointment.html')

# Messages
@client_portal_bp.route('/messages')
@portal_login_required
def portal_messages():
    """Client messages page"""
    user_id = session.get('portal_user_id')
    
    messages = client_portal.get_portal_messages(user_id)
    
    # Separate sent and received messages
    sent_messages = [msg for msg in messages if msg.sender_id == user_id]
    received_messages = [msg for msg in messages if msg.recipient_id == user_id]
    
    return render_template('portal/messages.html',
                         sent_messages=sent_messages,
                         received_messages=received_messages)

@client_portal_bp.route('/message/<int:message_id>')
@portal_login_required
def portal_message_detail(message_id):
    """Message detail page"""
    user_id = session.get('portal_user_id')
    
    message = Message.query.get_or_404(message_id)
    
    # Check if user has access to this message
    if message.sender_id != user_id and message.recipient_id != user_id:
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.messages'))
    
    # Mark as read if user is recipient
    if message.recipient_id == user_id and not message.is_read:
        client_portal.mark_message_read(message_id, user_id)
    
    return render_template('portal/message_detail.html', message=message)

@client_portal_bp.route('/send-message', methods=['GET', 'POST'])
@portal_login_required
def portal_send_message():
    """Send message page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        message = request.form.get('message')
        message_type = request.form.get('message_type', 'general')
        
        if not recipient_id or not message:
            flash('Recipient and message are required', 'danger')
            return render_template('portal/send_message.html')
        
        # Get available recipients (lawyer for this client)
        from models import User
        client = Client.query.get(client_id)
        lawyer = User.query.filter_by(id=client.assigned_lawyer_id).first()
        
        if not lawyer:
            flash('No assigned lawyer found', 'danger')
            return render_template('portal/send_message.html')
        
        # Create portal user for lawyer if not exists
        lawyer_portal_user = ClientPortalUser.query.filter_by(email=lawyer.email).first()
        if not lawyer_portal_user:
            lawyer_portal_user = ClientPortalUser(
                client_id=client_id,
                username=lawyer.username,
                email=lawyer.email,
                password_hash=lawyer.password_hash,
                is_active=True,
                role='lawyer'
            )
            db.session.add(lawyer_portal_user)
            db.session.commit()
        
        # Send message
        result = client_portal.send_portal_message(
            user_id, lawyer_portal_user.id, message, message_type
        )
        
        if result:
            flash('Message sent successfully!', 'success')
            return redirect(url_for('client_portal.messages'))
        else:
            flash('Failed to send message', 'danger')
    
    return render_template('portal/send_message.html')

# Profile and Settings
@client_portal_bp.route('/profile')
@portal_login_required
def portal_profile():
    """Client profile page"""
    user_id = session.get('portal_user_id')
    client_id = session.get('portal_client_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    client = Client.query.get_or_404(client_id)
    
    return render_template('portal/profile.html', user=user, client=client)

@client_portal_bp.route('/update-profile', methods=['POST'])
@portal_login_required
def portal_update_profile():
    """Update client profile"""
    user_id = session.get('portal_user_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    
    # Update allowed fields
    if request.form.get('email'):
        user.email = request.form.get('email')
    
    # Note: In a real implementation, you might want to verify email ownership
    # before allowing it to be changed
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('client_portal.profile'))

@client_portal_bp.route('/change-password', methods=['GET', 'POST'])
@portal_login_required
def portal_change_password():
    """Change password page"""
    user_id = session.get('portal_user_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('portal/change_password.html')
        
        # Verify current password
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('portal/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('portal/change_password.html')
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('client_portal.profile'))
    
    return render_template('portal/change_password.html')

@client_portal_bp.route('/security')
@portal_login_required
def portal_security():
    """Security settings page"""
    user_id = session.get('portal_user_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    
    return render_template('portal/security.html', user=user)

@client_portal_bp.route('/setup-2fa-security', methods=['POST'])
@portal_login_required
def portal_setup_2fa_security():
    """Setup 2FA from security settings"""
    user_id = session.get('portal_user_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    
    # Setup 2FA
    result = client_portal.setup_2fa_for_user(user_id)
    
    if result:
        return jsonify({'success': True, 'setup_data': result})
    else:
        return jsonify({'success': False, 'message': 'Failed to setup 2FA'})

@client_portal_bp.route('/verify-2fa-security', methods=['POST'])
@portal_login_required
def portal_verify_2fa_security():
    """Verify 2FA from security settings"""
    user_id = session.get('portal_user_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    
    token = request.form.get('token')
    backup_code = request.form.get('backup_code')
    
    # Verify 2FA
    result = client_portal.verify_2fa_token(user_id, token, backup_code)
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid token or backup code'})

@client_portal_bp.route('/disable-2fa', methods=['POST'])
@portal_login_required
def portal_disable_2fa():
    """Disable 2FA from security settings"""
    user_id = session.get('portal_user_id')
    
    user = ClientPortalUser.query.get_or_404(user_id)
    
    password = request.form.get('password')
    
    if not password:
        return jsonify({'success': False, 'message': 'Password is required'})
    
    # Disable 2FA
    result = client_portal.disable_2fa_for_user(user_id, password)
    
    if result:
        return jsonify({'success': True, 'message': '2FA disabled successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to disable 2FA'})

@client_portal_bp.route('/regenerate-backup-codes', methods=['POST'])
@portal_login_required
def portal_regenerate_backup_codes():
    """Regenerate backup codes"""
    user_id = session.get('portal_user_id')
    
    result = client_portal.regenerate_backup_codes(user_id)
    
    if result:
        return jsonify({'success': True, 'message': 'Backup codes regenerated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to regenerate backup codes'})

# AJAX Endpoints
@client_portal_bp.route('/ajax/mark-message-read/<int:message_id>')
@portal_login_required
def ajax_mark_message_read(message_id):
    """Mark message as read (AJAX)"""
    user_id = session.get('portal_user_id')
    
    result = client_portal.mark_message_read(message_id, user_id)
    
    return jsonify({'success': bool(result)})

@client_portal_bp.route('/ajax/get-unread-count')
@portal_login_required
def ajax_get_unread_count():
    """Get unread message count (AJAX)"""
    user_id = session.get('portal_user_id')
    
    messages = client_portal.get_portal_messages(user_id)
    unread_count = len([msg for msg in messages if not msg.is_read and msg.recipient_id == user_id])
    
    return jsonify({'unread_count': unread_count})

# Error handlers
@client_portal_bp.errorhandler(404)
def portal_not_found(error):
    """Handle 404 errors"""
    return render_template('portal/error.html', 
                         error_code=404,
                         error_message='Page not found'), 404

@client_portal_bp.errorhandler(500)
def portal_server_error(error):
    """Handle 500 errors"""
    logger.error(f"Portal server error: {error}")
    return render_template('portal/error.html',
                         error_code=500,
                         error_message='Internal server error'), 500

# API Endpoints for external integrations
@client_portal_bp.route('/api/v1/create-user', methods=['POST'])
def api_create_portal_user():
    """API endpoint to create portal user"""
    data = request.get_json()
    
    client_id = data.get('client_id')
    username = data.get('username')
    email = data.get('email')
    temporary_password = data.get('temporary_password')
    
    if not all([client_id, username, email]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Create portal user
    result, user = client_portal.create_portal_user(
        client_id, username, email, temporary_password
    )
    
    if result:
        return jsonify({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'message': 'Portal user created successfully'
        })
    else:
        return jsonify({'success': False, 'message': 'Failed to create portal user'}), 400

@client_portal_bp.route('/api/v1/authenticate', methods=['POST'])
def api_authenticate_portal_user():
    """API endpoint for portal authentication"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    ip_address = data.get('ip_address', request.remote_addr)
    user_agent = data.get('user_agent', request.headers.get('User-Agent'))
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    # Authenticate user
    result = client_portal.authenticate_portal_user(
        username, password, ip_address, user_agent
    )
    
    return jsonify(result)

@client_portal_bp.route('/api/v1/send-message', methods=['POST'])
def api_send_message():
    """API endpoint to send message"""
    data = request.get_json()
    
    sender_id = data.get('sender_id')
    recipient_id = data.get('recipient_id')
    message = data.get('message')
    message_type = data.get('message_type', 'general')
    
    if not all([sender_id, recipient_id, message]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Send message
    result, msg = client_portal.send_portal_message(
        sender_id, recipient_id, message, message_type
    )
    
    if result:
        return jsonify({
            'success': True,
            'message_id': msg.id,
            'message': 'Message sent successfully'
        })
    else:
        return jsonify({'success': False, 'message': 'Failed to send message'}), 400

# Portal management routes for admin
@client_portal_bp.route('/admin/create-user', methods=['GET', 'POST'])
def admin_create_portal_user():
    """Admin page to create portal user"""
    # Check if user is admin
    user_id = session.get('portal_user_id')
    user = ClientPortalUser.query.get(user_id)
    
    if not user or user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.dashboard'))
    
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        username = request.form.get('username')
        email = request.form.get('email')
        temporary_password = request.form.get('temporary_password')
        is_active = request.form.get('is_active', 'off') == 'on'
        
        if not all([client_id, username, email]):
            flash('All fields except password are required', 'danger')
            return render_template('portal/admin/create_user.html')
        
        # Create portal user
        result, user = client_portal.create_portal_user(
            client_id, username, email, temporary_password
        )
        
        if result:
            if not is_active:
                user.is_active = False
                db.session.commit()
            
            flash('Portal user created successfully!', 'success')
            return redirect(url_for('client_portal.admin_users'))
        else:
            flash('Failed to create portal user', 'danger')
    
    # Get clients for dropdown
    clients = Client.query.all()
    
    return render_template('portal/admin/create_user.html', clients=clients)

@client_portal_bp.route('/admin/users')
def admin_users():
    """Admin page to manage portal users"""
    # Check if user is admin
    user_id = session.get('portal_user_id')
    user = ClientPortalUser.query.get(user_id)
    
    if not user or user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('client_portal.dashboard'))
    
    # Get all portal users
    users = ClientPortalUser.query.all()
    
    return render_template('portal/admin/users.html', users=users)

@client_portal_bp.route('/admin/toggle-user/<int:user_id>', methods=['POST'])
def admin_toggle_user():
    """Toggle user active status"""
    # Check if user is admin
    user_id = session.get('portal_user_id')
    user = ClientPortalUser.query.get(user_id)
    
    if not user or user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    target_user = ClientPortalUser.query.get(user_id)
    if not target_user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Toggle active status
    target_user.is_active = not target_user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {"activated" if target_user.is_active else "deactivated"} successfully',
        'is_active': target_user.is_active
    })
