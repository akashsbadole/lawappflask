"""
Enhanced Client Portal Module
Implements secure client portal with 2FA, document access, and communication features
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
import io
import base64
from functools import wraps

# Try to import additional libraries
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import jwt
except ImportError:
    jwt = None

# Configure logging
logger = logging.getLogger(__name__)

class ClientPortal:
    """Enhanced client portal with 2FA and security features"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        # Portal Configuration
        self.portal_url = app.config.get('PORTAL_URL', 'https://lawedge.com/portal')
        self.portal_name = app.config.get('PORTAL_NAME', 'LawEdge Client Portal')
        self.session_timeout = app.config.get('PORTAL_SESSION_TIMEOUT', 8)  # hours
        self.max_login_attempts = app.config.get('PORTAL_MAX_LOGIN_ATTEMPTS', 5)
        self.account_lockout_duration = app.config.get('PORTAL_LOCKOUT_DURATION', 30)  # minutes
        
        # Security Configuration
        self.require_2fa = app.config.get('PORTAL_REQUIRE_2FA', True)
        self.ip_whitelist = app.config.get('PORTAL_IP_WHITELIST', [])
        self.allowed_file_types = app.config.get('PORTAL_ALLOWED_FILE_TYPES', 
                                           ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'])
        self.max_file_size = app.config.get('PORTAL_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
        
        # Features Configuration
        self.enable_document_access = app.config.get('PORTAL_ENABLE_DOCUMENT_ACCESS', True)
        self.enable_appointment_scheduling = app.config.get('PORTAL_ENABLE_APPOINTMENT_SCHEDULING', True)
        self.enable_messaging = app.config.get('PORTAL_ENABLE_MESSAGING', True)
        self.enable_case_updates = app.config.get('PORTAL_ENABLE_CASE_UPDATES', True)
    
    def create_portal_user(self, client_id, username, email, temporary_password=None):
        """Create portal user for client"""
        try:
            from models import db, ClientPortalUser, Client
            
            client = Client.query.get(client_id)
            if not client:
                return False, "Client not found"
            
            # Check if username already exists
            existing_user = ClientPortalUser.query.filter_by(username=username).first()
            if existing_user:
                return False, "Username already exists"
            
            # Check if email already exists
            existing_email = ClientPortalUser.query.filter_by(email=email).first()
            if existing_email:
                return False, "Email already exists"
            
            # Generate temporary password if not provided
            if not temporary_password:
                temporary_password = self._generate_temporary_password()
            
            # Create portal user
            portal_user = ClientPortalUser(
                client_id=client_id,
                username=username,
                email=email,
                password_hash=generate_password_hash(temporary_password),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Enable 2FA if required
            if self.require_2fa:
                portal_user.two_factor_enabled = False
                portal_user.two_factor_secret = None
                portal_user.backup_codes = None
            
            db.session.add(portal_user)
            db.session.commit()
            
            # Send welcome email
            from email_integration import email_service
            
            portal_credentials = {
                'username': username,
                'temporary_password': temporary_password
            }
            
            email_result = email_service.send_welcome_email(client, portal_credentials)
            
            logger.info(f"Portal user created for client {client_id}: {username}")
            
            return True, portal_user
            
        except Exception as e:
            logger.error(f"Error creating portal user: {str(e)}")
            return False, f"Error creating portal user: {str(e)}"
    
    def authenticate_portal_user(self, username, password, ip_address=None, user_agent=None):
        """Authenticate portal user with enhanced security"""
        try:
            from models import db, ClientPortalUser, ActivityLog
            
            # Find user
            user = ClientPortalUser.query.filter_by(username=username).first()
            if not user:
                return False, "Invalid credentials"
            
            # Check if account is locked
            if user.is_locked():
                if user.locked_until and user.locked_until > datetime.utcnow():
                    return False, "Account locked. Please try again later."
                else:
                    # Unlock account if lock period has expired
                    user.is_locked = False
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    db.session.commit()
            
            # Check if account is active
            if not user.is_active:
                return False, "Account is deactivated"
            
            # Check IP whitelist if configured
            if self.ip_whitelist and ip_address not in self.ip_whitelist:
                return False, "Access denied from this IP address"
            
            # Verify password
            if not user.check_password(password):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account after max attempts
                if user.failed_login_attempts >= self.max_login_attempts:
                    user.is_locked = True
                    user.locked_until = datetime.utcnow() + timedelta(minutes=self.account_lockout_duration)
                    
                    # Log security event
                    activity = ActivityLog(
                        user_id=user.id,
                        action="portal_account_locked",
                        resource_type="client_portal",
                        resource_id=user.id,
                        details=f"Account locked due to {user.failed_login_attempts} failed attempts",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    db.session.add(activity)
                
                # Log failed login attempt
                activity = ActivityLog(
                    user_id=user.id,
                    action="portal_login_failed",
                    resource_type="client_portal",
                    resource_id=user.id,
                    details=f"Failed login attempt {user.failed_login_attempts}/{self.max_login_attempts}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                db.session.add(activity)
                
                db.session.commit()
                return False, "Invalid credentials"
            
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            
            # Check if 2FA is required
            if self.require_2fa and not user.two_factor_enabled:
                # Generate 2FA setup data
                setup_data, error = self._setup_2fa_for_user(user)
                if error:
                    return False, error
                
                # Save 2FA setup data temporarily
                user._2fa_setup_secret = setup_data['secret']
                user._2fa_setup_qr = setup_data['qr_code']
                user._2fa_setup_backup_codes = setup_data['backup_codes']
                
                db.session.commit()
                
                return {
                    'success': True,
                    'requires_2fa_setup': True,
                    'setup_data': setup_data
                }
            
            # Check if 2FA verification is required
            if self.require_2fa and user.two_factor_enabled:
                return {
                    'success': True,
                    'requires_2fa_verification': True
                }
            
            # Successful login
            db.session.commit()
            
            # Log successful login
            activity = ActivityLog(
                user_id=user.id,
                action="portal_login_success",
                resource_type="client_portal",
                resource_id=user.id,
                details="User logged into client portal successfully",
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(activity)
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'client_id': user.client_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating portal user: {str(e)}")
            return False, f"Error authenticating portal user: {str(e)}"
    
    def verify_2fa_token(self, user_id, token, backup_code=None):
        """Verify 2FA token or backup code"""
        try:
            from models import db, ClientPortalUser, ActivityLog
            
            user = ClientPortalUser.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Verify backup code if provided
            if backup_code:
                if user.verify_backup_code(backup_code):
                    # Mark backup code as used
                    backup_codes = user.backup_codes.split(',') if user.backup_codes else []
                    if backup_code in backup_codes:
                        backup_codes.remove(backup_code)
                        user.backup_codes = ','.join(backup_codes)
                        db.session.commit()
                    
                    # Log successful backup code verification
                    activity = ActivityLog(
                        user_id=user.id,
                        action="portal_2fa_backup_code_verified",
                        resource_type="client_portal",
                        resource_id=user.id,
                        details="User verified 2FA using backup code",
                        ip_address=request.remote_addr if 'request' in globals() else None,
                        user_agent=request.headers.get('User-Agent') if 'request' in globals() else None
                    )
                    db.session.add(activity)
                    
                    return True, "Backup code verified successfully"
                else:
                    return False, "Invalid backup code"
            
            # Verify TOTP token
            if user.two_factor_enabled and user.two_factor_secret:
                totp = pyotp.TOTP(user.two_factor_secret)
                if totp.verify(token):
                    # Log successful 2FA verification
                    activity = ActivityLog(
                        user_id=user.id,
                        action="portal_2fa_verified",
                        resource_type="client_portal",
                        resource_id=user.id,
                        details="User verified 2FA token successfully",
                        ip_address=request.remote_addr if 'request' in globals() else None,
                        user_agent=request.headers.get('User-Agent') if 'request' in globals() else None
                    )
                    db.session.add(activity)
                    
                    return True, "2FA token verified successfully"
                else:
                    return False, "Invalid 2FA token"
            
            return False, "2FA verification failed"
            
        except Exception as e:
            logger.error(f"Error verifying 2FA token: {str(e)}")
            return False, f"Error verifying 2FA token: {str(e)}"
    
    def setup_2fa_for_user(self, user_id):
        """Setup 2FA for user"""
        try:
            from models import db, ClientPortalUser
            
            user = ClientPortalUser.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Generate secret key
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = []
            for _ in range(10):
                code = ''.join([str(pyotp.random_base32().replace('=', ''))[:5] for _ in range(3)])
                backup_codes.append(code)
            
            # Save 2FA settings
            user.two_factor_secret = secret
            user.backup_codes = ','.join(backup_codes)
            user.two_factor_enabled = False  # Will be enabled after user verification
            db.session.commit()
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name=f"{self.portal_name} - {user.email.split('@')[0]}",
                algorithm='SHA1',
                digits=6,
                period=30
            )
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'secret': secret,
                'qr_code': f"data:image/png;base64,{qr_code_data}",
                'backup_codes': backup_codes,
                'totp_uri': totp_uri,
                'manual_entry_key': secret
            }
            
        except Exception as e:
            logger.error(f"Error setting up 2FA for user: {str(e)}")
            return False, f"Error setting up 2FA: {str(e)}"
    
    def enable_2fa_for_user(self, user_id, token):
        """Enable 2FA for user after token verification"""
        try:
            from models import db, ClientPortalUser, ActivityLog
            
            user = ClientPortalUser.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Verify token
            if user.two_factor_secret:
                totp = pyotp.TOTP(user.two_factor_secret)
                if not totp.verify(token):
                    return False, "Invalid token"
            
            # Enable 2FA
            user.two_factor_enabled = True
            db.session.commit()
            
            # Log 2FA enabling
            activity = ActivityLog(
                user_id=user.id,
                action="portal_2fa_enabled",
                resource_type="client_portal",
                resource_id=user.id,
                details="User enabled 2FA successfully",
                ip_address=request.remote_addr if 'request' in globals() else None,
                user_agent=request.headers.get('User-Agent') if 'request' in globals() else None
            )
            db.session.add(activity)
            
            return True, "2FA enabled successfully"
            
        except Exception as e:
            logger.error(f"Error enabling 2FA for user: {str(e)}")
            return False, f"Error enabling 2FA: {str(e)}"
    
    def disable_2fa_for_user(self, user_id, password):
        """Disable 2FA for user"""
        try:
            from models import db, ClientPortalUser, ActivityLog
            
            user = ClientPortalUser.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Verify password
            if not user.check_password(password):
                return False, "Invalid password"
            
            # Disable 2FA
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.backup_codes = None
            db.session.commit()
            
            # Log 2FA disabling
            activity = ActivityLog(
                user_id=user.id,
                action="portal_2fa_disabled",
                resource_type="client_portal",
                resource_id=user.id,
                details="User disabled 2FA",
                ip_address=request.remote_addr if 'request' in globals() else None,
                user_agent=request.headers.get('User-Agent') if 'request' in globals() else None
            )
            db.session.add(activity)
            
            return True, "2FA disabled successfully"
            
        except Exception as e:
            logger.error(f"Error disabling 2FA for user: {str(e)}")
            return False, f"Error disabling 2FA: {str(e)}"
    
    def regenerate_backup_codes(self, user_id):
        """Regenerate backup codes for user"""
        try:
            from models import db, ClientPortalUser
            
            user = ClientPortalUser.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Generate new backup codes
            backup_codes = []
            for _ in range(10):
                code = ''.join([str(pyotp.random_base32().replace('=', ''))[:5] for _ in range(3)])
                backup_codes.append(code)
            
            # Save backup codes
            user.backup_codes = ','.join(backup_codes)
            db.session.commit()
            
            return True, "Backup codes regenerated successfully"
            
        except Exception as e:
            logger.error(f"Error regenerating backup codes: {str(e)}")
            return False, f"Error regenerating backup codes: {str(e)}"
    
    def get_client_documents(self, client_id, user_id=None):
        """Get documents accessible to client"""
        try:
            from models import db, Document, Client, ClientPortalUser
            
            client = Client.query.get(client_id)
            if not client:
                return []
            
            # Get portal user
            portal_user = None
            if user_id:
                portal_user = ClientPortalUser.query.get(user_id)
                if portal_user and portal_user.client_id != client_id:
                    return []
            
            # Get documents for this client
            documents = Document.query.filter_by(client_id=client_id).all()
            
            # Filter documents based on permissions
            accessible_documents = []
            for doc in documents:
                # If document is not confidential, it's accessible
                if not doc.is_confidential:
                    accessible_documents.append(doc)
                # If user is logged in and has access, include confidential documents
                elif portal_user and self._check_document_access(portal_user, doc):
                    accessible_documents.append(doc)
            
            return accessible_documents
            
        except Exception as e:
            logger.error(f"Error getting client documents: {str(e)}")
            return []
    
    def _check_document_access(self, user, document):
        """Check if user has access to document"""
        try:
            # Check if user is the assigned lawyer or has permission
            if user.role in ['admin', 'lawyer']:
                return True
            
            # Check if user is the client who owns the document
            if user.client_id == document.client_id:
                return True
            
            # Additional access checks can be added here
            return False
            
        except Exception as e:
            logger.error(f"Error checking document access: {str(e)}")
            return False
    
    def get_client_cases(self, client_id, user_id=None):
        """Get cases accessible to client"""
        try:
            from models import db, Case, Client, ClientPortalUser
            
            client = Client.query.get(client_id)
            if not client:
                return []
            
            # Get portal user
            portal_user = None
            if user_id:
                portal_user = ClientPortalUser.query.get(user_id)
                if portal_user and portal_user.client_id != client_id:
                    return []
            
            # Get cases for this client
            cases = Case.query.filter_by(client_id=client_id).all()
            
            # Filter cases based on permissions
            accessible_cases = []
            for case in cases:
                # If case is not confidential, it's accessible
                if case.status != 'confidential':
                    accessible_cases.append(case)
                # If user is logged in and has access, include confidential cases
                elif portal_user and self._check_case_access(portal_user, case):
                    accessible_cases.append(case)
            
            return accessible_cases
            
        except Exception as e:
            logger.error(f"Error getting client cases: {str(e)}")
            return []
    
    def _check_case_access(self, user, case):
        """Check if user has access to case"""
        try:
            # Check if user is the assigned lawyer or has permission
            if user.role in ['admin', 'lawyer']:
                return True
            
            # Check if user is the client who owns the case
            if user.client_id == case.client_id:
                return True
            
            # Additional access checks can be added here
            return False
            
        except Exception as e:
            logger.error(f"Error checking case access: {str(e)}")
            return False
    
    def get_client_appointments(self, client_id, user_id=None):
        """Get appointments for client"""
        try:
            from models import db, Appointment, Client, ClientPortalUser
            
            client = Client.query.get(client_id)
            if not client:
                return []
            
            # Get portal user
            portal_user = None
            if user_id:
                portal_user = ClientPortalUser.query.get(user_id)
                if portal_user and portal_user.client_id != client_id:
                    return []
            
            # Get appointments for this client
            appointments = Appointment.query.filter_by(client_id=client_id).all()
            
            # Filter appointments based on permissions
            accessible_appointments = []
            for appointment in appointments:
                # Include appointments that are not confidential
                if appointment.status != 'confidential':
                    accessible_appointments.append(appointment)
                # If user is logged in and has access, include confidential appointments
                elif portal_user and self._check_appointment_access(portal_user, appointment):
                    accessible_appointments.append(appointment)
            
            return accessible_appointments
            
        except Exception as e:
            logger.error(f"Error getting client appointments: {str(e)}")
            return []
    
    def _check_appointment_access(self, user, appointment):
        """Check if user has access to appointment"""
        try:
            # Check if user is the assigned lawyer or has permission
            if user.role in ['admin', 'lawyer']:
                return True
            
            # Check if user is the client who owns the appointment
            if user.client_id == appointment.client_id:
                return True
            
            # Additional access checks can be added here
            return False
            
        except Exception as e:
            logger.error(f"Error checking appointment access: {str(e)}")
            return False
    
    def send_portal_message(self, sender_id, recipient_id, message, message_type='general'):
        """Send message from client to lawyer or vice versa"""
        try:
            from models import db, ClientPortalUser, Message, ActivityLog
            
            sender = ClientPortalUser.query.get(sender_id)
            recipient = ClientPortalUser.query.get(recipient_id)
            
            if not sender or not recipient:
                return False, "Invalid sender or recipient"
            
            # Check if sender and recipient are from the same client
            if sender.client_id != recipient.client_id:
                return False, "Cannot send message to different clients"
            
            # Check if sender has permission to recipient
            if not self._check_messaging_permission(sender, recipient):
                return False, "Permission denied"
            
            # Create message
            msg = Message(
                sender_id=sender.id,
                recipient_id=recipient.id,
                message=message,
                message_type=message_type,
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(msg)
            db.session.commit()
            
            # Send notification
            if message_type == 'urgent':
                from email_integration import email_service
                from models import User
                
                # Notify recipient's assigned lawyer
                lawyer = User.query.filter_by(id=recipient.client.assigned_lawyer_id).first()
                if lawyer:
                    client = Client.query.get(recipient.client_id)
                    
                    email_result = email_service.send_email(
                        to_email=lawyer.email,
                        subject=f"Urgent Message from {client.full_name}",
                        html_body=f"""
                        <h2>Urgent Message from Client Portal</h2>
                        <p><strong>Client:</strong> {client.full_name}</p>
                        <p><strong>Message:</strong> {message}</p>
                        <p><strong>Sent:</strong> {sender.full_name}</p>
                        <p><strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}</p>
                        """,
                        text_body=f"""
                        Urgent Message from Client Portal
                        
                        Client: {client.full_name}
                        Message: {message}
                        Sent: {sender.full_name}
                        Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
                        """,
                        recipient=lawyer.email
                    )
            
            # Log message activity
            activity = ActivityLog(
                user_id=sender.id,
                action="portal_message_sent",
                resource_type="client_portal",
                resource_id=msg.id,
                details=f"Message sent from {sender.username} to {recipient.username}",
                ip_address=request.remote_addr if 'request' in globals() else None,
                user_agent=request.headers.get('User-Agent') if 'request' in globals() else None
            )
            db.session.add(activity)
            db.session.commit()
            
            return True, msg
            
        except Exception as e:
            logger.error(f"Error sending portal message: {str(e)}")
            return False, f"Error sending portal message: {str(e)}"
    
    def _generate_temporary_password(self):
        """Generate secure temporary password"""
        import random
        import string
        
        length = 12
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for i in range(length))
        
        return password
    
    def _check_messaging_permission(self, sender, recipient):
        """Check if sender has permission to send message to recipient"""
        try:
            # Clients can send messages to their assigned lawyer
            if sender.role == 'client' and recipient.role == 'client':
                return False  # Clients cannot message other clients directly
            
            if sender.role == 'client' and recipient.role == 'lawyer':
                # Check if recipient is assigned lawyer for sender's client
                if recipient.client_id == sender.client_id:
                    # Lawyer may be assigned via client.assigned_lawyer_id or firm settings
                    if (hasattr(recipient, 'client_id') and recipient.client_id == sender.client_id) or \
                       (hasattr(sender, 'client') and sender.client.assigned_lawyer_id and 
                        sender.client.assigned_lawyer_id == recipient.id) or \
                       (hasattr(sender.client, 'firm') and sender.client.firm.assigned_lawyer and 
                        sender.client.firm.assigned_lawyer.id == recipient.id):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking messaging permission: {str(e)}")
            return False
    
    def get_portal_messages(self, user_id, message_type=None, limit=50):
        """Get messages for user in portal"""
        try:
            from models import Message
            
            query = Message.query.filter(
                (Message.sender_id == user_id) | (Message.recipient_id == user_id)
            )
            
            if message_type:
                query = query.filter_by(message_type=message_type)
            
            query = query.order_by(Message.created_at.desc()).limit(limit)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error getting portal messages: {str(e)}")
            return []
    
    def mark_message_read(self, message_id, user_id):
        """Mark message as read"""
        try:
            from models import db, Message
            
            message = Message.query.get(message_id)
            if not message:
                return False, "Message not found"
            
            # Only recipient can mark message as read
            if message.recipient_id == user_id:
                message.is_read = True
                message.read_at = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
    
    def schedule_appointment_in_portal(self, appointment_id, client_id, requested_time, notes=None):
        """Schedule appointment request from client portal"""
        try:
            from models import db, Appointment, Client, ClientPortalUser, ActivityLog
            
            client = Client.query.get(client_id)
            portal_user = ClientPortalUser.query.filter_by(client_id=client_id).first()
            
            if not client or not portal_user:
                return False, "Client or portal user not found"
            
            # Create appointment request record
            from models import AppointmentRequest
            appointment_request = AppointmentRequest(
                client_id=client_id,
                portal_user_id=portal_user.id,
                appointment_id=appointment_id,  # If rescheduling existing appointment
                requested_time=requested_time,
                notes=notes,
                status='pending',
                created_at=datetime.utcnow()
            )
            
            db.session.add(appointment_request)
            db.session.commit()
            
            # Notify assigned lawyer
            lawyer = User.query.filter_by(id=client.assigned_lawyer_id).first()
            if lawyer:
                from email_integration import email_service
                
                email_result = email_service.send_email(
                    to_email=lawyer.email,
                    subject=f"New Appointment Request from {client.full_name}",
                    html_body=f"""
                    <h2>New Appointment Request</h2>
                    <p><strong>Client:</strong> {client.full_name}</p>
                    <p><strong>Requested Time:</strong> {requested_time}</p>
                    <p><strong>Notes:</strong> {notes}</p>
                    <p><strong>Status:</strong> Pending Review</p>
                    """,
                    text_body=f"""
                    New Appointment Request from {client.full_name}
                    
                    Requested Time: {requested_time}
                    Notes: {notes}
                    Status: Pending Review
                    """,
                    recipient=lawyer.email
                )
            
            # Log appointment request
            activity = ActivityLog(
                user_id=portal_user.id,
                action="portal_appointment_requested",
                resource_type="client_portal",
                resource_id=appointment_request.id,
                details=f"Client {client.full_name} requested appointment",
                ip_address=request.remote_addr if 'request' in globals() else None,
                user_agent=request.headers.get('User-Agent') if 'request' in globals() else None
            )
            db.session.add(activity)
            db.session.commit()
            
            return True, "Appointment request submitted successfully"
            
        except Exception as e:
            logger.error(f"Error scheduling appointment in portal: {str(e)}")
            return False, f"Error scheduling appointment: {str(e)}"
    
    def get_portal_analytics(self, client_id=None):
        """Get portal analytics"""
        try:
            from models import db, ClientPortalUser, ActivityLog
            
            # Base query
            query = ActivityLog.query.filter(
                ActivityLog.resource_type == 'client_portal'
            )
            
            # Filter by client if specified
            if client_id:
                users = ClientPortalUser.query.filter_by(client_id=client_id).all()
                user_ids = [user.id for user in users]
                query = query.filter(ActivityLog.user_id.in_(user_ids))
            
            # Get analytics data
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            analytics = {
                'total_logins': query.filter(ActivityLog.action.like('%login_success%')).count(),
                'logins_today': query.filter(
                    ActivityLog.action.like('%login_success%'),
                    db.func.date(ActivityLog.timestamp) == today
                ).count(),
                'logins_this_week': query.filter(
                    ActivityLog.action.like('%login_success%'),
                    db.func.date(ActivityLog.timestamp) >= week_ago
                ).count(),
                'logins_this_month': query.filter(
                    ActivityLog.action.like('%login_success%'),
                    db.func.date(ActivityLog.timestamp) >= month_ago
                ).count(),
                'failed_logins': query.filter(ActivityLog.action.like('%login_failed%')).count(),
                'active_users': ClientPortalUser.query.filter_by(is_active=True).count(),
                'users_with_2fa': ClientPortalUser.query.filter_by(two_factor_enabled=True).count(),
                'messages_sent': query.filter(ActivityLog.action.like('%message_sent%')).count(),
                'documents_accessed': query.filter(ActivityLog.action.like('%document_%')).count()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting portal analytics: {str(e)}")
            return {}
    
    def cleanup_expired_sessions(self):
        """Clean up expired portal sessions"""
        try:
            from models import db, ClientPortalUser
            
            # Find users with expired sessions
            expired_time = datetime.utcnow() - timedelta(hours=self.session_timeout)
            expired_users = ClientPortalUser.query.filter(
                ClientPortalUser.last_login < expired_time
            ).all()
            
            # Log them out (in a real implementation, you might invalidate their session tokens)
            for user in expired_users:
                logger.info(f"Session expired for user {user.username}")
            
            return len(expired_users)
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0

# Initialize client portal
client_portal = ClientPortal()
