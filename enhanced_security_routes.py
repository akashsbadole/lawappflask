"""
Enhanced Security Routes
Implements routes for SMS login, 2FA, attendance tracking, and advanced security features
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from models import db, User, ActivityLog, Attendance, AttendanceRecord, SecurityEvent
from enhanced_security import enhanced_security, attendance_tracker, role_manager
from functools import wraps
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_security_bp = Blueprint('enhanced_security', __name__, url_prefix='/security')

# Helper decorators
def sms_verification_required(f):
    """Decorator to require SMS verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('sms_verified'):
            flash('SMS verification required', 'warning')
            return redirect(url_for('enhanced_security.sms_verify'))
        return f(*args, **kwargs)
    return decorated_function

def two_factor_required(f):
    """Decorator to require 2FA verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('2fa_verified'):
            flash('Two-factor authentication required', 'warning')
            return redirect(url_for('enhanced_security.two_factor_verify'))
        return f(*args, **kwargs)
    return decorated_function

# SMS Authentication Routes
@enhanced_security_bp.route('/sms-login', methods=['GET', 'POST'])
def sms_login():
    """Send SMS OTP for login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active and user.sms_otp_enabled:
            # Check if account is locked
            if user.is_account_locked():
                flash('Account is temporarily locked due to failed login attempts', 'danger')
                return render_template('security/sms_login.html')
            
            # Generate and send SMS OTP
            success, message = enhanced_security.generate_sms_otp(user.id)
            
            if success:
                flash('OTP sent to your registered mobile number', 'success')
                session['pending_user_id'] = user.id
                return redirect(url_for('enhanced_security.sms_verify'))
            else:
                flash(f'Failed to send OTP: {message}', 'danger')
                user.increment_failed_login()
                db.session.commit()
        else:
            # Log failed login attempt
            if user:
                user.increment_failed_login()
                db.session.commit()
                enhanced_security.log_security_event(
                    user.id, 'login_failed', 
                    f'Failed login attempt for username: {username}',
                    request.remote_addr
                )
            
            flash('Invalid username or password', 'danger')
    
    return render_template('security/sms_login.html')

@enhanced_security_bp.route('/sms-verify', methods=['GET', 'POST'])
def sms_verify():
    """Verify SMS OTP"""
    if 'pending_user_id' not in session:
        return redirect(url_for('enhanced_security.sms_login'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        success, message = enhanced_security.verify_sms_otp(otp)
        
        if success:
            user_id = session.get('verified_user_id')
            user = User.query.get(user_id)
            
            if user:
                # Reset failed login attempts
                user.failed_login_attempts = 0
                user.account_locked_until = None
                db.session.commit()
                
                # Log successful login
                enhanced_security.log_security_event(
                    user.id, 'login_success_sms',
                    'Successful login via SMS OTP',
                    request.remote_addr
                )
                
                # Set session
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                session['full_name'] = user.full_name
                session['sms_verified'] = True
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                flash(f'Welcome back, {user.full_name}!', 'success')
                return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')
    
    return render_template('security/sms_verify.html')

# Two-Factor Authentication Routes
@enhanced_security_bp.route('/2fa/setup', methods=['GET', 'POST'])
def two_factor_setup():
    """Setup 2FA for user"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        if 'enable' in request.form:
            # Generate 2FA setup data
            if pyotp and qrcode:
                setup_data, error = enhanced_security.setup_2fa(user.id)
                
                if setup_data:
                    return render_template('security/2fa_setup.html', 
                                         setup_data=setup_data, 
                                         step='verify')
                else:
                    flash(f'Error setting up 2FA: {error}', 'danger')
            else:
                flash('2FA libraries not available. Please install pyotp and qrcode.', 'danger')
        
        elif 'verify' in request.form:
            token = request.form.get('token')
            
            success, message = enhanced_security.verify_2fa_setup(user.id, token)
            
            if success:
                flash('Two-factor authentication enabled successfully!', 'success')
                enhanced_security.log_security_event(
                    user.id, '2fa_enabled',
                    'User enabled 2FA',
                    request.remote_addr
                )
                return redirect(url_for('enhanced_security.security_settings'))
            else:
                flash(message, 'danger')
    
    return render_template('security/2fa_setup.html', step='setup')

@enhanced_security_bp.route('/2fa/verify', methods=['GET', 'POST'])
def two_factor_verify():
    """Verify 2FA token during login"""
    if 'pending_2fa_user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        token = request.form.get('token')
        user_id = session.get('pending_2fa_user_id')
        
        success, message = enhanced_security.verify_2fa_token(user_id, token)
        
        if success:
            user = User.query.get(user_id)
            
            # Log successful 2FA verification
            enhanced_security.log_security_event(
                user.id, '2fa_verified',
                'Successful 2FA verification',
                request.remote_addr
            )
            
            # Set session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            session['2fa_verified'] = True
            
            # Clear pending 2FA
            session.pop('pending_2fa_user_id', None)
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')
    
    return render_template('security/2fa_verify.html')

@enhanced_security_bp.route('/2fa/disable', methods=['POST'])
def two_factor_disable():
    """Disable 2FA for user"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Verify password before disabling 2FA
    password = request.form.get('password')
    if not user.check_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('enhanced_security.security_settings'))
    
    # Disable 2FA
    user.two_factor_enabled = False
    user.two_factor_secret = None
    user.backup_codes = None
    db.session.commit()
    
    # Log 2FA disable
    enhanced_security.log_security_event(
        user.id, '2fa_disabled',
        'User disabled 2FA',
        request.remote_addr
    )
    
    flash('Two-factor authentication disabled', 'info')
    return redirect(url_for('enhanced_security.security_settings'))

@enhanced_security_bp.route('/2fa/backup-codes')
def backup_codes():
    """Generate and display backup codes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if not user.two_factor_enabled:
        flash('2FA must be enabled to generate backup codes', 'warning')
        return redirect(url_for('enhanced_security.security_settings'))
    
    # Generate new backup codes
    codes = enhanced_security.generate_backup_codes(user.id)
    
    return render_template('security/backup_codes.html', codes=codes)

# Attendance Routes
@enhanced_security_bp.route('/attendance/check-in', methods=['GET', 'POST'])
def attendance_check_in():
    """User check-in with optional geolocation"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        check_in_method = request.form.get('check_in_method', 'manual')
        
        success, message = attendance_tracker.check_in(
            user.id, latitude, longitude, check_in_method
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('enhanced_security.attendance'))
        else:
            flash(message, 'danger')
    
    return render_template('security/attendance_check_in.html')

@enhanced_security_bp.route('/attendance/check-out', methods=['GET', 'POST'])
def attendance_check_out():
    """User check-out with optional geolocation"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        success, message = attendance_tracker.check_out(
            user.id, latitude, longitude
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('enhanced_security.attendance'))
        else:
            flash(message, 'danger')
    
    return render_template('security/attendance_check_out.html')

@enhanced_security_bp.route('/attendance')
def attendance():
    """View attendance records"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get attendance records for the current month
    today = datetime.utcnow().date()
    start_of_month = today.replace(day=1)
    start_of_month_dt = datetime.combine(start_of_month, datetime.min.time())
    end_of_month_dt = datetime.combine(today, datetime.max.time())
    
    attendance_records = AttendanceRecord.query.filter(
        AttendanceRecord.user_id == user.id,
        AttendanceRecord.check_in_time >= start_of_month_dt,
        AttendanceRecord.check_in_time <= end_of_month_dt
    ).order_by(AttendanceRecord.check_in_time.desc()).all()
    
    # Calculate statistics
    total_days = len(attendance_records)
    total_hours = sum(record.calculate_total_hours() or 0 for record in attendance_records)
    overtime_hours = sum(0 for record in attendance_records if record.total_hours and record.total_hours > 8)
    
    return render_template('security/attendance.html',
                         attendance_records=attendance_records,
                         total_days=total_days,
                         total_hours=total_hours,
                         overtime_hours=overtime_hours)

# Security Settings Routes
@enhanced_security_bp.route('/settings')
def security_settings():
    """View and manage security settings"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    return render_template('security/settings.html', user=user)

@enhanced_security_bp.route('/settings/update', methods=['POST'])
def update_security_settings():
    """Update security settings"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Update SMS OTP setting
    sms_otp_enabled = 'sms_otp_enabled' in request.form
    if sms_otp_enabled and not user.phone:
        flash('Phone number is required to enable SMS OTP', 'danger')
        return redirect(url_for('enhanced_security.security_settings'))
    
    user.sms_otp_enabled = sms_otp_enabled
    
    # Log security setting change
    enhanced_security.log_security_event(
        user.id, 'security_settings_updated',
        f'SMS OTP enabled: {sms_otp_enabled}',
        request.remote_addr
    )
    
    db.session.commit()
    
    flash('Security settings updated successfully', 'success')
    return redirect(url_for('enhanced_security.security_settings'))

# API Routes
@enhanced_security_bp.route('/api/send-sms-otp', methods=['POST'])
def api_send_sms_otp():
    """API endpoint to send SMS OTP"""
    username = request.json.get('username')
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    if not user.sms_otp_enabled:
        return jsonify({'success': False, 'message': 'SMS OTP not enabled for this user'})
    
    success, message = enhanced_security.generate_sms_otp(user.id)
    
    return jsonify({'success': success, 'message': message})

@enhanced_security_bp.route('/api/verify-sms-otp', methods=['POST'])
def api_verify_sms_otp():
    """API endpoint to verify SMS OTP"""
    otp = request.json.get('otp')
    
    if not otp:
        return jsonify({'success': False, 'message': 'OTP required'})
    
    success, message = enhanced_security.verify_sms_otp(otp)
    
    if success:
        user_id = session.get('verified_user_id')
        user = User.query.get(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'message': 'OTP verified successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role
                }
            })
    
    return jsonify({'success': success, 'message': message})