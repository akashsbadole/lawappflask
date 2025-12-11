"""
Calendar Integration Module
Implements calendar synchronization with Google Calendar, Outlook, and other calendar services
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import current_app

# Try to import calendar service libraries
try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.errors import HttpError
    from googleapiclient import calendar
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False

try:
    import exchangelib
    from exchangelib import Credentials, Account
    from exchangelib.protocol import Autodiscover
    from exchangelib.protocol import Permissions
    EXCHANGE_CALENDAR_AVAILABLE = True
except ImportError:
    EXCHANGE_CALENDAR_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class CalendarService:
    """Calendar service integration with multiple providers"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        # Google Calendar Configuration
        self.google_credentials_path = app.config.get('GOOGLE_CALENDAR_CREDENTIALS_PATH', 'credentials.json')
        self.google_scopes = ['https://www.googleapis.com/auth/calendar']
        self.google_client_secrets = app.config.get('GOOGLE_CLIENT_SECRETS')
        
        # Exchange Calendar Configuration
        self.exchange_client_id = app.config.get('EXCHANGE_CLIENT_ID')
        self.exchange_client_secret = app.config.get('EXCHANGE_CLIENT_SECRET')
        self.exchange_tenant_id = app.config.get('EXCHANGE_TENANT_ID')
        self.exchange_authority = app.config.get('EXCHANGE_AUTHORITY', 'login.microsoftonline.com')
        
        # Calendar Settings
        self.default_reminder_minutes = app.config.get('DEFAULT_REMINDER_MINUTES', 30)
        self.default_timezone = app.config.get('DEFAULT_TIMEZONE', 'Asia/Kolkata')
    
    def create_google_calendar_event(self, event_data):
        """Create event in Google Calendar"""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return False, "Google Calendar library not available"
        
        try:
            creds = self._get_google_credentials()
            if not creds:
                return False, "Google Calendar credentials not found"
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Prepare event data
            event = {
                'summary': event_data.get('title', ''),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': self._format_datetime_for_google(event_data['start_time']),
                    'timeZone': self.default_timezone
                },
                'end': {
                    'dateTime': self._format_datetime_for_google(event_data['end_time']),
                    'timeZone': self.default_timezone
                },
                'attendees': self._format_attendees_for_google(event_data.get('attendees', [])),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {
                            'method': 'email',
                            'minutes': event_data.get('reminder_minutes', self.default_reminder_minutes)
                        }
                    ]
                }
            }
            
            # Add location if provided
            if event_data.get('location'):
                event['location'] = event_data['location']
            
            # Add recurrence if provided
            if event_data.get('recurrence'):
                event['recurrence'] = event_data['recurrence']
            
            # Create event
            event_result = service.events().insert(calendarId='primary', body=event).execute()
            
            logger.info(f"Google Calendar event created: {event_result.get('htmlLink')}")
            return True, f"Event created: {event_result.get('htmlLink')}"
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {str(e)}")
            return False, f"Error creating Google Calendar event: {str(e)}"
    
    def update_google_calendar_event(self, event_id, event_data):
        """Update event in Google Calendar"""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return False, "Google Calendar library not available"
        
        try:
            creds = self._get_google_credentials()
            if not creds:
                return False, "Google Calendar credentials not found"
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Prepare event data
            event = {
                'summary': event_data.get('title', ''),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': self._format_datetime_for_google(event_data['start_time']),
                    'timeZone': self.default_timezone
                },
                'end': {
                    'dateTime': self._format_datetime_for_google(event_data['end_time']),
                    'timeZone': self.default_timezone
                }
            }
            
            # Update optional fields
            if event_data.get('location'):
                event['location'] = event_data['location']
            
            if event_data.get('attendees'):
                event['attendees'] = self._format_attendees_for_google(event_data['attendees'])
            
            # Update event
            event_result = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Google Calendar event updated: {event_result.get('htmlLink')}")
            return True, f"Event updated: {event_result.get('htmlLink')}"
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {str(e)}")
            return False, f"Error updating Google Calendar event: {str(e)}"
    
    def delete_google_calendar_event(self, event_id):
        """Delete event from Google Calendar"""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return False, "Google Calendar library not available"
        
        try:
            creds = self._get_google_credentials()
            if not creds:
                return False, "Google Calendar credentials not found"
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Delete event
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            
            logger.info(f"Google Calendar event deleted: {event_id}")
            return True, f"Event {event_id} deleted successfully"
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False, f"Google Calendar API error: {error}"
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {str(e)}")
            return False, f"Error deleting Google Calendar event: {str(e)}"
    
    def create_exchange_calendar_event(self, event_data):
        """Create event in Exchange Calendar"""
        if not EXCHANGE_CALENDAR_AVAILABLE:
            return False, "Exchange Calendar library not available"
        
        try:
            credentials = self._get_exchange_credentials()
            if not credentials:
                return False, "Exchange Calendar credentials not found"
            
            # Authenticate with Exchange
            account = Account(credentials)
            if not account:
                return False, "Exchange account authentication failed"
            
            # Create event object
            event = exchangelib.Message(
                subject=event_data.get('title', ''),
                body=event_data.get('description', ''),
                start=event_data['start_time'],
                end=event_data['end_time']
            )
            
            # Add location
            if event_data.get('location'):
                event.location = event_data['location']
            
            # Add attendees
            if event_data.get('attendees'):
                for attendee in event_data['attendees']:
                    event.add_attendee(attendee['email'], attendee['name'])
            
            # Add reminder
            if event_data.get('reminder_minutes'):
                event.reminder_before(20)
                event.reminder_minutes = event_data['reminder_minutes']
            
            # Save event
            saved_event = account.calendar.save_event(event)
            
            logger.info(f"Exchange Calendar event created: {saved_event.subject}")
            return True, f"Event created: {saved_event.subject}"
            
        except Exception as e:
            logger.error(f"Error creating Exchange Calendar event: {str(e)}")
            return False, f"Error creating Exchange Calendar event: {str(e)}"
    
    def update_exchange_calendar_event(self, event_id, event_data):
        """Update event in Exchange Calendar"""
        if not EXCHANGE_CALENDAR_AVAILABLE:
            return False, "Exchange Calendar library not available"
        
        try:
            credentials = self._get_exchange_credentials()
            if not credentials:
                return False, "Exchange Calendar credentials not found"
            
            # Authenticate with Exchange
            account = Account(credentials)
            if not account:
                return False, "Exchange account authentication failed"
            
            # Get existing event
            item_view = account.calendar.get(calendar_id=event_id, include_body=True)
            if len(item_view.items) == 0:
                return False, f"Event {event_id} not found in Exchange Calendar"
            
            event = item_view.items[0]
            
            # Update event fields
            event.subject = event_data.get('title', event.subject)
            event.body = event_data.get('description', event.body)
            event.start = event_data['start_time']
            event.end = event_data['end_time']
            
            # Update optional fields
            if event_data.get('location'):
                event.location = event_data['location']
            
            # Save updated event
            event.save()
            
            logger.info(f"Exchange Calendar event updated: {event.subject}")
            return True, f"Event updated: {event.subject}"
            
        except Exception as e:
            logger.error(f"Error updating Exchange Calendar event: {str(e)}")
            return False, f"Error updating Exchange Calendar event: {str(e)}"
    
    def delete_exchange_calendar_event(self, event_id):
        """Delete event from Exchange Calendar"""
        if not EXCHANGE_CALENDAR_AVAILABLE:
            return False, "Exchange Calendar library not available"
        
        try:
            credentials = self._get_exchange_credentials()
            if not credentials:
                return False, "Exchange Calendar credentials not found"
            
            # Authenticate with Exchange
            account = Account(credentials)
            if not account:
                return False, "Exchange account authentication failed"
            
            # Get existing event
            item_view = account.calendar.get(calendar_id=event_id, include_body=True)
            if len(item_view.items) == 0:
                return False, f"Event {event_id} not found in Exchange Calendar"
            
            event = item_view.items[0]
            
            # Delete event
            event.delete()
            
            logger.info(f"Exchange Calendar event deleted: {event_id}")
            return True, f"Event {event_id} deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting Exchange Calendar event: {str(e)}")
            return False, f"Error deleting Exchange Calendar event: {str(e)}"
    
    def sync_appointment_to_calendar(self, appointment, provider='google'):
        """Sync appointment to calendar service"""
        if provider == 'google':
            return self._sync_appointment_to_google_calendar(appointment)
        elif provider == 'exchange':
            return self._sync_appointment_to_exchange_calendar(appointment)
        else:
            return self._sync_appointment_to_google_calendar(appointment)
    
    def _sync_appointment_to_google_calendar(self, appointment):
        """Sync appointment to Google Calendar"""
        # Check if appointment already has a calendar event ID
        if appointment.calendar_event_id:
            # Update existing event
            event_data = {
                'title': appointment.title,
                'description': appointment.description,
                'start_time': appointment.start_time,
                'end_time': appointment.end_time,
                'location': appointment.location,
                'reminder_minutes': 30  # Default reminder
            }
            
            # Get existing Google Calendar event ID
            google_event_id = self._extract_google_event_id_from_notes(appointment.notes)
            if google_event_id:
                return self.update_google_calendar_event(google_event_id, event_data)
            else:
                result = self.create_google_calendar_event(event_data)
                if result[0]:
                    # Save Google Calendar event ID to appointment notes
                    self._save_google_event_id_to_appointment(appointment, result[1])
                return result
        else:
            # Create new event
            event_data = {
                'title': appointment.title,
                'description': appointment.description,
                'start_time': appointment.start_time,
                'end_time': appointment.end_time,
                'location': appointment.location,
                'reminder_minutes': 30  # Default reminder
            }
            
            result = self.create_google_calendar_event(event_data)
            if result[0]:
                # Save Google Calendar event ID to appointment notes
                self._save_google_event_id_to_appointment(appointment, result[1])
                return result
        
        return False, "Failed to sync appointment to Google Calendar"
    
    def _sync_appointment_to_exchange_calendar(self, appointment):
        """Sync appointment to Exchange Calendar"""
        # Similar implementation for Exchange Calendar
        event_data = {
            'title': appointment.title,
            'description': appointment.description,
            'start_time': appointment.start_time,
            'end_time': appointment.end_time,
            'location': appointment.location,
            'reminder_minutes': 30  # Default reminder
        }
        
        # Check if appointment already has a calendar event ID
        if appointment.calendar_event_id:
            # Update existing event
            return self.update_exchange_calendar_event(appointment.calendar_event_id, event_data)
        else:
            # Create new event
            result = self.create_exchange_calendar_event(event_data)
            if result[0]:
                # Save Exchange event ID to appointment notes
                self._save_exchange_event_id_to_appointment(appointment, result[1])
                return result
        
        return False, "Failed to sync appointment to Exchange Calendar"
    
    def _get_google_credentials(self):
        """Get Google Calendar credentials"""
        if not self.google_client_secrets:
            return None
        
        creds = None
        if os.path.exists(self.google_credentials_path):
            creds = Credentials.from_authorized_user_file(
                self.google_credentials_path, self.google_scopes)
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.google_client_secrets, self.google_scopes)
                creds = flow.run_local_server(port=0)
                with open(self.google_credentials_path, 'w') as token:
                    token.write(creds.to_json())
                creds = Credentials.from_authorized_user_file(
                    self.google_credentials_path, self.google_scopes)
            return creds
        
        return None
    
    def _get_exchange_credentials(self):
        """Get Exchange credentials"""
        if not self.exchange_client_id or not self.exchange_client_secret:
            return None
        
        credentials = Credentials(
            client_id=self.exchange_client_id,
            client_secret=self.exchange_client_secret,
            tenant_id=self.exchange_tenant_id
        )
        
        return credentials
    
    def _format_datetime_for_google(self, dt):
        """Format datetime for Google Calendar API"""
        return dt.isoformat()
    
    def _format_attendees_for_google(self, attendees):
        """Format attendees for Google Calendar API"""
        formatted_attendees = []
        for attendee in attendees:
            formatted_attendees.append({
                'email': attendee.get('email', ''),
                'displayName': attendee.get('name', ''),
                'responseStatus': 'needsAction'
            })
        return formatted_attendees
    
    def _extract_google_event_id_from_notes(self, notes):
        """Extract Google Calendar event ID from appointment notes"""
        if not notes:
            return None
        
        # Look for Google Calendar event ID pattern in notes
        pattern = r'Google Calendar Event ID:\s*([^\s\n]+)'
        match = re.search(pattern, notes)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _extract_exchange_event_id_from_notes(self, notes):
        """Extract Exchange event ID from appointment notes"""
        if not notes:
            return None
        
        # Look for Exchange event ID pattern in notes
        pattern = r'Exchange Event ID:\s*([^\s\n]+)'
        match = re.search(pattern, notes)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _save_google_event_id_to_appointment(self, appointment, event_id):
        """Save Google Calendar event ID to appointment notes"""
        try:
            # Import here to avoid circular imports
            from models import db, Appointment, ActivityLog
            
            # Update appointment notes with event ID
            current_notes = appointment.notes or ""
            google_event_pattern = f"Google Calendar Event ID: {event_id}"
            
            # Check if event ID already exists in notes
            if google_event_pattern not in current_notes:
                appointment.notes = f"{current_notes}\n{google_event_pattern}"
            
            # Add activity log
            activity = ActivityLog(
                user_id=appointment.lawyer_id,
                action="sync_to_google_calendar",
                resource_type="appointment",
                resource_id=appointment.id,
                details=f"Appointment {appointment.id} synced to Google Calendar with event ID: {event_id}"
            )
            db.session.add(activity)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving Google event ID to appointment: {str(e)}")
    
    def _save_exchange_event_id_to_appointment(self, appointment, event_id):
        """Save Exchange event ID to appointment notes"""
        from models import db, Appointment
        
        try:
            # Update appointment notes with event ID
            current_notes = appointment.notes or ""
            exchange_event_pattern = f"Exchange Event ID: {event_id}"
            
            # Check if event ID already exists in notes
            if exchange_event_pattern not in current_notes:
                appointment.notes = f"{current_notes}\n{exchange_event_pattern}"
            
            # Add activity log
            from models import ActivityLog
            activity = ActivityLog(
                user_id=appointment.lawyer_id,
                action="sync_to_exchange_calendar",
                resource_type="appointment",
                resource_id=appointment.id,
                details=f"Appointment {appointment.id} synced to Exchange Calendar with event ID: {event_id}"
            )
            db.session.add(activity)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving Exchange event ID to appointment: {str(e)}")
    
    def schedule_reminder_for_appointment(self, appointment):
        """Schedule reminder for upcoming appointment"""
        try:
            # Calculate reminder time
            reminder_time = appointment.start_time - timedelta(minutes=self.default_reminder_minutes)
            
            # Create calendar reminder event
            reminder_event = {
                'title': f"Reminder: {appointment.title}",
                'description': f"Appointment reminder for {appointment.client.full_name}",
                'start_time': reminder_time,
                'end_time': reminder_time + timedelta(minutes=5),
                'attendees': [appointment.client.email] + ',' + appointment.lawyer.email] if appointment.lawyer else appointment.client.email
            }
            
            # Sync to calendar
            result = self.sync_appointment_to_calendar({
                'appointment': appointment,
                'start_time': reminder_time,
                'end_time': appointment.end_time
            })
            
            # Create notification
            from enhanced_security import enhanced_security
            
            enhanced_security.log_security_event(
                appointment.lawyer_id,
                'schedule_reminder',
                'appointment',
                appointment.id,
                f"Reminder scheduled for appointment {appointment.title}",
                request.remote_addr
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error scheduling appointment reminder: {str(e)}")
            return False, f"Error scheduling reminder: {str(e)}"

# Initialize calendar service
calendar_service = CalendarService()
