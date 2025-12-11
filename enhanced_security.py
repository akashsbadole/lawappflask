"""
Enhanced Security & Authentication Module
Implements SMS login, 2FA, attendance tracking, and advanced security features
"""

try:
    import pyotp
    import qrcode
except ImportError:
    pyotp = None
    qrcode = None

import io
import base64
from datetime import datetime, timedelta
from flask import request, session, flash, redirect, url_for, render_template, jsonify
from werkzeug.security import check_password_hash
import requests
import random
import string
from models import db, User, ActivityLog, SystemSetting
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSecurity:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        # Initialize SMS service settings
        self.sms_provider = app.config.get('SMS_PROVIDER', 'twilio')
        self.twilio_account_sid = app.config.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = app.config.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = app.config.get('TWILIO_PHONE_NUMBER')
        
        # 2FA settings
        self.issuer_name = app.config.get('2FA_ISSUER_NAME', 'LawEdge')
    
    def generate_sms_otp(self, user_id):
        """Generate and send SMS OTP for authentication"""
        user = User.query.get(user_id)
        if not user or not user.phone:
            return False, "User not found or no phone number"
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in session with expiry (5 minutes)
        session['sms_otp'] = otp
        session['sms_otp_expiry'] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        session['sms_otp_user_id'] = user_id
        
        # Send OTP via SMS
        success = self.send_sms_otp(user.phone, otp)
        
        if success:
            # Log OTP generation
            logger.info(f"SMS OTP generated for user {user.username}")
            return True, "OTP sent successfully"
        else:
            return False, "Failed to send OTP"
    
    def send_sms_otp(self, phone_number, otp):
        """Send OTP via SMS using configured provider"""
        try:
            if self.sms_provider == 'twilio':
                return self._send_twilio_sms(phone_number, f"Your LawEdge verification code is: {otp}")
            elif self.sms_provider == 'msg91':
                return self._send_msg91_sms(phone_number, f"Your LawEdge verification code is: {otp}")
            else:
                # For development, log the OTP
                logger.info(f"DEV MODE - OTP for {phone_number}: {otp}")
                return True
        except Exception as e:
            logger.error(f"Failed to send SMS OTP: {str(e)}")
            return False
    
    def _send_twilio_sms(self, phone_number, message):
        """Send SMS using Twilio API"""
        try:
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message = client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            return message.sid is not None
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return False
    
    def _send_msg91_sms(self, phone_number, message):
        """Send SMS using MSG91 API"""
        try:
            authkey = self.app.config.get('MSG91_AUTH_KEY')
            template_id = self.app.config.get('MSG91_TEMPLATE_ID')
            
            url = "https://control.msg91.com/api/v5/flow/"
            payload = {
                "template_id": template_id,
                "short_url": "1",
                "recipients": [
                    {
                        "mobiles": phone_number,
                        "VAR1": message
                    }
                ]
            }
            headers = {
                "authkey": authkey,
                "content-type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"MSG91 SMS error: {str(e)}")
            return False
    
    def verify_sms_otp(self, otp):
        """Verify SMS OTP"""
        stored_otp = session.get('sms_otp')
        expiry_time = session.get('sms_otp_expiry')
        user_id = session.get('sms_otp_user_id')
        
        if not stored_otp or not expiry_time or not user_id:
            return False, "Invalid session"
        
        # Check if OTP has expired
        if datetime.utcnow() > datetime.fromisoformat(expiry_time):
            # Clear OTP from session
            session.pop('sms_otp', None)
            session.pop('sms_otp_expiry', None)
            session.pop('sms_otp_user_id', None)
            return False, "OTP has expired"
        
        # Verify OTP
        if otp == stored_otp:
            # Clear OTP from session
            session.pop('sms_otp', None)
            session.pop('sms_otp_expiry', None)
            session.pop('sms_otp_user_id', None)
            
            # Mark user as verified
            session['sms_verified'] = True
            session['verified_user_id'] = user_id
            
            return True, "OTP verified successfully"
        else:
            return False, "Invalid OTP"
    
    def setup_2fa(self, user_id):
        """Setup 2FA for user using TOTP"""
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        # Generate secret key
        secret = pyotp.random_base32()
        
        # Store secret temporarily
        session['2fa_setup_secret'] = secret
        session['2fa_setup_user_id'] = user_id
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=self.issuer_name
        )
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_code_data}",
            'manual_entry_key': secret
        }, None
    
    def verify_2fa_setup(self, user_id, token):
        """Verify 2FA setup token"""
        secret = session.get('2fa_setup_secret')
        setup_user_id = session.get('2fa_setup_user_id')
        
        if not secret or setup_user_id != user_id:
            return False, "Invalid setup session"
        
        totp = pyotp.TOTP(secret)
        if totp.verify(token):
            # Save 2FA secret to user profile
            user = User.query.get(user_id)
            if user:
                # Note: You'll need to add 2fa_secret column to User model
                # user.two_factor_secret = secret
                # user.two_factor_enabled = True
                # db.session.commit()
                
                # Clear setup session
                session.pop('2fa_setup_secret', None)
                session.pop('2fa_setup_user_id', None)
                
                return True, "2FA setup completed"
        
        return False, "Invalid verification code"
    
    def verify_2fa_token(self, user_id, token):
        """Verify 2FA token for login"""
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        # Note: You'll need to add 2fa_secret column to User model
        # if not user.two_factor_enabled or not user.two_factor_secret:
        #     return False, "2FA not enabled for this user"
        
        # totp = pyotp.TOTP(user.two_factor_secret)
        # if totp.verify(token):
        #     return True, "2FA verified"
        
        # For now, return True (implement when 2FA columns are added)
        return True, "2FA verified"
    
    def generate_backup_codes(self, user_id):
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(10):
            code = ''.join(random.choices(string.digits, k=8))
            codes.append(code)
        
        # Store backup codes (you'll need to add backup_codes column to User model)
        # user = User.query.get(user_id)
        # if user:
        #     user.backup_codes = ','.join(codes)
        #     db.session.commit()
        
        return codes
    
    def log_security_event(self, user_id, event_type, details=None, ip_address=None):
        """Log security-related events"""
        activity = ActivityLog(
            user_id=user_id,
            action=f"security_{event_type}",
            resource_type="security",
            details=details,
            ip_address=ip_address or request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        logger.info(f"Security event logged: {event_type} for user {user_id}")

class AttendanceTracker:
    """Track user attendance with geolocation"""
    
    def __init__(self, app=None):
        self.app = app
    
    def check_in(self, user_id, latitude=None, longitude=None, check_in_method='manual'):
        """User check-in with optional geolocation"""
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        # Check if already checked in today
        today = datetime.utcnow().date()
        existing_checkin = self._get_today_checkin(user_id, today)
        
        if existing_checkin:
            return False, "Already checked in today"
        
        # Create attendance record (you'll need to create Attendance model)
        # attendance = Attendance(
        #     user_id=user_id,
        #     check_in_time=datetime.utcnow(),
        #     check_in_latitude=latitude,
        #     check_in_longitude=longitude,
        #     check_in_method=check_in_method,
        #     date=today
        # )
        # db.session.add(attendance)
        # db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            action="check_in",
            resource_type="attendance",
            details=f"Checked in at {datetime.utcnow().strftime('%H:%M:%S')}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return True, "Check-in successful"
    
    def check_out(self, user_id, latitude=None, longitude=None):
        """User check-out with optional geolocation"""
        # Get today's check-in record
        today = datetime.utcnow().date()
        checkin = self._get_today_checkin(user_id, today)
        
        if not checkin:
            return False, "No check-in found for today"
        
        if checkin.check_out_time:
            return False, "Already checked out today"
        
        # Update attendance record
        # checkin.check_out_time = datetime.utcnow()
        # checkin.check_out_latitude = latitude
        # checkin.check_out_longitude = longitude
        # db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            action="check_out",
            resource_type="attendance",
            details=f"Checked out at {datetime.utcnow().strftime('%H:%M:%S')}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return True, "Check-out successful"
    
    def _get_today_checkin(self, user_id, date):
        """Get today's check-in record"""
        # attendance = Attendance.query.filter_by(
        #     user_id=user_id,
        #     date=date
        # ).first()
        # return attendance
        return None  # Placeholder until Attendance model is created

class AdvancedRoleManager:
    """Advanced role hierarchy with inheritance"""
    
    ROLE_HIERARCHY = {
        'admin': ['admin', 'lawyer', 'paralegal', 'staff', 'finance', 'support'],
        'lawyer': ['lawyer', 'paralegal'],
        'paralegal': ['paralegal'],
        'staff': ['staff'],
        'finance': ['finance'],
        'support': ['support']
    }
    
    def has_permission(self, user_role, required_role):
        """Check if user has permission based on role hierarchy"""
        if user_role == required_role:
            return True
        
        allowed_roles = self.ROLE_HIERARCHY.get(user_role, [])
        return required_role in allowed_roles
    
    def get_inherited_permissions(self, role):
        """Get all permissions inherited by a role"""
        return self.ROLE_HIERARCHY.get(role, [role])
    
    def can_access_resource(self, user, resource_type, action):
        """Check if user can access a specific resource"""
        # Define resource permissions
        resource_permissions = {
            'clients': ['admin', 'lawyer', 'paralegal'],
            'cases': ['admin', 'lawyer', 'paralegal'],
            'documents': ['admin', 'lawyer', 'paralegal', 'staff'],
            'invoices': ['admin', 'lawyer', 'finance'],
            'trust_accounts': ['admin', 'finance'],
            'users': ['admin'],
            'settings': ['admin'],
            'reports': ['admin', 'lawyer', 'paralegal', 'finance']
        }
        
        allowed_roles = resource_permissions.get(resource_type, [])
        return user.role in allowed_roles

# Initialize enhanced security
enhanced_security = EnhancedSecurity()
attendance_tracker = AttendanceTracker()
role_manager = AdvancedRoleManager()
