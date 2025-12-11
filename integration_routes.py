"""
Integration Routes for Email, Calendar, and Payment Services
Provides API endpoints for integrating external services
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps
from models import db, User, Appointment, Invoice, Payment
from email_integration import email_service
from calendar_integration import calendar_service
from payment_integration import payment_gateway
from datetime import datetime, timedelta
import logging

# Create blueprints
integration_bp = Blueprint('integration', __name__)

# Configure logging
logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function

# Email Integration Routes
@integration_bp.route('/email/send_test', methods=['POST'])
@login_required
def send_test_email():
    """Send test email"""
    try:
        data = request.get_json()
        to_email = data.get('to_email')
        subject = data.get('subject', 'Test Email from LawEdge')
        message = data.get('message', 'This is a test email from LawEdge Legal Services.')
        
        if not to_email:
            return jsonify({'success': False, 'message': 'Email address is required'})
        
        result = email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_body=f"<p>{message}</p>",
            text_body=message
        )
        
        if result[0]:
            return jsonify({'success': True, 'message': result[1]})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending test email: {str(e)}'})

@integration_bp.route('/email/send_appointment_reminder/<int:appointment_id>', methods=['POST'])
@login_required
def send_appointment_reminder(appointment_id):
    """Send appointment reminder"""
    try:
        from models import Appointment, Client, User
        
        appointment = Appointment.query.get_or_404(appointment_id)
        client = Client.query.get(appointment.client_id)
        lawyer = User.query.get(appointment.lawyer_id)
        
        if not client or not lawyer:
            return jsonify({'success': False, 'message': 'Appointment not found'})
        
        result = email_service.send_appointment_reminder(appointment, client, lawyer)
        
        if result[0]:
            return jsonify({'success': True, 'message': result[1]})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error sending appointment reminder: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending appointment reminder: {str(e)}'})

@integration_bp.route('/email/send_case_update/<int:case_id>', methods=['POST'])
@login_required
def send_case_update(case_id):
    """Send case update notification"""
    try:
        from models import Case, Client, User
        
        case = Case.query.get_or_404(case_id)
        client = Client.query.get(case.client_id)
        lawyer = User.query.get(case.assigned_lawyer_id)
        
        data = request.get_json()
        update_type = data.get('update_type', 'Status Update')
        details = data.get('details', 'Case status has been updated.')
        
        if not client or not lawyer:
            return jsonify({'success': False, 'message': 'Case not found'})
        
        result = email_service.send_case_update_notification(case, update_type, details)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Case update notification sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send case update'})
            
    except Exception as e:
        logger.error(f"Error sending case update: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending case update: {str(e)}'})

@integration_bp.route('/email/send_invoice/<int:invoice_id>', methods=['POST'])
@login_required
def send_invoice(invoice_id):
    """Send invoice notification"""
    try:
        from models import Invoice, Client
        
        invoice = Invoice.query.get_or_404(invoice_id)
        client = Client.query.get(invoice.client_id)
        
        if not client:
            return jsonify({'success': False, 'message': 'Invoice not found'})
        
        result = email_service.send_invoice_notification(invoice, client)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Invoice notification sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send invoice notification'})
            
    except Exception as e:
        logger.error(f"Error sending invoice: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending invoice: {str(e)}'})

@integration_bp.route('/email/send_welcome/<int:client_id>', methods=['POST'])
@login_required
def send_welcome_email(client_id):
    """Send welcome email to new client"""
    try:
        from models import Client, ClientPortalUser
        
        client = Client.query.get_or_404(client_id)
        portal_user = ClientPortalUser.query.filter_by(client_id=client_id).first()
        
        if not portal_user:
            return jsonify({'success': False, 'message': 'Portal user not found'})
        
        portal_credentials = {
            'username': portal_user.username,
            'temporary_password': 'temp123456'  # Generate secure password
        }
        
        result = email_service.send_welcome_email(client, portal_credentials)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Welcome email sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send welcome email'})
            
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending welcome email: {str(e)}'})

# Calendar Integration Routes
@integration_bp.route('/calendar/sync_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def sync_appointment_to_calendar(appointment_id):
    """Sync appointment to calendar"""
    try:
        from models import Appointment
        
        appointment = Appointment.query.get_or_404(appointment_id)
        provider = request.form.get('provider', 'google')
        
        result = calendar_service.sync_appointment_to_calendar(appointment, provider)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Appointment synced to calendar'})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error syncing appointment to calendar: {str(e)}")
        return jsonify({'success': False, 'message': f'Error syncing appointment: {str(e)}'})

@integration_bp.route('/calendar/schedule_reminder/<int:appointment_id>', methods=['POST'])
@login_required
def schedule_appointment_reminder(appointment_id):
    """Schedule reminder for appointment"""
    try:
        from models import Appointment
        
        appointment = Appointment.query.get_or_404(appointment_id)
        
        result = calendar_service.schedule_reminder_for_appointment(appointment)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Reminder scheduled'})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error scheduling appointment reminder: {str(e)}")
        return jsonify({'success': False, 'message': f'Error scheduling reminder: {str(e)}'})

@integration_bp.route('/calendar/create_event', methods=['POST'])
@login_required
def create_calendar_event():
    """Create calendar event"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'google')
        
        event_data = {
            'title': data.get('title'),
            'description': data.get('description', ''),
            'start_time': datetime.fromisoformat(data.get('start_time')),
            'end_time': datetime.fromisoformat(data.get('end_time')),
            'location': data.get('location', ''),
            'attendees': data.get('attendees', []),
            'reminder_minutes': data.get('reminder_minutes', 30)
        }
        
        if provider == 'google':
            result = calendar_service.create_google_calendar_event(event_data)
        elif provider == 'exchange':
            result = calendar_service.create_exchange_calendar_event(event_data)
        else:
            result = calendar_service.create_google_calendar_event(event_data)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Event created successfully'})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating calendar event: {str(e)}'})

@integration_bp.route('/calendar/delete_event/<string:event_id>', methods=['DELETE'])
@login_required
def delete_calendar_event(event_id, provider='google'):
    """Delete calendar event"""
    try:
        if provider == 'google':
            result = calendar_service.delete_google_calendar_event(event_id)
        elif provider == 'exchange':
            result = calendar_service.delete_exchange_calendar_event(event_id)
        else:
            result = calendar_service.delete_google_calendar_event(event_id)
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Event deleted successfully'})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error deleting calendar event: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting calendar event: {str(e)}'})

# Payment Integration Routes
@integration_bp.route('/payment/create_order/<int:invoice_id>', methods=['POST'])
@login_required
def create_payment_order(invoice_id):
    """Create payment order for invoice"""
    try:
        from models import Invoice, Client
        
        invoice = Invoice.query.get_or_404(invoice_id)
        client = Client.query.get(invoice.client_id)
        
        payment_method = request.form.get('payment_method', 'razorpay')
        customer_info = {
            'name': client.full_name,
            'email': client.email,
            'contact': client.phone or ''
        }
        
        result = payment_gateway.process_invoice_payment(
            invoice, 
            payment_method, 
            customer_info
        )
        
        if result[0]:
            return jsonify({'success': True, 'data': result[1]})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error creating payment order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating payment order: {str(e)}'})

@integration_bp.route('/payment/capture/<string:payment_id>', methods=['POST'])
@login_required
def capture_payment(payment_id):
    """Capture payment"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'razorpay')
        amount = data.get('amount')
        
        if provider == 'razorpay':
            result = payment_gateway.capture_razorpay_payment(payment_id, amount)
        else:
            return jsonify({'success': False, 'message': 'Unsupported provider'})
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Payment captured successfully'})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error capturing payment: {str(e)}")
        return jsonify({'success': False, 'message': f'Error capturing payment: {str(e)}'})

@integration_bp.route('/payment/webhook/<string:provider>', methods=['POST'])
def payment_webhook(provider):
    """Process payment webhook"""
    try:
        # Get webhook signature
        signature = request.headers.get('X-Webhook-Signature')
        payload = request.get_json() if request.is_json else request.get_data(as_text=True)
        
        # Verify signature
        if signature and payload:
            verification_result = payment_gateway.verify_webhook_signature(
                payload, 
                signature, 
                provider
            )
            
            if not verification_result:
                logger.error(f"Webhook signature verification failed for {provider}")
                return jsonify({'error': 'Invalid signature'}), 401
        
        # Process webhook
        result = payment_gateway.process_payment_webhook(payload, provider)
        
        if result[0]:
            return jsonify({'success': True, 'data': result[1]})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error processing payment webhook: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing webhook: {str(e)}'})

@integration_bp.route('/payment/status/<string:payment_id>/<string:provider>')
@login_required
def get_payment_status(payment_id, provider):
    """Get payment status"""
    try:
        result = payment_gateway.get_payment_status(payment_id, provider)
        
        if result[0]:
            return jsonify({'success': True, 'data': result[1]})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return jsonify({'success': False, 'message': f'Error getting payment status: {str(e)}'})

# Integration Settings Routes
@integration_bp.route('/integration/settings')
@login_required
def integration_settings():
    """Integration settings page"""
    try:
        user = User.query.get(session['user_id'])
        
        if user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect('/dashboard')
        
        # Get current integration status
        email_config = {
            'smtp_configured': bool(current_app.config.get('SMTP_USERNAME')),
            'sendgrid_configured': bool(current_app.config.get('SENDGRID_API_KEY')),
            'aws_ses_configured': bool(current_app.config.get('AWS_ACCESS_KEY'))
        }
        
        calendar_config = {
            'google_configured': bool(current_app.config.get('GOOGLE_CLIENT_SECRETS')),
            'exchange_configured': bool(current_app.config.get('EXCHANGE_CLIENT_ID'))
        }
        
        payment_config = {
            'razorpay_configured': bool(current_app.config.get('RAZORPAY_KEY_ID')),
            'stripe_configured': bool(current_app.config.get('STRIPE_PUBLISHABLE_KEY')),
            'paypal_configured': bool(current_app.config.get('PAYPAL_CLIENT_ID'))
        }
        
        return render_template('integration_settings.html',
                             email_config=email_config,
                             calendar_config=calendar_config,
                             payment_config=payment_config)
        
    except Exception as e:
        logger.error(f"Error loading integration settings: {str(e)}")
        return render_template('error.html', error=str(e))

@integration_bp.route('/integration/test_email', methods=['POST'])
@login_required
def test_email_integration():
    """Test email integration"""
    try:
        data = request.get_json()
        service = data.get('service')
        to_email = data.get('to_email')
        
        if not to_email:
            return jsonify({'success': False, 'message': 'Email address is required'})
        
        # Create test email content
        subject = f"Email Integration Test - {service.upper()}"
        html_body = f"""
        <h2>Email Integration Test</h2>
        <p>This is a test email from LawEdge Legal Services.</p>
        <p><strong>Service:</strong> {service.upper()}</p>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Status:</strong> Integration Successful</p>
        """
        
        text_body = f"""
        Email Integration Test - {service.upper()}
        
        Service: {service.upper()}
        Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        Status: Integration Successful
        """
        
        result = email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            provider=service
        )
        
        if result[0]:
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error testing email integration: {str(e)}")
        return jsonify({'success': False, 'message': f'Error testing email integration: {str(e)}'})

@integration_bp.route('/integration/test_payment', methods=['POST'])
@login_required
def test_payment_integration():
    """Test payment integration"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'razorpay')
        amount = float(data.get('amount', 1.0))
        
        # Create test order
        result = payment_gateway.create_razorpay_order(
            amount=amount,
            currency='INR',
            receipt=f"TEST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            notes={
                'test_order': True,
                'provider': provider
            }
        )
        
        if result[0]:
            return jsonify({
                'success': True, 
                'message': 'Test order created successfully',
                'order_id': result[1]['id'],
                'amount': amount
            })
        else:
            return jsonify({'success': False, 'message': result[1]})
            
    except Exception as e:
        logger.error(f"Error testing payment integration: {str(e)}")
        return jsonify({'success': False, 'message': f'Error testing payment integration: {str(e)}'})

# Integration Dashboard
@integration_bp.route('/integration/dashboard')
@login_required
def integration_dashboard():
    """Integration dashboard"""
    try:
        user = User.query.get(session['user_id'])
        
        if user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect('/dashboard')
        
        # Get integration statistics
        from models import Payment, ActivityLog
        
        # Payment statistics
        total_payments = Payment.query.count()
        paid_payments = Payment.query.filter_by(status='paid').count()
        failed_payments = Payment.query.filter_by(status='failed').count()
        
        # Recent activity
        recent_activities = ActivityLog.query.filter(
            ActivityLog.action.like('%sync_%')
        ).order_by(ActivityLog.timestamp.desc()).limit(10).all()
        
        # Email statistics (mock for now)
        email_stats = {
            'sent_today': 12,
            'sent_this_week': 45,
            'sent_this_month': 180,
            'success_rate': 95.2
        }
        
        # Calendar statistics (mock for now)
        calendar_stats = {
            'events_today': 8,
            'events_this_week': 22,
            'events_this_month': 85,
            ' synced_appointments': 15
        }
        
        return render_template('integration_dashboard.html',
                             total_payments=total_payments,
                             paid_payments=paid_payments,
                             failed_payments=failed_payments,
                             email_stats=email_stats,
                             calendar_stats=calendar_stats,
                             recent_activities=recent_activities)
        
    except Exception as e:
        logger.error(f"Error loading integration dashboard: {str(e)}")
        return render_template('error.html', error=str(e))

# API endpoints for external integrations
@integration_bp.route('/api/v1/email/templates')
@login_required
def get_email_templates():
    """Get available email templates"""
    try:
        templates = list(email_service.templates.keys())
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        logger.error(f"Error getting email templates: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@integration_bp.route('/api/v1/calendar/events')
@login_required
def get_calendar_events():
    """Get calendar events"""
    try:
        # Mock data for now - in real implementation, this would fetch from calendar service
        events = [
            {
                'id': 'cal_001',
                'title': 'Client Meeting',
                'start': '2024-01-15T10:00:00Z',
                'end': '2024-01-15T11:00:00Z',
                'provider': 'google'
            },
            {
                'id': 'cal_002',
                'title': 'Court Hearing',
                'start': '2024-01-16T14:00:00Z',
                'end': '2024-01-16T16:00:00Z',
                'provider': 'google'
            }
        ]
        
        return jsonify({
            'success': True,
            'events': events
        })
        
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@integration_bp.route('/api/v1/payments/recent')
@login_required
def get_recent_payments():
    """Get recent payments"""
    try:
        from models import Payment
        
        payments = Payment.query.order_by(Payment.payment_date.desc()).limit(10).all()
        
        payment_list = []
        for payment in payments:
            payment_list.append({
                'id': payment.id,
                'amount': payment.amount,
                'currency': payment.currency,
                'method': payment.payment_method,
                'status': payment.status,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'invoice_id': payment.invoice_id,
                'transaction_id': payment.transaction_id
            })
        
        return jsonify({
            'success': True,
            'payments': payment_list
        })
        
    except Exception as e:
        logger.error(f"Error getting recent payments: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
