"""
Enhanced Authentication Routes
Implements SMS login, 2FA, and advanced security features
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, ActivityLog, Attendance
from enhanced_security import enhanced_security, attendance_tracker, role_manager
from datetime import datetime
import logging

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with SMS OTP and 2FA support"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        login_method = request.form.get('login_method', 'password')  # password, sms
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        # Check if account is locked
        if user.is_account_locked():
            flash('Account is locked due to multiple failed login attempts. Please try again later.', 'danger')
            return render_template('login.html')
        
        # Check if user is active
        if not user.is_active:
            flash('Account is deactivated. Please contact administrator.', 'danger')
            return render_template('login.html')
        
        # Verify password
        if not user.check_password(password):
            user.increment_failed_login()
            db.session.commit()
            
            # Log failed login attempt
            enhanced_security.log_security_event(
                user.id, 'login_failed', 
                f'Failed login attempt for username: {username}',
                request.remote_addr
            )
            
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        # Reset failed login attempts on successful password verification
        user.failed_login_attempts = 0
        db.session.commit()
        
        # Handle different login methods
        if login_method == 'sms':
            if not user.phone:
                flash('Phone number not configured for SMS login. Please use password login.', 'warning')
                return render_template('login.html')
            
            if not user.sms_login_enabled:
                flash('SMS login not enabled for this account. Please contact administrator.', 'warning')
                return render_template('login.html')
            
            # Generate and send SMS OTP
            success, message = enhanced_security.generate_sms_otp(user.id)
            if success:
                flash('OTP has been sent to your registered mobile number.', 'success')
                session['pending_user_id'] = user.id
                session['login_method'] = 'sms'
                return redirect(url_for('auth.verify_sms_otp'))
            else:
                flash(f'Failed to send OTP: {message}', 'danger')
                return render_template('login.html')
        
        else:  # password login
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                session['pending_user_id'] = user.id
                session['login_method'] = 'password'
                return redirect(url_for('auth.verify_2fa'))
            
            # Complete login
            return complete_login(user)
    
    return render_template('login.html')

@auth_bp.route('/verify_sms_otp', methods=['GET', 'POST'])
def verify_sms_otp():
    """Verify SMS OTP for login"""
    if 'pending_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        if not otp:
            flash('Please enter the OTP', 'danger')
            return render_template('verify_sms_otp.html')
        
        success, message = enhanced_security.verify_sms_otp(otp)
        
        if success:
            user_id = session.get('verified_user_id')
            user = User.query.get(user_id)
            
            if user:
                return complete_login(user)
            else:
                flash('User not found', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
            return render_template('verify_sms_otp.html')
    
    return render_template('verify_sms_otp.html')

@auth_bp.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Verify 2FA token for login"""
    if 'pending_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session.get('pending_user_id')
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        token = request.form.get('token')
        backup_code = request.form.get('backup_code')
        
        if token:
            # Verify TOTP token
            success, message = enhanced_security.verify_2fa_token(user.id, token)
            if success:
                return complete_login(user)
            else:
                flash('Invalid verification code', 'danger')
        
        elif backup_code:
            # Verify backup code
            if user.verify_backup_code(backup_code):
                flash('Backup code used. Please generate new backup codes for security.', 'warning')
                return complete_login(user)
            else:
                flash('Invalid backup code', 'danger')
        
        else:
            flash('Please enter a verification code or backup code', 'danger')
    
    return render_template('verify_2fa.html', user=user)

@auth_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    """Resend SMS OTP"""
    if 'pending_user_id' not in session:
        return jsonify({'success': False, 'message': 'Invalid session'})
    
    user_id = session.get('pending_user_id')
    success, message = enhanced_security.generate_sms_otp(user_id)
    
    return jsonify({'success': success, 'message': message})

def complete_login(user):
    """Complete the login process"""
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['full_name'] = user.full_name
    
    # Clear pending login session
    session.pop('pending_user_id', None)
    session.pop('login_method', None)
    
    # Log successful login
    enhanced_security.log_security_event(
        user.id, 'login_success', 
        f'User {user.username} logged in successfully',
        request.remote_addr
    )
    
    flash(f'Welcome back, {user.full_name}!', 'success')
    return redirect(url_for('dashboard'))

@auth_bp.route('/setup_2fa', methods=['GET', 'POST'])
def setup_2fa():
    """Setup 2FA for user"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'setup':
            # Generate 2FA setup
            setup_data, error = enhanced_security.setup_2fa(user.id)
            if error:
                flash(error, 'danger')
                return redirect(url_for('auth.setup_2fa'))
            
            return render_template('setup_2fa.html', user=user, setup_data=setup_data)
        
        elif action == 'verify':
            token = request.form.get('token')
            success, message = enhanced_security.verify_2fa_setup(user.id, token)
            
            if success:
                # Generate backup codes
                backup_codes = enhanced_security.generate_backup_codes(user.id)
                
                # Log 2FA setup
                enhanced_security.log_security_event(
                    user.id, '2fa_enabled', 
                    'Two-factor authentication enabled',
                    request.remote_addr
                )
                
                flash('Two-factor authentication enabled successfully!', 'success')
                return render_template('backup_codes.html', backup_codes=backup_codes)
            else:
                flash(message, 'danger')
                return redirect(url_for('auth.setup_2fa'))
        
        elif action == 'disable':
            if user.two_factor_enabled:
                # Verify current password
                password = request.form.get('password')
                if not user.check_password(password):
                    flash('Invalid password', 'danger')
                    return redirect(url_for('auth.setup_2fa'))
                
                # Disable 2FA
                user.two_factor_enabled = False
                user.two_factor_secret = None
                user.backup_codes = None
                db.session.commit()
                
                # Log 2FA disable
                enhanced_security.log_security_event(
                    user.id, '2fa_disabled', 
                    'Two-factor authentication disabled',
                    request.remote_addr
                )
                
                flash('Two-factor authentication disabled', 'info')
            
            return redirect(url_for('auth.setup_2fa'))
    
    return render_template('setup_2fa.html', user=user)

@auth_bp.route('/enable_sms_login', methods=['POST'])
def enable_sms_login():
    """Enable SMS login for user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = User.query.get(session['user_id'])
    
    if not user.phone:
        return jsonify({'success': False, 'message': 'Phone number not configured'})
    
    # Verify current password
    password = request.form.get('password')
    if not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid password'})
    
    # Enable SMS login
    user.sms_login_enabled = True
    db.session.commit()
    
    # Log SMS login enable
    enhanced_security.log_security_event(
        user.id, 'sms_login_enabled', 
        'SMS login enabled',
        request.remote_addr
    )
    
    return jsonify({'success': True, 'message': 'SMS login enabled successfully'})

@auth_bp.route('/attendance/check_in', methods=['POST'])
def check_in():
    """User check-in with geolocation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    check_in_method = request.form.get('method', 'manual')
    
    success, message = attendance_tracker.check_in(
        user_id, latitude, longitude, check_in_method
    )
    
    if success:
        enhanced_security.log_security_event(
            user_id, 'check_in', 
            f'Checked in at {datetime.utcnow().strftime("%H:%M:%S")}',
            request.remote_addr
        )
    
    return jsonify({'success': success, 'message': message})

@auth_bp.route('/attendance/check_out', methods=['POST'])
def check_out():
    """User check-out with geolocation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    
    success, message = attendance_tracker.check_out(
        user_id, latitude, longitude
    )
    
    if success:
        enhanced_security.log_security_event(
            user_id, 'check_out', 
            f'Checked out at {datetime.utcnow().strftime("%H:%M:%S")}',
            request.remote_addr
        )
    
    return jsonify({'success': success, 'message': message})

@auth_bp.route('/attendance/status')
def attendance_status():
    """Get current attendance status"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    today = datetime.utcnow().date()
    
    # Get today's attendance record
    attendance = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()
    
    if attendance:
        return jsonify({
            'success': True,
            'status': 'checked_in' if attendance.check_in_time and not attendance.check_out_time else 'checked_out',
            'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
            'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
            'total_hours': attendance.calculate_total_hours()
        })
    else:
        return jsonify({
            'success': True,
            'status': 'not_checked_in'
        })

@auth_bp.route('/logout')
def logout():
    """Enhanced logout with security logging"""
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Log logout
        enhanced_security.log_security_event(
            user_id, 'logout', 
            'User logged out',
            request.remote_addr
        )
    
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/security_settings')
def security_settings():
    """Security settings page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('security_settings.html', user=user)

@auth_bp.route('/change_password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user = User.query.get(session['user_id'])
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Verify current password
    if not user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    # Check new password confirmation
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'})
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    # Log password change
    enhanced_security.log_security_event(
        user.id, 'password_changed', 
        'Password changed successfully',
        request.remote_addr
    )
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})
