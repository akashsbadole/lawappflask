"""
Email Integration Module
Implements email sending, receiving, and integration with popular email services
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.utils import formataddr
from email.header import Header
import logging
from datetime import datetime, timedelta
import json
import re
from flask import current_app

# Try to import email service libraries
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_SES_AVAILABLE = True
except ImportError:
    AWS_SES_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class EmailService:
    """Email service integration with multiple providers"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        # SMTP Configuration
        self.smtp_server = app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = app.config.get('SMTP_PORT', 587)
        self.smtp_username = app.config.get('SMTP_USERNAME')
        self.smtp_password = app.config.get('SMTP_PASSWORD')
        self.smtp_use_tls = app.config.get('SMTP_USE_TLS', True)
        
        # SendGrid Configuration
        self.sendgrid_api_key = app.config.get('SENDGRID_API_KEY')
        self.sendgrid_from_email = app.config.get('SENDGRID_FROM_EMAIL')
        
        # AWS SES Configuration
        self.aws_access_key = app.config.get('AWS_ACCESS_KEY')
        self.aws_secret_key = app.config.get('AWS_SECRET_KEY')
        self.aws_region = app.config.get('AWS_REGION', 'us-east-1')
        
        # Email Templates
        self.templates = {
            'appointment_reminder': {
                'subject': 'Appointment Reminder - {appointment_title}',
                'html': self._get_appointment_reminder_template(),
                'text': self._get_appointment_reminder_text_template()
            },
            'case_update': {
                'subject': 'Case Update - {case_title}',
                'html': self._get_case_update_template(),
                'text': self._get_case_update_text_template()
            },
            'invoice_notification': {
                'subject': 'Invoice {invoice_number} - {amount_due}',
                'html': self._get_invoice_template(),
                'text': self._get_invoice_text_template()
            },
            'welcome_email': {
                'subject': 'Welcome to LawEdge - {client_name}',
                'html': self._get_welcome_template(),
                'text': self._get_welcome_text_template()
            },
            'document_shared': {
                'subject': 'Document Shared - {document_title}',
                'html': self._get_document_shared_template(),
                'text': self._get_document_shared_text_template()
            }
        }
    
    def send_email(self, to_email, subject, html_body=None, text_body=None, 
                   from_email=None, attachments=None, template_name=None, 
                   template_data=None, provider='auto'):
        """
        Send email using specified provider or auto-select best available
        """
        try:
            # Use template if specified
            if template_name and template_data:
                if template_name in self.templates:
                    template = self.templates[template_name]
                    subject = template['subject'].format(**template_data)
                    html_body = template['html'].format(**template_data)
                    text_body = template['text'].format(**template_data)
            
            # Set default from email
            if not from_email:
                from_email = self.sendgrid_from_email or self.smtp_username
            
            # Choose provider
            if provider == 'auto':
                provider = self._choose_best_provider()
            
            # Send email using chosen provider
            if provider == 'sendgrid' and SENDGRID_AVAILABLE:
                return self._send_sendgrid_email(to_email, subject, html_body, text_body, from_email, attachments)
            elif provider == 'aws_ses' and AWS_SES_AVAILABLE:
                return self._send_aws_ses_email(to_email, subject, html_body, text_body, from_email, attachments)
            elif provider == 'smtp':
                return self._send_smtp_email(to_email, subject, html_body, text_body, from_email, attachments)
            else:
                logger.error(f"Email provider {provider} not available")
                return False, f"Email provider {provider} not available"
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False, f"Error sending email: {str(e)}"
        
        return True, "Email sent successfully"
    
    def _choose_best_provider(self):
        """Choose the best available email provider"""
        # Priority order: SendGrid > AWS SES > SMTP
        if SENDGRID_AVAILABLE and self.sendgrid_api_key:
            return 'sendgrid'
        elif AWS_SES_AVAILABLE and self.aws_access_key:
            return 'aws_ses'
        elif self.smtp_username and self.smtp_password:
            return 'smtp'
        else:
            logger.warning("No email provider configured")
            return 'smtp'
    
    def _send_smtp_email(self, to_email, subject, html_body=None, text_body=None, 
                          from_email=None, attachments=None):
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((from_email.split('<')[0] if '<' in from_email else from_email, 
                                           from_email.split('<')[1].replace('>', '') if '<' in from_email else from_email))
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(
                        attachment['content'],
                        attachment['filename'],
                        Name=attachment['filename']
                    )
                    part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                    msg.attach(part)
            
            # Create SMTP connection
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, context=context)
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"SMTP email sent successfully to {to_email}")
            return True, "SMTP email sent successfully"
            
        except Exception as e:
            logger.error(f"Error sending SMTP email: {str(e)}")
            return False, f"Error sending SMTP email: {str(e)}"
    
    def _send_sendgrid_email(self, to_email, subject, html_body=None, text_body=None, 
                             from_email=None, attachments=None):
        """Send email using SendGrid API"""
        try:
            if not self.sendgrid_api_key:
                return False, "SendGrid API key not configured"
            
            message = Mail(
                from_email=from_email or self.sendgrid_from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_body,
                plain_content=text_body
            )
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    message.attachment(attachment['content'], 
                                     attachment['filename'],
                                     disposition='attachment')
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                logger.info(f"SendGrid email sent successfully to {to_email}")
                return True, "SendGrid email sent successfully"
            else:
                logger.error(f"SendGrid API error: {response.body}")
                return False, f"SendGrid API error: {response.body}"
                
        except Exception as e:
            logger.error(f"Error sending SendGrid email: {str(e)}")
            return False, f"Error sending SendGrid email: {str(e)}"
    
    def _send_aws_ses_email(self, to_email, subject, html_body=None, text_body=None, 
                          from_email=None, attachments=None):
        """Send email using AWS SES"""
        try:
            if not self.aws_access_key or not self.aws_secret_key:
                return False, "AWS credentials not configured"
            
            # Create SES client
            ses_client = boto3.client('ses', self.aws_region,
                                      aws_access_key_id=self.aws_access_key,
                                      aws_secret_access_key=self.aws_secret_key)
            
            # Build email message
            message = {
                'Source': from_email or self.smtp_username,
                'Destination': {
                    'ToAddresses': [{'EmailAddress': to_email}]
                },
                'Message': {
                    'Subject': subject,
                    'Body': {
                        'Text': text_body or '',
                        'Html': html_body or ''
                    }
                }
            }
            
            # Add attachments
            if attachments:
                message['Message']['Attachments'] = []
                for attachment in attachments:
                    message['Message']['Attachments'].append({
                        'Filename': attachment['filename'],
                        'Content': attachment['content']
                    })
            
            # Send email
            response = ses_client.send_email(Message=message)
            
            if response['MessageId']:
                logger.info(f"AWS SES email sent successfully to {to_email}")
                return True, "AWS SES email sent successfully"
            else:
                logger.error(f"AWS SES error: {response}")
                return False, f"AWS SES error: {response}"
                
        except Exception as e:
            logger.error(f"Error sending AWS SES email: {str(e)}")
            return False, f"Error sending AWS SES email: {str(e)}"
    
    def send_appointment_reminder(self, appointment, client, lawyer):
        """Send appointment reminder email"""
        template_data = {
            'appointment_title': appointment.title,
            'client_name': client.full_name,
            'lawyer_name': lawyer.full_name,
            'appointment_date': appointment.start_time.strftime('%Y-%m-%d %H:%M'),
            'appointment_location': appointment.location,
            'appointment_type': appointment.appointment_type
        }
        
        # Send to client
        result = self.send_email(
            to_email=client.email,
            template_name='appointment_reminder',
            template_data=template_data
        )
        
        # Send to lawyer if different
        if lawyer.email != client.email:
            self.send_email(
                to_email=lawyer.email,
                template_name='appointment_reminder',
                template_data=template_data
            )
        
        return result
    
    def send_case_update_notification(self, case, update_type, details):
        """Send case update notification"""
        client = case.client
        lawyer = case.assigned_lawyer
        
        template_data = {
            'case_title': case.title,
            'case_number': case.case_number,
            'client_name': client.full_name,
            'lawyer_name': lawyer.full_name if lawyer else 'System',
            'update_type': update_type,
            'details': details,
            'update_date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        recipients = [client.email]
        if lawyer and lawyer.email != client.email:
            recipients.append(lawyer.email)
        
        results = []
        for recipient in recipients:
            result = self.send_email(
                to_email=recipient,
                template_name='case_update',
                template_data=template_data
            )
            results.append(result)
        
        return results
    
    def send_invoice_notification(self, invoice, client):
        """Send invoice notification"""
        template_data = {
            'invoice_number': invoice.invoice_number,
            'client_name': client.full_name,
            'amount_due': f"₹{invoice.total:.2f}",
            'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'Due upon receipt',
            'issue_date': invoice.issue_date.strftime('%Y-%m-%d'),
            'case_title': invoice.case.title if invoice.case else 'General',
            'lawyer_name': invoice.case.assigned_lawyer.full_name if invoice.case and invoice.case.assigned_lawyer else 'System'
        }
        
        return self.send_email(
            to_email=client.email,
            template_name='invoice_notification',
            template_data=template_data
        )
    
    def send_welcome_email(self, client, portal_credentials):
        """Send welcome email to new client with portal credentials"""
        template_data = {
            'client_name': client.full_name,
            'portal_url': current_app.config.get('PORTAL_URL', 'https://lawedge.com/portal'),
            'username': portal_credentials['username'],
            'temporary_password': portal_credentials['temporary_password'],
            'lawyer_name': client.assigned_lawyer.full_name if client.assigned_lawyer else 'System',
            'firm_name': current_app.config.get('FIRM_NAME', 'LawEdge Legal Services')
        }
        
        return self.send_email(
            to_email=client.email,
            template_name='welcome_email',
            template_data=template_data
        )
    
    def send_document_shared_notification(self, document, recipient_email, sharer_name):
        """Send notification when document is shared"""
        template_data = {
            'document_title': document.title,
            'sharer_name': sharer_name,
            'shared_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'document_category': document.category,
            'document_type': document.file_type
        }
        
        return self.send_email(
            to_email=recipient_email,
            template_name='document_shared',
            template_data=template_data
        )
    
    # Email Templates
    def _get_appointment_reminder_template(self):
        """HTML template for appointment reminder"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Appointment Reminder</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #007bff; margin: 0; font-size: 24px; }
                .details { margin-bottom: 20px; }
                .details p { margin: 5px 0; color: #666; }
                .details strong { color: #333; }
                .footer { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Appointment Reminder</h1>
                </div>
                <div class="details">
                    <p><strong>Appointment:</strong> {appointment_title}</p>
                    <p><strong>Date & Time:</strong> {appointment_date}</p>
                    <p><strong>Location:</strong> {appointment_location}</p>
                    <p><strong>Type:</strong> {appointment_type}</p>
                    <p><strong>Client:</strong> {client_name}</p>
                    <p><strong>Lawyer:</strong> {lawyer_name}</p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder from LawEdge Legal Services.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_appointment_reminder_text_template(self):
        """Text template for appointment reminder"""
        return """
        Appointment Reminder
        
        Appointment: {appointment_title}
        Date & Time: {appointment_date}
        Location: {appointment_location}
        Type: {appointment_type}
        Client: {client_name}
        Lawyer: {lawyer_name}
        
        This is an automated reminder from LawEdge Legal Services.
        """
    
    def _get_case_update_template(self):
        """HTML template for case update"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Case Update</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #007bff; margin: 0; font-size: 24px; }
                .details { margin-bottom: 20px; }
                .details p { margin: 5px 0; color: #666; }
                .details strong { color: #333; }
                .update-box { background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .footer { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Case Update</h1>
                </div>
                <div class="details">
                    <p><strong>Case:</strong> {case_title} ({case_number})</p>
                    <p><strong>Client:</strong> {client_name}</p>
                    <p><strong>Lawyer:</strong> {lawyer_name}</p>
                    <p><strong>Update Date:</strong> {update_date}</p>
                </div>
                <div class="update-box">
                    <p><strong>Update Type:</strong> {update_type}</p>
                    <p><strong>Details:</strong> {details}</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from LawEdge Legal Services.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_case_update_text_template(self):
        """Text template for case update"""
        return """
        Case Update
        
        Case: {case_title} ({case_number})
        Client: {client_name}
        Lawyer: {lawyer_name}
        Update Date: {update_date}
        
        Update Type: {update_type}
        Details: {details}
        
        This is an automated notification from LawEdge Legal Services.
        """
    
    def _get_invoice_template(self):
        """HTML template for invoice notification"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invoice Notification</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #28a745; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #28a745; margin: 0; font-size: 24px; }
                .invoice-details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .invoice-details p { margin: 5px 0; color: #666; }
                .invoice-details strong { color: #333; }
                .payment-info { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .footer { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Invoice {invoice_number}</h1>
                </div>
                <div class="invoice-details">
                    <p><strong>Amount Due:</strong> {amount_due}</p>
                    <p><strong>Due Date:</strong> {due_date}</p>
                    <p><strong>Issue Date:</strong> {issue_date}</p>
                    <p><strong>Case:</strong> {case_title}</p>
                    <p><strong>Lawyer:</strong> {lawyer_name}</p>
                </div>
                <div class="payment-info">
                    <p><strong>Client:</strong> {client_name}</p>
                    <p>Please arrange for payment at your earliest convenience.</p>
                </div>
                <div class="footer">
                    <p>This is an automated invoice from LawEdge Legal Services.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_invoice_text_template(self):
        """Text template for invoice notification"""
        return """
        Invoice {invoice_number}
        
        Amount Due: {amount_due}
        Due Date: {due_date}
        Issue Date: {issue_date}
        Case: {case_title}
        Lawyer: {lawyer_name}
        
        Client: {client_name}
        Please arrange for payment at your earliest convenience.
        
        This is an automated invoice from LawEdge Legal Services.
        """
    
    def _get_welcome_template(self):
        """HTML template for welcome email"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to LawEdge</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #007bff; margin: 0; font-size: 24px; }
                .welcome-text { margin: 20px 0; line-height: 1.6; color: #666; }
                .credentials { background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .credentials p { margin: 5px 0; }
                .credentials strong { color: #333; }
                .footer { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to LawEdge</h1>
                </div>
                <div class="welcome-text">
                    <p>Dear {client_name},</p>
                    <p>Welcome to LawEdge Legal Services! We are pleased to have you as our valued client.</p>
                    <p>Your client portal account has been created and you can now access your case information, documents, and communicate with your legal team.</p>
                </div>
                <div class="credentials">
                    <p><strong>Portal URL:</strong> {portal_url}</p>
                    <p><strong>Username:</strong> {username}</p>
                    <p><strong>Temporary Password:</strong> {temporary_password}</p>
                    <p>Please change your password after your first login for security.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>{lawyer_name}<br>{firm_name}</p>
                    <p>This is an automated welcome email from LawEdge Legal Services.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_text_template(self):
        """Text template for welcome email"""
        return """
        Welcome to LawEdge
        
        Dear {client_name},
        
        Welcome to LawEdge Legal Services! We are pleased to have you as our valued client.
        
        Your client portal account has been created and you can now access your case information, documents, and communicate with your legal team.
        
        Portal URL: {portal_url}
        Username: {username}
        Temporary Password: {temporary_password}
        
        Please change your password after your first login for security.
        
        Best regards,
        {lawyer_name}
        {firm_name}
        
        This is an automated welcome email from LawEdge Legal Services.
        """
    
    def _get_document_shared_template(self):
        """HTML template for document shared notification"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Document Shared</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #17a2b8; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #17a2b8; margin: 0; font-size: 24px; }
                .details { margin-bottom: 20px; }
                .details p { margin: 5px 0; color: #666; }
                .footer { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Document Shared</h1>
                </div>
                <div class="details">
                    <p><strong>Document:</strong> {document_title}</p>
                    <p><strong>Shared By:</strong> {sharer_name}</p>
                    <p><strong>Shared Date:</strong> {shared_date}</p>
                    <p><strong>Category:</strong> {document_category}</p>
                    <p><strong>Type:</strong> {document_type}</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from LawEdge Legal Services.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_document_shared_text_template(self):
        """Text template for document shared notification"""
        return """
        Document Shared
        
        Document: {document_title}
        Shared By: {sharer_name}
        Shared Date: {shared_date}
        Category: {document_category}
        Type: {document_type}
        
        This is an automated notification from LawEdge Legal Services.
        """

# Initialize email service
email_service = EmailService()
