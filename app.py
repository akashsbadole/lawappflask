from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_session import Session
from flask_mail import Mail
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, DateTimeField, IntegerField, FloatField, BooleanField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

# Forms
class ClientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Length(max=20)])
    address = TextAreaField('Address', validators=[Length(max=500)])
    city = StringField('City', validators=[Length(max=100)])
    state = StringField('State', validators=[Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Length(max=20)])
    company = StringField('Company', validators=[Length(max=200)])
    client_type = SelectField('Client Type', choices=[
        ('individual', 'Individual'),
        ('corporate', 'Corporate'),
        ('government', 'Government'),
        ('ngo', 'NGO')
    ], default='individual')
    practice_area = SelectField('Practice Area', choices=[
        ('property_law', 'Property Law'),
        ('corporate_law', 'Corporate Law'),
        ('criminal_law', 'Criminal Law'),
        ('family_law', 'Family Law'),
        ('employment_law', 'Employment Law'),
        ('intellectual_property', 'Intellectual Property'),
        ('tax_law', 'Tax Law'),
        ('immigration_law', 'Immigration Law'),
        ('environmental_law', 'Environmental Law'),
        ('other', 'Other')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    assigned_lawyer_id = SelectField('Assigned Lawyer', coerce=int, validators=[Optional()])
    tags = StringField('Tags', validators=[Length(max=500)])
    notes = TextAreaField('Notes', validators=[Length(max=1000)])

class CaseForm(FlaskForm):
    title = StringField('Case Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    assigned_lawyer_id = SelectField('Assigned Lawyer', coerce=int, validators=[Optional()])
    case_type = SelectField('Case Type', choices=[
        ('civil', 'Civil'),
        ('criminal', 'Criminal'),
        ('corporate', 'Corporate'),
        ('family', 'Family'),
        ('employment', 'Employment'),
        ('property', 'Property'),
        ('intellectual_property', 'Intellectual Property'),
        ('tax', 'Tax'),
        ('immigration', 'Immigration'),
        ('environmental', 'Environmental'),
        ('other', 'Other')
    ])
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed')
    ], default='open')
    stage = SelectField('Stage', choices=[
        ('initial', 'Initial Assessment'),
        ('investigation', 'Investigation'),
        ('pleading', 'Pleading'),
        ('discovery', 'Discovery'),
        ('negotiation', 'Negotiation'),
        ('trial', 'Trial'),
        ('appeal', 'Appeal'),
        ('enforcement', 'Enforcement')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    date_opened = DateField('Date Opened', validators=[Optional()])
    estimated_completion = DateField('Estimated Completion', validators=[Optional()])
    billing_method = SelectField('Billing Method', choices=[
        ('hourly', 'Hourly'),
        ('flat_fee', 'Flat Fee'),
        ('contingency', 'Contingency'),
        ('retainer', 'Retainer')
    ], default='hourly')
    hourly_rate = FloatField('Hourly Rate', validators=[Optional()])
    budget = FloatField('Budget', validators=[Optional()])
    court_number = StringField('Court Number', validators=[Length(max=100)])
    notes = TextAreaField('Notes', validators=[Length(max=1000)])

class AppointmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    lawyer_id = SelectField('Lawyer', coerce=int, validators=[Optional()])
    case_id = SelectField('Case', coerce=int, validators=[Optional()])
    appointment_type = SelectField('Appointment Type', choices=[
        ('consultation', 'Consultation'),
        ('meeting', 'Meeting'),
        ('court_hearing', 'Court Hearing'),
        ('deposition', 'Deposition'),
        ('mediation', 'Mediation'),
        ('arbitration', 'Arbitration'),
        ('other', 'Other')
    ])
    start_time = DateTimeField('Start Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('End Time', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    location = StringField('Location', validators=[Length(max=500)])
    is_virtual = BooleanField('Virtual Meeting')
    meeting_link = StringField('Meeting Link', validators=[Length(max=500)])
    reminder_minutes = IntegerField('Reminder Minutes', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Length(max=1000)])

class DocumentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    category = SelectField('Category', choices=[
        ('contract', 'Contract'),
        ('court_filing', 'Court Filing'),
        ('correspondence', 'Correspondence'),
        ('evidence', 'Evidence'),
        ('legal_brief', 'Legal Brief'),
        ('motion', 'Motion'),
        ('pleading', 'Pleading'),
        ('research', 'Research'),
        ('other', 'Other')
    ])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    case_id = SelectField('Case', coerce=int, validators=[Optional()])
    file = FileField('File', validators=[DataRequired()])
    tags = StringField('Tags', validators=[Length(max=500)])
    document_type = SelectField('Document Type', choices=[
        ('original', 'Original'),
        ('copy', 'Copy'),
        ('draft', 'Draft'),
        ('final', 'Final'),
        ('signed', 'Signed')
    ], default='original')
    is_confidential = BooleanField('Confidential')
    requires_signature = BooleanField('Requires Signature')
    signature_details = TextAreaField('Signature Details', validators=[Length(max=500)])
    is_template = BooleanField('Template')
    template_details = TextAreaField('Template Details', validators=[Length(max=500)])
    expiry_date = DateField('Expiry Date', validators=[Optional()])

class TimeEntryForm(FlaskForm):
    case_id = SelectField('Case', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    lawyer_id = SelectField('Lawyer', coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    start_time = DateTimeField('Start Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('End Time', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    duration_minutes = IntegerField('Duration (minutes)', validators=[Optional()])
    is_billable = BooleanField('Billable')
    hourly_rate = FloatField('Hourly Rate', validators=[Optional()])
    amount = FloatField('Amount', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('invoiced', 'Invoiced')
    ], default='draft')
    notes = TextAreaField('Notes', validators=[Length(max=1000)])

class ExpenseForm(FlaskForm):
    case_id = SelectField('Case', coerce=int, validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    lawyer_id = SelectField('Lawyer', coerce=int, validators=[Optional()])
    expense_type = SelectField('Expense Type', choices=[
        ('travel', 'Travel'),
        ('meals', 'Meals'),
        ('accommodation', 'Accommodation'),
        ('office_supplies', 'Office Supplies'),
        ('legal_research', 'Legal Research'),
        ('court_fees', 'Court Fees'),
        ('expert_witness', 'Expert Witness'),
        ('other', 'Other')
    ])
    description = StringField('Description', validators=[DataRequired(), Length(max=500)])
    amount = FloatField('Amount', validators=[DataRequired()])
    currency = SelectField('Currency', choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('INR', 'INR')
    ], default='USD')
    date_incurred = DateField('Date Incurred', validators=[DataRequired()])
    is_billable = BooleanField('Billable to Client')
    receipt = FileField('Receipt', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reimbursed', 'Reimbursed')
    ], default='pending')
    notes = TextAreaField('Notes', validators=[Length(max=1000)])
    # Additional fields for the template
    date = DateField('Date', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('travel', 'Travel'),
        ('meals', 'Meals'),
        ('accommodation', 'Accommodation'),
        ('office_supplies', 'Office Supplies'),
        ('legal_research', 'Legal Research'),
        ('court_fees', 'Court Fees'),
        ('expert_witness', 'Expert Witness'),
        ('professional_services', 'Professional Services'),
        ('research_database', 'Research & Database'),
        ('postage_delivery', 'Postage & Delivery'),
        ('other', 'Other')
    ])
    payment_method = SelectField('Payment Method', choices=[
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other')
    ])
    is_billable_to_client = BooleanField('Billable to Client')
    is_reimbursable = BooleanField('Reimbursable')
    reimbursement_details = TextAreaField('Reimbursement Details', validators=[Length(max=500)])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Email(), Length(max=120)])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional(),
        EqualTo('password', message='Passwords must match')
    ])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    role = SelectField('Role', choices=[
        ('admin', 'Administrator'),
        ('lawyer', 'Lawyer'),
        ('paralegal', 'Paralegal'),
        ('staff', 'Staff'),
        ('finance', 'Finance')
    ], validators=[DataRequired()])
    phone = StringField('Phone', validators=[Length(max=20)])
    address = TextAreaField('Address', validators=[Length(max=500)])
    is_active = BooleanField('Active', default=True)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import uuid
from functools import wraps
from zoneinfo import ZoneInfo
from io import BytesIO
import csv
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'law_firm_management_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///law_firm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
# Set session type to filesystem to avoid potential issues with session serialization
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
app.config['SESSION_FILE_THRESHOLD'] = 500

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@lawedge.com')
app.config['MAIL_DEFAULT_RECIPIENT'] = os.environ.get('MAIL_DEFAULT_RECIPIENT', 'info@lawedge.com')
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False

# Initialize Flask-Mail
mail = Mail(app)
app.mail = mail

# Import models first to get the db instance
import models
from models import db, User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, TrustAccount, TrustTransaction, Notification, ActivityLog, Firm, Branch, Permission, RolePermission, Communication, Lead, CaseWorkflow, DocumentVersion, Expense, InvoiceLineItem, ClientPortalUser, DocumentAnalysis, LegalResearch, AutomationRule, SystemSetting, AttendanceRecord, SecurityEvent

# Import enhanced modules
try:
    from enhanced_security import enhanced_security, attendance_tracker, role_manager
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError:
    ENHANCED_SECURITY_AVAILABLE = False
    print("Warning: Enhanced security module not available")

try:
    from enhanced_security_routes import enhanced_security_bp
    ENHANCED_SECURITY_ROUTES_AVAILABLE = True
except ImportError:
    ENHANCED_SECURITY_ROUTES_AVAILABLE = False
    print("Warning: Enhanced security routes not available")

try:
    from document_ocr import ocr_engine, document_analyzer, document_search, process_document_ocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR module not available")

try:
    from analytics_reporting import analytics_engine
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("Warning: Analytics module not available")

try:
    from document_routes import documents_bp
    ENHANCED_DOCUMENTS_AVAILABLE = True
except ImportError:
    ENHANCED_DOCUMENTS_AVAILABLE = False
    print("Warning: Enhanced document routes not available")

try:
    from auth_routes import auth_bp
    AUTH_ROUTES_AVAILABLE = True
except ImportError:
    AUTH_ROUTES_AVAILABLE = False
    print("Warning: Auth routes not available")

try:
    from analytics_routes import analytics_bp
    ANALYTICS_ROUTES_AVAILABLE = True
except ImportError:
    ANALYTICS_ROUTES_AVAILABLE = False
    print("Warning: Analytics routes not available")

# Initialize the app with the db instance from models
db.init_app(app)
migrate = Migrate(app, db)

# Initialize enhanced services
if ENHANCED_SECURITY_AVAILABLE:
    enhanced_security.init_app(app)

if OCR_AVAILABLE:
    ocr_engine.init_app(app)
    document_analyzer.init_app(app)

if ANALYTICS_AVAILABLE:
    analytics_engine.init_app(app)

# Register blueprints
if AUTH_ROUTES_AVAILABLE:
    app.register_blueprint(auth_bp, url_prefix='/auth')

if ENHANCED_SECURITY_ROUTES_AVAILABLE:
    app.register_blueprint(enhanced_security_bp, url_prefix='/security')

if ENHANCED_DOCUMENTS_AVAILABLE:
    app.register_blueprint(documents_bp, url_prefix='/documents_enhanced')

if ANALYTICS_AVAILABLE:
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

# Register enquiry routes
from enquiry_routes import enquiry_bp
app.register_blueprint(enquiry_bp)

# Create tables
with app.app_context():
    db.create_all()

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role-based access decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Permission check decorator
def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            
            # Admin has all permissions
            if user.role == 'admin':
                return f(*args, **kwargs)
            
            # Check if user has the specific permission
            permission = Permission.query.filter_by(name=permission_name).first()
            if permission:
                role_permission = RolePermission.query.filter_by(role=user.role, permission_id=permission.id).first()
                if not role_permission:
                    flash('You do not have permission to access this page.', 'danger')
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Activity logging function
def log_activity(user_id, action, resource_type=None, resource_id=None, details=None):
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(activity)
    db.session.commit()

# Notification function
def create_notification(user_id, title, message, notification_type='system'):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

# System settings function
def get_system_setting(key, default=None):
    setting = SystemSetting.query.filter_by(key=key).first()
    if setting:
        if setting.data_type == 'integer':
            return int(setting.value)
        elif setting.data_type == 'boolean':
            return setting.value.lower() == 'true'
        elif setting.data_type == 'json':
            return json.loads(setting.value)
        else:
            return setting.value
    return default

# Routes
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response for favicon

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log activity
            log_activity(user.id, 'login')
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'logout')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Get dashboard data based on user role
    if user.role == 'admin':
        clients_count = Client.query.count()
        cases_count = Case.query.filter_by(status='active').count()
        appointments_count = Appointment.query.filter_by(status='scheduled').count()
        pending_invoices = Invoice.query.filter_by(status='sent').count()
        leads_count = Lead.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Calculate revenue this month
        current_month = datetime.utcnow().replace(day=1)
        revenue_this_month = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.payment_date >= current_month
        ).scalar() or 0
        
        # Get pending tasks (appointments + overdue tasks)
        pending_tasks = Appointment.query.filter(
            Appointment.start_time >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        ).count()
        
    elif user.role == 'lawyer':
        clients_count = Client.query.filter_by(assigned_lawyer_id=user.id).count()
        cases_count = Case.query.filter_by(assigned_lawyer_id=user.id, status='active').count()
        appointments_count = Appointment.query.filter_by(lawyer_id=user.id, status='scheduled').count()
        pending_invoices = Invoice.query.join(Case).filter(Case.assigned_lawyer_id == user.id, Invoice.status == 'sent').count()
        leads_count = Lead.query.filter_by(assigned_lawyer_id=user.id).count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Calculate revenue this month for this lawyer
        current_month = datetime.utcnow().replace(day=1)
        revenue_this_month = db.session.query(db.func.sum(Payment.amount)).join(Invoice).join(Case).filter(
            Case.assigned_lawyer_id == user.id,
            Payment.payment_date >= current_month
        ).scalar() or 0
        
        # Get pending tasks for this lawyer
        pending_tasks = Appointment.query.filter(
            Appointment.lawyer_id == user.id,
            Appointment.start_time >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        ).count()
        
    else:
        clients_count = 0
        cases_count = 0
        appointments_count = 0
        pending_invoices = 0
        leads_count = 0
        active_users = 0
        revenue_this_month = 0
        pending_tasks = 0
    
    # Create stats dictionary
    stats = {
        'active_cases': cases_count,
        'total_clients': clients_count,
        'revenue_this_month': revenue_this_month,
        'pending_tasks': pending_tasks
    }
    
    # Get recent activities
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Get upcoming appointments as tasks
    if user.role == 'admin':
        upcoming_appointments = Appointment.query.filter(
            Appointment.start_time >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        ).order_by(Appointment.start_time).limit(5).all()
    else:
        upcoming_appointments = Appointment.query.filter(
            Appointment.lawyer_id == user.id,
            Appointment.start_time >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        ).order_by(Appointment.start_time).limit(5).all()
    
    # Convert appointments to tasks format
    upcoming_tasks = []
    for apt in upcoming_appointments:
        upcoming_tasks.append({
            'id': apt.id,
            'title': apt.title,
            'description': apt.description or '',
            'type': 'appointment',
            'due_date': apt.start_time,
            'is_today': apt.start_time.date() == datetime.utcnow().date(),
            'is_overdue': apt.start_time < datetime.utcnow(),
            'assigned_to': apt.lawyer,
            'client': apt.client
        })
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Prepare financial summary (placeholder data)
    financial_summary = {
        'revenue': {
            'current': revenue_this_month,
            'previous': revenue_this_month * 0.8,  # Placeholder
            'change': revenue_this_month * 0.2,
            'percent_change': 25.0
        },
        'expenses': {
            'current': revenue_this_month * 0.3,  # Placeholder
            'previous': revenue_this_month * 0.25,
            'change': revenue_this_month * 0.05,
            'percent_change': 20.0
        },
        'profit': {
            'current': revenue_this_month * 0.7,  # Placeholder
            'previous': revenue_this_month * 0.6,
            'change': revenue_this_month * 0.1,
            'percent_change': 16.7
        },
        'outstanding_invoices': {
            'current': pending_invoices * 1000,  # Placeholder
            'previous': pending_invoices * 800,
            'change': pending_invoices * 200,
            'percent_change': 25.0
        }
    }
    
    # Prepare performance metrics (placeholder data)
    performance_metrics = {
        'billable_hours': {
            'current': 120,
            'target': 160,
            'percentage': 75.0
        },
        'collection_rate': {
            'current': 85.0,
            'target': 90.0,
            'percentage': 94.4
        },
        'client_satisfaction': {
            'current': 4.5,
            'target': 4.8,
            'percentage': 93.8
        },
        'case_resolution': {
            'current': 78.0,
            'target': 85.0,
            'percentage': 91.8
        }
    }
    
    # Prepare chart data (placeholder data)
    revenue_chart = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'data': [45000, 52000, 48000, 61000, 58000, 67000]
    }
    
    case_status_chart = {
        'labels': ['Active', 'Pending', 'Closed'],
        'data': [cases_count, 15, 45]
    }
    
    time_category_chart = {
        'labels': ['Research', 'Client Meetings', 'Court', 'Documentation'],
        'data': [25, 35, 15, 25]
    }
    
    expense_category_chart = {
        'labels': ['Office', 'Travel', 'Marketing', 'Legal', 'Other'],
        'data': [5000, 3000, 2000, 1500, 1000]
    }
    
    client_acquisition_chart = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'data': [3, 5, 4, 7, 6, 8]
    }
    
    return render_template('dashboard.html', 
                         user=user,
                         stats=stats,
                         clients_count=clients_count,
                         cases_count=cases_count,
                         appointments_count=appointments_count,
                         pending_invoices=pending_invoices,
                         leads_count=leads_count,
                         active_users=active_users,
                         recent_activities=recent_activities,
                         upcoming_appointments=upcoming_appointments,
                         upcoming_tasks=upcoming_tasks,
                         unread_notifications=unread_notifications,
                         financial_summary=financial_summary,
                         performance_metrics=performance_metrics,
                         revenue_chart=revenue_chart,
                         case_status_chart=case_status_chart,
                         time_category_chart=time_category_chart,
                         expense_category_chart=expense_category_chart,
                         client_acquisition_chart=client_acquisition_chart)

# User Management Routes (Step 1)
@app.route('/users')
@login_required
@role_required('admin')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    form = UserForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                role=form.role.data,
                phone=form.phone.data,
                address=form.address.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            # Log activity
            log_activity(session['user_id'], 'create_user', 'user', user.id, f'Created user: {user.full_name}')
            
            flash('User added successfully!', 'success')
            return redirect(url_for('users'))
    
    return render_template('add_user.html', form=form)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            user.username = form.username.data
            user.email = form.email.data
            user.full_name = form.full_name.data
            user.role = form.role.data
            user.phone = form.phone.data
            user.address = form.address.data
            user.is_active = form.is_active.data
            
            if form.password.data:
                user.set_password(form.password.data)
            
            db.session.commit()
            
            # Log activity
            log_activity(session['user_id'], 'update_user', 'user', user.id, f'Updated user: {user.full_name}')
            
            flash('User updated successfully!', 'success')
            return redirect(url_for('users'))
    
    # Populate form with existing user data for GET request
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.full_name.data = user.full_name
        form.role.data = user.role
        form.phone.data = user.phone
        form.address.data = user.address
        form.is_active.data = user.is_active
    
    return render_template('edit_user.html', user=user, form=form)

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    
    user.full_name = request.form.get('full_name')
    user.email = request.form.get('email')
    user.phone = request.form.get('phone')
    user.address = request.form.get('address')
    
    if request.form.get('password'):
        user.set_password(request.form.get('password'))
    
    db.session.commit()
    
    # Log activity
    log_activity(user.id, 'update_profile', 'user', user.id, f'Updated profile')
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

# Client Management Routes (Step 2)
@app.route('/clients')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def clients():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        clients = Client.query.all()
    else:
        clients = Client.query.filter_by(assigned_lawyer_id=user.id).all()
    return render_template('clients.html', clients=clients)

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def add_client():
    form = ClientForm()
    form.assigned_lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Generate client number
            last_client = Client.query.order_by(Client.id.desc()).first()
            if last_client:
                client_num = int(last_client.client_number.split('-')[2]) + 1
            else:
                client_num = 1
            
            client_number = f"CL-2023-{client_num:03d}"
            
            client = Client(
                client_number=client_number,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                postal_code=form.postal_code.data,
                company=form.company.data,
                client_type=form.client_type.data,
                practice_area=form.practice_area.data,
                priority=form.priority.data,
                assigned_lawyer_id=form.assigned_lawyer_id.data or session['user_id'],
                notes=form.notes.data
            )
            
            db.session.add(client)
            db.session.commit()
            
            # Log activity and create notification
            log_activity(session['user_id'], 'create_client', 'client', client.id, f'Created client: {client.full_name}')
            
            # Create notification for assigned lawyer if different from current user
            if client.assigned_lawyer_id != session['user_id']:
                create_notification(client.assigned_lawyer_id, 'New Client Assigned', 
                                  f'You have been assigned a new client: {client.full_name}', 'client')
            
            flash('Client added successfully!', 'success')
            return redirect(url_for('clients'))
        else:
            # If form validation fails, repopulate choices
            form.assigned_lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    lawyers = User.query.filter_by(role='lawyer').all()
    return render_template('add_client.html', form=form, lawyers=lawyers)

@app.route('/view_client/<int:client_id>')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def view_client(client_id):
    user = User.query.get(session['user_id'])
    client = Client.query.get_or_404(client_id)
    
    # Check if user has permission to view this client
    if user.role != 'admin' and client.assigned_lawyer_id != user.id:
        flash('You do not have permission to view this client.', 'danger')
        return redirect(url_for('clients'))
    
    # Get client cases
    cases = Case.query.filter_by(client_id=client_id).all()
    
    # Get client communications
    communications = Communication.query.filter_by(client_id=client_id).order_by(Communication.communication_date.desc()).limit(10).all()
    
    # Get client invoices
    invoices = Invoice.query.filter_by(client_id=client_id).all()
    
    # Get client appointments
    appointments = Appointment.query.filter_by(client_id=client_id).order_by(Appointment.start_time.desc()).limit(5).all()
    
    return render_template('view_client.html', 
                         client=client, 
                         cases=cases, 
                         communications=communications,
                         invoices=invoices,
                         appointments=appointments)

@app.route('/edit_client/<int:client_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def edit_client(client_id):
    user = User.query.get(session['user_id'])
    client = Client.query.get_or_404(client_id)
    
    # Check if user has permission to edit this client
    if user.role != 'admin' and client.assigned_lawyer_id != user.id:
        flash('You do not have permission to edit this client.', 'danger')
        return redirect(url_for('clients'))
    
    if request.method == 'POST':
        client.first_name = request.form.get('first_name')
        client.last_name = request.form.get('last_name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.city = request.form.get('city')
        client.state = request.form.get('state')
        client.postal_code = request.form.get('postal_code')
        client.company = request.form.get('company')
        client.client_type = request.form.get('client_type')
        client.practice_area = request.form.get('practice_area')
        client.priority = request.form.get('priority')
        client.assigned_lawyer_id = request.form.get('assigned_lawyer_id')
        client.notes = request.form.get('notes')
        
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'update_client', 'client', client.id, f'Updated client: {client.full_name}')
        
        flash('Client updated successfully!', 'success')
        return redirect(url_for('view_client', client_id=client_id))
    
    lawyers = User.query.filter_by(role='lawyer').all()
    return render_template('edit_client.html', client=client, lawyers=lawyers)

# Case Management Routes (Step 3)
@app.route('/cases')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def cases():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        cases = Case.query.all()
    else:
        cases = Case.query.filter_by(assigned_lawyer_id=user.id).all()
    return render_template('cases.html', cases=cases)

@app.route('/add_case', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def add_case():
    form = CaseForm()
    form.client_id.choices = [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
    form.assigned_lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Generate case number
            last_case = Case.query.order_by(Case.id.desc()).first()
            if last_case:
                case_num = int(last_case.case_number.split('-')[2]) + 1
            else:
                case_num = 1
            
            case_number = f"CASE-2023-{case_num:03d}"
            
            case = Case(
                case_number=case_number,
                title=form.title.data,
                description=form.description.data,
                client_id=form.client_id.data,
                assigned_lawyer_id=form.assigned_lawyer_id.data or session['user_id'],
                case_type=form.case_type.data,
                status=form.status.data,
                stage=form.stage.data,
                date_opened=form.date_opened.data,
                estimated_completion=form.estimated_completion.data,
                billing_method=form.billing_method.data,
                hourly_rate=form.hourly_rate.data,
                budget=form.budget.data,
                court_number=form.court_number.data,
                notes=form.notes.data
            )
            
            db.session.add(case)
            db.session.commit()
            
            # Log activity
            log_activity(session['user_id'], 'create_case', 'case', case.id, f'Created case: {case.title}')
            
            # Create notification for assigned lawyer if different from current user
            if case.assigned_lawyer_id != session['user_id']:
                create_notification(case.assigned_lawyer_id, 'New Case Assigned', 
                                  f'You have been assigned a new case: {case.title}', 'case')
            
            flash('Case added successfully!', 'success')
            return redirect(url_for('cases'))
        else:
            # If form validation fails, repopulate choices
            form.client_id.choices = [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
            form.assigned_lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    clients = Client.query.all()
    lawyers = User.query.filter_by(role='lawyer').all()
    return render_template('add_case.html', form=form, clients=clients, lawyers=lawyers)

@app.route('/view_case/<int:case_id>')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def view_case(case_id):
    user = User.query.get(session['user_id'])
    case = Case.query.get_or_404(case_id)
    
    # Check if user has permission to view this case
    if user.role != 'admin' and case.assigned_lawyer_id != user.id:
        flash('You do not have permission to view this case.', 'danger')
        return redirect(url_for('cases'))
    
    # Get case documents
    documents = Document.query.filter_by(case_id=case_id).all()
    
    # Get case time entries
    time_entries = TimeEntry.query.filter_by(case_id=case_id).order_by(TimeEntry.start_time.desc()).all()
    
    # Calculate total hours and amount from time entries
    total_hours = sum(entry.duration_minutes or 0 for entry in time_entries) / 60
    total_amount = sum(entry.amount or 0 for entry in time_entries)
    
    # Get case appointments
    appointments = Appointment.query.filter_by(case_id=case_id).order_by(Appointment.start_time.desc()).all()
    
    # Get case invoices
    invoices = Invoice.query.filter_by(case_id=case_id).all()
    
    # Get case workflows
    workflows = CaseWorkflow.query.filter_by(case_id=case_id).order_by(CaseWorkflow.stage_order).all()
    
    # Get case communications
    communications = Communication.query.filter_by(case_id=case_id).order_by(Communication.communication_date.desc()).limit(10).all()
    
    return render_template('view_case.html',
                         case=case,
                         documents=documents,
                         time_entries=time_entries,
                         total_hours=total_hours,
                         total_amount=total_amount,
                         appointments=appointments,
                         invoices=invoices,
                         workflows=workflows,
                         communications=communications)

@app.route('/edit_case/<int:case_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def edit_case(case_id):
    user = User.query.get(session['user_id'])
    case = Case.query.get_or_404(case_id)
    
    # Check if user has permission to edit this case
    if user.role != 'admin' and case.assigned_lawyer_id != user.id:
        flash('You do not have permission to edit this case.', 'danger')
        return redirect(url_for('cases'))
    
    if request.method == 'POST':
        case.title = request.form.get('title')
        case.description = request.form.get('description')
        case.client_id = request.form.get('client_id')
        case.assigned_lawyer_id = request.form.get('assigned_lawyer_id')
        case.case_type = request.form.get('case_type')
        case.status = request.form.get('status')
        case.stage = request.form.get('stage')
        case.estimated_completion = datetime.strptime(request.form.get('estimated_completion'), '%Y-%m-%d') if request.form.get('estimated_completion') else None
        case.billing_method = request.form.get('billing_method')
        case.hourly_rate = float(request.form.get('hourly_rate')) if request.form.get('hourly_rate') else None
        case.budget = float(request.form.get('budget')) if request.form.get('budget') else None
        case.notes = request.form.get('notes')
        
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'update_case', 'case', case.id, f'Updated case: {case.title}')
        
        flash('Case updated successfully!', 'success')
        return redirect(url_for('view_case', case_id=case_id))
    
    clients = Client.query.all()
    lawyers = User.query.filter_by(role='lawyer').all()
    return render_template('edit_case.html', case=case, clients=clients, lawyers=lawyers)

@app.route('/delete_case/<int:case_id>', methods=['POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def delete_case(case_id):
    user = User.query.get(session['user_id'])
    case = Case.query.get_or_404(case_id)
    
    # Check if user has permission to delete this case
    if user.role != 'admin' and case.assigned_lawyer_id != user.id:
        flash('You do not have permission to delete this case.', 'danger')
        return redirect(url_for('cases'))
    
    # Log activity before deletion
    log_activity(session['user_id'], 'delete_case', 'case', case.id, f'Deleted case: {case.title}')
    
    # Delete the case
    db.session.delete(case)
    db.session.commit()
    
    flash('Case deleted successfully!', 'success')
    return redirect(url_for('cases'))

# Appointment Management Routes (Step 4)
@app.route('/appointments')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def appointments():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        appointments = Appointment.query.all()
    else:
        appointments = Appointment.query.filter_by(lawyer_id=user.id).all()
    return render_template('appointments.html', appointments=appointments)

@app.route('/add_appointment', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def add_appointment():
    form = AppointmentForm()
    form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
    form.lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    form.case_id.choices = [(0, 'Select Case')] + [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            appointment = Appointment(
                title=form.title.data,
                description=form.description.data,
                client_id=form.client_id.data,
                lawyer_id=form.lawyer_id.data or session['user_id'],
                case_id=form.case_id.data,
                appointment_type=form.appointment_type.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                location=form.location.data,
                is_virtual=form.is_virtual.data,
                meeting_link=form.meeting_link.data,
                notes=form.notes.data
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            # Log activity
            log_activity(session['user_id'], 'create_appointment', 'appointment', appointment.id, f'Created appointment: {appointment.title}')
            
            # Create notification for assigned lawyer if different from current user
            if appointment.lawyer_id != session['user_id']:
                create_notification(appointment.lawyer_id, 'New Appointment Scheduled', 
                                  f'You have a new appointment: {appointment.title} on {appointment.start_time.strftime("%Y-%m-%d %H:%M")}', 'appointment')
            
            # Create notification for client
            if appointment.client_id:
                create_notification(appointment.client_id, 'Appointment Scheduled', 
                                  f'You have an appointment: {appointment.title} on {appointment.start_time.strftime("%Y-%m-%d %H:%M")}', 'appointment')
            
            flash('Appointment scheduled successfully!', 'success')
            return redirect(url_for('appointments'))
        else:
            # If form validation fails, repopulate choices
            form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
            form.lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
            form.case_id.choices = [(0, 'Select Case')] + [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
    
    clients = Client.query.all()
    lawyers = User.query.filter_by(role='lawyer').all()
    cases = Case.query.all()
    return render_template('add_appointment.html', form=form, clients=clients, lawyers=lawyers, cases=cases)

@app.route('/view_appointment/<int:appointment_id>')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def view_appointment(appointment_id):
    user = User.query.get(session['user_id'])
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if user has permission to view this appointment
    if user.role != 'admin' and appointment.lawyer_id != user.id:
        flash('You do not have permission to view this appointment.', 'danger')
        return redirect(url_for('appointments'))
    
    return render_template('view_appointment.html', appointment=appointment)

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def edit_appointment(appointment_id):
    user = User.query.get(session['user_id'])
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if user has permission to edit this appointment
    if user.role != 'admin' and appointment.lawyer_id != user.id:
        flash('You do not have permission to edit this appointment.', 'danger')
        return redirect(url_for('appointments'))
    
    if request.method == 'POST':
        appointment.title = request.form.get('title')
        appointment.description = request.form.get('description')
        appointment.client_id = request.form.get('client_id')
        appointment.lawyer_id = request.form.get('lawyer_id')
        appointment.case_id = request.form.get('case_id')
        appointment.appointment_type = request.form.get('appointment_type')
        appointment.start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        appointment.end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        appointment.location = request.form.get('location')
        appointment.is_virtual = True if request.form.get('is_virtual') else False
        appointment.meeting_link = request.form.get('meeting_link')
        appointment.notes = request.form.get('notes')
        
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'update_appointment', 'appointment', appointment.id, f'Updated appointment: {appointment.title}')
        
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('view_appointment', appointment_id=appointment_id))
    
    clients = Client.query.all()
    lawyers = User.query.filter_by(role='lawyer').all()
    cases = Case.query.all()
    return render_template('edit_appointment.html', appointment=appointment, clients=clients, lawyers=lawyers, cases=cases)

# Document Management Routes (Step 5)
@app.route('/documents')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def documents():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        documents = Document.query.all()
    else:
        documents = Document.query.filter_by(uploaded_by=user.id).all()
    return render_template('documents.html', documents=documents)

@app.route('/upload_document', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def upload_document():
    form = DocumentForm()
    form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
    form.case_id.choices = [(0, 'Select Case')] + [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            file = form.file.data
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                document = Document(
                    title=form.title.data,
                    description=form.description.data,
                    filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    file_type=file.content_type,
                    category=form.category.data,
                    case_id=form.case_id.data,
                    client_id=form.client_id.data,
                    uploaded_by=session['user_id'],
                    tags=form.tags.data,
                    is_confidential=form.is_confidential.data,
                    requires_signature=form.requires_signature.data
                )
                
                db.session.add(document)
                db.session.commit()
                
                # Process OCR in background if available
                if OCR_AVAILABLE:
                    try:
                        process_document_ocr(document.id)
                        flash('Document uploaded successfully! OCR processing started.', 'success')
                    except Exception as e:
                        app.logger.error(f"OCR processing failed for document {document.id}: {str(e)}")
                        flash('Document uploaded successfully! OCR processing failed.', 'warning')
                else:
                    flash('Document uploaded successfully!', 'success')
                
                # Log activity
                log_activity(session['user_id'], 'upload_document', 'document', document.id, f'Uploaded document: {document.title}')
                
                return redirect(url_for('documents'))
        else:
            # If form validation fails, repopulate choices
            form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
            form.case_id.choices = [(0, 'Select Case')] + [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('upload_document.html', form=form, clients=clients, cases=cases)

@app.route('/view_document/<int:document_id>')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def view_document(document_id):
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to view this document
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to view this document.', 'danger')
        return redirect(url_for('documents'))
    
    # Get document versions
    versions = DocumentVersion.query.filter_by(document_id=document_id).order_by(DocumentVersion.version_number.desc()).all()
    
    # Get document analyses
    analyses = DocumentAnalysis.query.filter_by(document_id=document_id).all()
    analysis_data = {}
    for analysis in analyses:
        try:
            analysis_data[analysis.analysis_type] = json.loads(analysis.analysis_result)
        except:
            analysis_data[analysis.analysis_type] = analysis.analysis_result
    
    return render_template('view_document_enhanced.html', 
                         document=document, 
                         versions=versions,
                         analyses=analyses,
                         analysis_data=analysis_data)

@app.route('/process_ocr/<int:document_id>', methods=['POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def process_ocr(document_id):
    if not OCR_AVAILABLE:
        flash('OCR processing is not available.', 'danger')
        return redirect(url_for('documents.view_document', document_id=document_id))
    
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to process this document
    if user.role != 'admin' and document.uploaded_by != user.id:
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    try:
        process_document_ocr(document_id)
        return jsonify({'success': True, 'message': 'OCR processing completed successfully'})
    except Exception as e:
        app.logger.error(f"Error processing OCR for document {document_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'OCR processing failed: {str(e)}'})

@app.route('/search_document_text', methods=['POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def search_document_text():
    search_query = request.form.get('query')
    document_id = request.form.get('document_id', type=int)
    
    if not search_query or not document_id:
        return jsonify({'results': [], 'message': 'Invalid request'})
    
    # Get documents based on user role
    if session['user_role'] == 'admin':
        documents = Document.query.filter_by(id=document_id).all()
    else:
        documents = Document.query.filter_by(id=document_id, uploaded_by=session['user_id']).all()
    
    results = []
    for doc in documents:
        if doc.ocr_text and search_query.lower() in doc.ocr_text.lower():
            # Find context around the search term
            text = doc.ocr_text
            start_idx = text.lower().find(search_query.lower())
            start = max(0, start_idx - 100)
            end = min(len(text), start_idx + len(search_query) + 100)
            context = text[start:end].replace('\n', ' ')
            
            results.append({
                'document_id': doc.id,
                'document_title': doc.title,
                'context': context,
                'highlight': search_query
            })
    
    return jsonify({'results': results, 'count': len(results)})

@app.route('/download_document/<int:document_id>')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def download_document(document_id):
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to download this document
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to download this document.', 'danger')
        return redirect(url_for('documents'))
    
    # Log activity
    log_activity(session['user_id'], 'download_document', 'document', document.id, f'Downloaded document: {document.title}')
    
    return send_file(document.file_path, as_attachment=True)

# Time Entry Routes (Step 6)
@app.route('/time_entries')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def time_entries():
    user = User.query.get(session['user_id'])
    active_tab = request.args.get('tab', 'time')
    
    # Get filter parameters
    current_case_id = request.args.get('case_id', type=int)
    current_client_id = request.args.get('client_id', type=int)
    current_lawyer_id = request.args.get('lawyer_id', type=int)
    current_status = request.args.get('status')
    current_date_from = request.args.get('date_from')
    current_date_to = request.args.get('date_to')
    
    # Build query for time entries
    query = TimeEntry.query
    
    # Apply filters
    if current_case_id:
        query = query.filter(TimeEntry.case_id == current_case_id)
    if current_date_from:
        query = query.filter(TimeEntry.start_time >= datetime.strptime(current_date_from, '%Y-%m-%d'))
    if current_date_to:
        query = query.filter(TimeEntry.start_time <= datetime.strptime(current_date_to, '%Y-%m-%d'))
    if current_status:
        query = query.filter(TimeEntry.status == current_status)
    
    # Apply role-based filtering
    if user.role == 'admin':
        if current_lawyer_id:
            query = query.filter(TimeEntry.user_id == current_lawyer_id)
        if current_client_id:
            query = query.join(Case).filter(Case.client_id == current_client_id)
        time_entries = query.all()
    else:
        query = query.filter(TimeEntry.user_id == user.id)
        if current_client_id:
            query = query.join(Case).filter(Case.client_id == current_client_id)
        time_entries = query.all()
    
    # Calculate statistics
    total_hours = sum(entry.duration_minutes or 0 for entry in time_entries) / 60
    billable_hours = sum(entry.duration_minutes or 0 for entry in time_entries if entry.is_billable) / 60
    total_amount = sum(entry.amount or 0 for entry in time_entries)
    unbilled_hours = sum(entry.duration_minutes or 0 for entry in time_entries
                        if entry.is_billable and entry.status in ['draft', 'submitted']) / 60
    
    # Get data for filters
    cases = Case.query.all()
    clients = Client.query.all()
    lawyers = User.query.filter_by(role='lawyer').all()
    time_entry_statuses = ['draft', 'submitted', 'approved', 'rejected', 'invoiced']
    
    # Calculate billable/non-billable percentages
    if total_hours > 0:
        billable_percentage = (billable_hours / total_hours) * 100
        non_billable_percentage = ((total_hours - billable_hours) / total_hours) * 100
    else:
        billable_percentage = 0
        non_billable_percentage = 0
    
    # Get top clients by hours
    client_hours = {}
    for entry in time_entries:
        if entry.case and entry.case.client:
            client_id = entry.case.client_id
            client_name = entry.case.client.full_name
            hours = (entry.duration_minutes or 0) / 60
            if client_id not in client_hours:
                client_hours[client_id] = {'name': client_name, 'hours': 0}
            client_hours[client_id]['hours'] += hours
    
    top_clients_by_hours = sorted(
        [(Client.query.get(client_id), data['hours']) for client_id, data in client_hours.items()],
        key=lambda x: x[1], reverse=True
    )[:5]
    
    # Get expenses data for the expense tab
    expenses_query = Expense.query
    
    # Apply expense filters
    expense_case_id = request.args.get('expense_case_id', type=int)
    expense_client_id = request.args.get('expense_client_id', type=int)
    expense_lawyer_id = request.args.get('expense_lawyer_id', type=int)
    expense_status = request.args.get('expense_status')
    expense_date_from = request.args.get('expense_date_from')
    expense_date_to = request.args.get('expense_date_to')
    
    if expense_case_id:
        expenses_query = expenses_query.filter(Expense.case_id == expense_case_id)
    if expense_date_from:
        expenses_query = expenses_query.filter(Expense.date_incurred >= datetime.strptime(expense_date_from, '%Y-%m-%d').date())
    if expense_date_to:
        expenses_query = expenses_query.filter(Expense.date_incurred <= datetime.strptime(expense_date_to, '%Y-%m-%d').date())
    if expense_status:
        expenses_query = expenses_query.filter(Expense.status == expense_status)
    
    # Apply role-based filtering for expenses
    if user.role == 'admin':
        if expense_lawyer_id:
            expenses_query = expenses_query.filter(Expense.user_id == expense_lawyer_id)
        if expense_client_id:
            expenses_query = expenses_query.join(Case).filter(Case.client_id == expense_client_id)
        expenses = expenses_query.all()
    else:
        expenses_query = expenses_query.filter(Expense.user_id == user.id)
        if expense_client_id:
            expenses_query = expenses_query.join(Case).filter(Case.client_id == expense_client_id)
        expenses = expenses_query.all()
    
    # Calculate expense statistics
    total_expenses = sum(expense.amount or 0 for expense in expenses)
    reimbursed_expenses = sum(expense.amount or 0 for expense in expenses if expense.status == 'reimbursed')
    pending_reimbursement = sum(expense.amount or 0 for expense in expenses
                              if expense.is_billable and expense.status in ['pending', 'submitted'])
    
    # Calculate this month's expenses
    current_month = datetime.utcnow().replace(day=1)
    this_month_expenses = sum(expense.amount or 0 for expense in expenses
                             if expense.date_incurred and expense.date_incurred >= current_month.date())
    
    # Get expense statuses for filter
    expense_statuses = ['pending', 'submitted', 'approved', 'rejected', 'reimbursed']
    
    # Get top expense categories
    category_amounts = {}
    for expense in expenses:
        category = expense.expense_type or 'Other'
        amount = expense.amount or 0
        if category not in category_amounts:
            category_amounts[category] = 0
        category_amounts[category] += amount
    
    top_expense_categories = sorted(category_amounts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return render_template('time_entries.html',
                         time_entries=time_entries,
                         expenses=expenses,
                         active_tab=active_tab,
                         total_hours=total_hours,
                         billable_hours=billable_hours,
                         total_amount=total_amount,
                         unbilled_hours=unbilled_hours,
                         billable_percentage=billable_percentage,
                         non_billable_percentage=non_billable_percentage,
                         top_clients_by_hours=top_clients_by_hours,
                         total_expenses=total_expenses,
                         reimbursed_expenses=reimbursed_expenses,
                         pending_reimbursement=pending_reimbursement,
                         this_month_expenses=this_month_expenses,
                         top_expense_categories=top_expense_categories,
                         cases=cases,
                         clients=clients,
                         lawyers=lawyers,
                         time_entry_statuses=time_entry_statuses,
                         expense_statuses=expense_statuses,
                         current_case_id=current_case_id,
                         current_client_id=current_client_id,
                         current_lawyer_id=current_lawyer_id,
                         current_status=current_status,
                         current_date_from=current_date_from,
                         current_date_to=current_date_to,
                         current_expense_case_id=expense_case_id,
                         current_expense_client_id=expense_client_id,
                         current_expense_lawyer_id=expense_lawyer_id,
                         current_expense_status=expense_status,
                         current_expense_date_from=expense_date_from,
                         current_expense_date_to=expense_date_to)

@app.route('/export_time_entries')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def export_time_entries():
    user = User.query.get(session['user_id'])
    
    # Get time entries based on user role
    if user.role == 'admin':
        entries = TimeEntry.query.all()
    else:
        entries = TimeEntry.query.filter_by(user_id=user.id).all()
    
    # Create CSV content
    output = BytesIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Lawyer', 'Client', 'Case', 'Description', 'Duration (minutes)', 'Hourly Rate', 'Amount', 'Status'])
    
    # Write data
    for entry in entries:
        writer.writerow([
            entry.start_time.strftime('%Y-%m-%d') if entry.start_time else '',
            entry.user.full_name if entry.user else '',
            entry.case.client.full_name if entry.case and entry.case.client else '',
            entry.case.title if entry.case else '',
            entry.description or '',
            entry.duration_minutes or 0,
            entry.hourly_rate or 0,
            entry.amount or 0,
            entry.status or ''
        ])
    
    output.seek(0)
    
    # Log activity
    log_activity(session['user_id'], 'export_time_entries', 'time_entry', None, 'Exported time entries')
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'time_entries_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/export_expenses')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def export_expenses():
    user = User.query.get(session['user_id'])
    
    # Get expenses based on user role
    if user.role == 'admin':
        expenses = Expense.query.all()
    else:
        expenses = Expense.query.filter_by(user_id=user.id).all()
    
    # Create CSV content
    output = BytesIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Lawyer', 'Client', 'Case', 'Description', 'Category', 'Amount', 'Status'])
    
    # Write data
    for expense in expenses:
        writer.writerow([
            expense.date_incurred.strftime('%Y-%m-%d') if expense.date_incurred else '',
            expense.user.full_name if expense.user else '',
            expense.case.client.full_name if expense.case and expense.case.client else '',
            expense.case.title if expense.case else '',
            expense.description or '',
            expense.expense_type or '',
            expense.amount or 0,
            expense.status or ''
        ])
    
    output.seek(0)
    
    # Log activity
    log_activity(session['user_id'], 'export_expenses', 'expense', None, 'Exported expenses')
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/export_leads')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def export_leads():
    try:
        user = User.query.get(session['user_id'])
        
        # Get leads based on user role
        if user.role == 'admin':
            leads = Lead.query.all()
        else:
            leads = Lead.query.filter_by(assigned_lawyer_id=user.id).all()
        
        # Create CSV content
        output = BytesIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Lead Number', 'Name', 'Email', 'Phone', 'Company', 'Practice Area', 'Source', 'Priority', 'Status', 'Assigned Lawyer', 'Created Date'])
        
        # Write data
        for lead in leads:
            writer.writerow([
                lead.lead_number or '',
                f"{lead.first_name} {lead.last_name}" if lead.first_name and lead.last_name else '',
                lead.email or '',
                lead.phone or '',
                lead.company or '',
                lead.practice_area or '',
                lead.source or '',
                lead.priority or '',
                lead.status or '',
                lead.assigned_lawyer.full_name if lead.assigned_lawyer else '',
                lead.created_at.strftime('%Y-%m-%d') if lead.created_at else ''
            ])
        
        output.seek(0)
        
        # Log activity
        log_activity(session['user_id'], 'export_leads', 'lead', None, 'Exported leads')
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        app.logger.error(f'Error exporting leads: {str(e)}')
        flash(f'Error exporting leads: {str(e)}', 'danger')
        # Redirect to dashboard if leads route doesn't exist
        return redirect(url_for('dashboard'))

@app.route('/export_invoices')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'finance')
def export_invoices():
    try:
        user = User.query.get(session['user_id'])
        
        # Get invoices based on user role
        if user.role == 'admin':
            invoices = Invoice.query.all()
        else:
            invoices = Invoice.query.join(Case).filter(Case.assigned_lawyer_id == user.id).all()
        
        # Create CSV content
        output = BytesIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Invoice Number', 'Client', 'Case', 'Issue Date', 'Due Date', 'Subtotal', 'Tax', 'Total', 'Status', 'Currency'])
        
        # Write data
        for invoice in invoices:
            writer.writerow([
                invoice.invoice_number or '',
                invoice.client.full_name if invoice.client else '',
                invoice.case.title if invoice.case else '',
                invoice.issue_date.strftime('%Y-%m-%d') if invoice.issue_date else '',
                invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
                invoice.subtotal or 0,
                invoice.tax_amount or 0,
                invoice.total or 0,
                invoice.status or '',
                invoice.currency or ''
            ])
        
        output.seek(0)
        
        # Log activity
        log_activity(session['user_id'], 'export_invoices', 'invoice', None, 'Exported invoices')
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        app.logger.error(f'Error exporting invoices: {str(e)}')
        flash(f'Error exporting invoices: {str(e)}', 'danger')
        # Check if invoices route exists, otherwise redirect to dashboard
        try:
            return redirect(url_for('invoices'))
        except:
            return redirect(url_for('dashboard'))

# Time Report Routes
@app.route('/reports/time/lawyer')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def time_report_by_lawyer():
    # Implementation for time report by lawyer
    return render_template('reports/time_by_lawyer.html')

@app.route('/reports/time/client')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def time_report_by_client():
    # Implementation for time report by client
    return render_template('reports/time_by_client.html')

@app.route('/reports/time/case')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def time_report_by_case():
    # Implementation for time report by case
    return render_template('reports/time_by_case.html')

@app.route('/reports/time/date')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def time_report_by_date():
    # Implementation for time report by date range
    return render_template('reports/time_by_date.html')

@app.route('/reports/utilization')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def utilization_report():
    # Implementation for utilization report
    return render_template('reports/utilization.html')

# Expense Report Routes
@app.route('/reports/expense/lawyer')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def expense_report_by_lawyer():
    # Implementation for expense report by lawyer
    return render_template('reports/expense_by_lawyer.html')

@app.route('/reports/expense/client')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def expense_report_by_client():
    # Implementation for expense report by client
    return render_template('reports/expense_by_client.html')

@app.route('/reports/expense/case')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def expense_report_by_case():
    # Implementation for expense report by case
    return render_template('reports/expense_by_case.html')

@app.route('/reports/expense/category')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def expense_report_by_category():
    # Implementation for expense report by category
    return render_template('reports/expense_by_category.html')

@app.route('/reports/expense/date')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def expense_report_by_date():
    # Implementation for expense report by date range
    return render_template('reports/expense_by_date.html')

@app.route('/add_time_entry', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def add_time_entry():
    form = TimeEntryForm()
    form.case_id.choices = [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
    form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
    form.lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Calculate duration if end time is provided
            duration_minutes = None
            if form.end_time.data:
                duration_minutes = int((form.end_time.data - form.start_time.data).total_seconds() / 60)
            
            time_entry = TimeEntry(
                user_id=session['user_id'],
                case_id=form.case_id.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                duration_minutes=duration_minutes,
                is_billable=form.is_billable.data,
                hourly_rate=form.hourly_rate.data,
                status=form.status.data,
                notes=form.notes.data
            )
            
            # Calculate amount
            time_entry.calculate_amount()
            
            db.session.add(time_entry)
            db.session.commit()
            
            # Log activity
            log_activity(session['user_id'], 'create_time_entry', 'time_entry', time_entry.id, f'Created time entry for case: {time_entry.case.title if time_entry.case else "N/A"}')
            
            flash('Time entry added successfully!', 'success')
            return redirect(url_for('time_entries'))
        else:
            # If form validation fails, repopulate choices
            form.case_id.choices = [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
            form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
            form.lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    cases = Case.query.all()
    return render_template('add_time_entry.html', form=form, cases=cases)

# Expense Tracking Routes (Step 6)
@app.route('/expenses')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def expenses():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        expenses = Expense.query.all()
    else:
        expenses = Expense.query.filter_by(user_id=user.id).all()
    return render_template('expenses.html', expenses=expenses)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def add_expense():
    form = ExpenseForm()
    form.case_id.choices = [(0, 'Select Case')] + [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
    form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
    form.lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            file = form.receipt.data
            receipt_filename = None
            receipt_path = None
            
            if file:
                receipt_filename = secure_filename(file.filename)
                receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], 'receipts', receipt_filename)
                os.makedirs(os.path.dirname(receipt_path), exist_ok=True)
                file.save(receipt_path)
            
            expense = Expense(
                user_id=session['user_id'],
                case_id=form.case_id.data if form.case_id.data != 0 else None,
                expense_type=form.expense_type.data,
                description=form.description.data,
                amount=form.amount.data,
                currency=form.currency.data,
                date_incurred=form.date_incurred.data,
                is_billable=form.is_billable.data,
                receipt_filename=receipt_filename,
                receipt_path=receipt_path,
                status=form.status.data,
                notes=form.notes.data
            )
            
            db.session.add(expense)
            db.session.commit()
            
            # Log activity
            log_activity(session['user_id'], 'create_expense', 'expense', expense.id, f'Created expense: {expense.description}')
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for('expenses'))
        else:
            # If form validation fails, repopulate choices
            form.case_id.choices = [(0, 'Select Case')] + [(case.id, f"{case.title} ({case.case_number})") for case in Case.query.all()]
            form.client_id.choices = [(0, 'Select Client')] + [(client.id, f"{client.full_name} ({client.client_number})") for client in Client.query.all()]
            form.lawyer_id.choices = [(0, 'Select Lawyer')] + [(lawyer.id, lawyer.full_name) for lawyer in User.query.filter_by(role='lawyer').all()]
    
    cases = Case.query.all()
    return render_template('add_expense.html', form=form, cases=cases)

# Invoice Routes (Step 7)
@app.route('/invoices')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'finance')
def invoices():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        invoices = Invoice.query.all()
    else:
        invoices = Invoice.query.join(Case).filter(Case.assigned_lawyer_id == user.id).all()
    return render_template('invoices.html', invoices=invoices)

@app.route('/add_invoice', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'finance')
def add_invoice():
    if request.method == 'POST':
        # Generate invoice number
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            invoice_num = int(last_invoice.invoice_number.split('-')[2]) + 1
        else:
            invoice_num = 1
        
        invoice_number = f"INV-2023-{invoice_num:03d}"
        
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d') if request.form.get('due_date') else None
        
        invoice = Invoice(
            invoice_number=invoice_number,
            client_id=request.form.get('client_id'),
            case_id=request.form.get('case_id'),
            issue_date=datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d'),
            due_date=due_date,
            subtotal=float(request.form.get('subtotal')),
            tax_rate=float(request.form.get('tax_rate')),
            currency=request.form.get('currency'),
            status=request.form.get('status'),
            payment_method=request.form.get('payment_method'),
            notes=request.form.get('notes')
        )
        
        # Calculate tax and total
        invoice.calculate_total()
        
        db.session.add(invoice)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_invoice', 'invoice', invoice.id, f'Created invoice: {invoice.invoice_number}')
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('invoices'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('add_invoice.html', clients=clients, cases=cases)

@app.route('/view_invoice/<int:invoice_id>')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'finance')
def view_invoice(invoice_id):
    user = User.query.get(session['user_id'])
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check if user has permission to view this invoice
    if user.role != 'admin' and invoice.case.assigned_lawyer_id != user.id:
        flash('You do not have permission to view this invoice.', 'danger')
        return redirect(url_for('invoices'))
    
    # Get invoice line items
    line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice_id).all()
    
    # Get invoice payments
    payments = Payment.query.filter_by(invoice_id=invoice_id).all()
    
    return render_template('view_invoice.html', invoice=invoice, line_items=line_items, payments=payments)

@app.route('/add_payment/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'finance')
def add_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if request.method == 'POST':
        payment = Payment(
            invoice_id=invoice_id,
            amount=float(request.form.get('amount')),
            payment_date=datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d'),
            payment_method=request.form.get('payment_method'),
            transaction_id=request.form.get('transaction_id'),
            notes=request.form.get('notes')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Update invoice status if fully paid
        total_paid = sum(p.amount for p in invoice.payments)
        if total_paid >= invoice.total:
            invoice.status = 'paid'
            db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_payment', 'payment', payment.id, f'Added payment of {payment.amount} to invoice {invoice.invoice_number}')
        
        flash('Payment added successfully!', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice_id))
    
    return render_template('add_payment.html', invoice=invoice)

# Trust Account Routes (Step 8)
@app.route('/trust_accounts')
@login_required
@role_required('admin', 'finance')
def trust_accounts():
    trust_accounts = TrustAccount.query.all()
    return render_template('trust_accounts.html', trust_accounts=trust_accounts)

@app.route('/add_trust_account', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'finance')
def add_trust_account():
    if request.method == 'POST':
        # Generate account number
        account_number = f"TRUST-{uuid.uuid4().hex[:8].upper()}"
        
        trust_account = TrustAccount(
            client_id=request.form.get('client_id'),
            account_number=account_number,
            balance=0
        )
        
        db.session.add(trust_account)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_trust_account', 'trust_account', trust_account.id, f'Created trust account for client: {trust_account.client.full_name}')
        
        flash('Trust account created successfully!', 'success')
        return redirect(url_for('trust_accounts'))
    
    clients = Client.query.all()
    return render_template('add_trust_account.html', clients=clients)

@app.route('/view_trust_account/<int:account_id>')
@login_required
@role_required('admin', 'finance')
def view_trust_account(account_id):
    trust_account = TrustAccount.query.get_or_404(account_id)
    
    # Get trust account transactions
    transactions = TrustTransaction.query.filter_by(trust_account_id=account_id).order_by(TrustTransaction.transaction_date.desc()).all()
    
    return render_template('view_trust_account.html', trust_account=trust_account, transactions=transactions)

@app.route('/add_trust_transaction/<int:account_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'finance')
def add_trust_transaction(account_id):
    trust_account = TrustAccount.query.get_or_404(account_id)
    
    if request.method == 'POST':
        transaction = TrustTransaction(
            trust_account_id=account_id,
            transaction_type=request.form.get('transaction_type'),
            amount=float(request.form.get('amount')),
            description=request.form.get('description'),
            transaction_date=datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d')
        )
        
        db.session.add(transaction)
        
        # Update trust account balance
        if transaction.transaction_type == 'deposit':
            trust_account.balance += transaction.amount
        else:  # withdrawal
            trust_account.balance -= transaction.amount
        
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_trust_transaction', 'trust_transaction', transaction.id, f'Added {transaction.transaction_type} of {transaction.amount} to trust account {trust_account.account_number}')
        
        flash('Trust transaction added successfully!', 'success')
        return redirect(url_for('view_trust_account', account_id=account_id))
    
    return render_template('add_trust_transaction.html', trust_account=trust_account)

# Client Portal Routes (Step 9)
@app.route('/client_portal')
@login_required
def client_portal():
    user = User.query.get(session['user_id'])
    
    # Check if user has client portal access
    if user.role not in ['admin', 'lawyer', 'paralegal', 'staff']:
        flash('You do not have permission to access the client portal.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('client_portal.html')

@app.route('/client_portal_login', methods=['GET', 'POST'])
def client_portal_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        client_user = ClientPortalUser.query.filter_by(username=username).first()
        
        if client_user and client_user.check_password(password) and client_user.is_active:
            session['client_user_id'] = client_user.id
            session['client_username'] = client_user.username
            session['client_id'] = client_user.client_id
            
            # Update last login
            client_user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Welcome to the Client Portal!', 'success')
            return redirect(url_for('client_portal_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('client_portal_login.html')

@app.route('/client_portal_dashboard')
@login_required
def client_portal_dashboard():
    if 'client_user_id' not in session:
        return redirect(url_for('client_portal_login'))
    
    client_user = ClientPortalUser.query.get(session['client_user_id'])
    client = client_user.client
    
    # Get client cases
    cases = Case.query.filter_by(client_id=client.id).all()
    
    # Get client appointments
    appointments = Appointment.query.filter_by(client_id=client.id).filter(
        Appointment.start_time >= datetime.utcnow()
    ).order_by(Appointment.start_time).limit(5).all()
    
    # Get client invoices
    invoices = Invoice.query.filter_by(client_id=client.id).filter(
        Invoice.status.in_(['sent', 'overdue'])
    ).all()
    
    # Get client documents
    documents = Document.query.filter_by(client_id=client.id).order_by(Document.created_at.desc()).limit(10).all()
    
    return render_template('client_portal_dashboard.html',
                         client=client,
                         cases=cases,
                         appointments=appointments,
                         invoices=invoices,
                         documents=documents)

@app.route('/client_portal_logout')
def client_portal_logout():
    session.clear()
    flash('You have been logged out of the Client Portal.', 'info')
    return redirect(url_for('client_portal_login'))

@app.route('/add_client_user/<int:client_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def add_client_user(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        client_user = ClientPortalUser(
            client_id=client_id,
            username=request.form.get('username'),
            email=request.form.get('email')
        )
        client_user.set_password(request.form.get('password'))
        
        db.session.add(client_user)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_client_user', 'client_portal_user', client_user.id, f'Created client portal user for client: {client.full_name}')
        
        flash('Client portal user created successfully!', 'success')
        return redirect(url_for('view_client', client_id=client_id))
    
    return render_template('add_client_user.html', client=client)

# Analytics & Reporting Routes (Step 10)
@app.route('/analytics')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def analytics():
    user = User.query.get(session['user_id'])
    
    # Get data based on user role
    if user.role == 'admin':
        # Get case statistics
        case_status_counts = db.session.query(
            Case.status,
            db.func.count(Case.id).label('count')
        ).group_by(Case.status).all()
        
        # Get client statistics
        client_type_counts = db.session.query(
            Client.client_type,
            db.func.count(Client.id).label('count')
        ).group_by(Client.client_type).all()
        
        # Get financial statistics
        total_invoiced = db.session.query(
            db.func.sum(Invoice.total)
        ).filter(Invoice.status.in_(['sent', 'paid', 'overdue'])).scalar() or 0
        
        total_paid = db.session.query(
            db.func.sum(Payment.amount)
        ).scalar() or 0
        
        # Get practice area statistics
        practice_area_counts = db.session.query(
            Client.practice_area,
            db.func.count(Client.id).label('count')
        ).filter(Client.practice_area.isnot(None)).group_by(Client.practice_area).all()
        
        # Get monthly revenue for the past year
        monthly_revenue = []
        for i in range(12):
            month = (datetime.now().replace(day=1) - timedelta(days=30 * i)).strftime('%Y-%m')
            revenue = db.session.query(
                db.func.sum(Payment.amount)
            ).filter(
                db.func.strftime('%Y-%m', Payment.payment_date) == month
            ).scalar() or 0
            
            monthly_revenue.append({
                'month': month,
                'revenue': revenue
            })
        
        monthly_revenue.reverse()
        
        # Get top lawyers by cases
        top_lawyers = db.session.query(
            User.full_name,
            db.func.count(Case.id).label('case_count')
        ).join(Case).group_by(User.id).order_by(db.func.count(Case.id).desc()).limit(5).all()
        
        # Get top clients by revenue
        top_clients = db.session.query(
            Client.full_name,
            db.func.sum(Invoice.total).label('revenue')
        ).join(Invoice).group_by(Client.id).order_by(db.func.sum(Invoice.total).desc()).limit(5).all()
        
    else:
        # Lawyer-specific data
        case_status_counts = db.session.query(
            Case.status,
            db.func.count(Case.id).label('count')
        ).filter(Case.assigned_lawyer_id == user.id).group_by(Case.status).all()
        
        client_type_counts = db.session.query(
            Client.client_type,
            db.func.count(Client.id).label('count')
        ).filter(Client.assigned_lawyer_id == user.id).group_by(Client.client_type).all()
        
        total_invoiced = db.session.query(
            db.func.sum(Invoice.total)
        ).join(Case).filter(
            Case.assigned_lawyer_id == user.id,
            Invoice.status.in_(['sent', 'paid', 'overdue'])
        ).scalar() or 0
        
        total_paid = db.session.query(
            db.func.sum(Payment.amount)
        ).join(Invoice).join(Case).filter(
            Case.assigned_lawyer_id == user.id
        ).scalar() or 0
        
        practice_area_counts = db.session.query(
            Client.practice_area,
            db.func.count(Client.id).label('count')
        ).filter(
            Client.assigned_lawyer_id == user.id,
            Client.practice_area.isnot(None)
        ).group_by(Client.practice_area).all()
        
        # Get monthly revenue for the past year
        monthly_revenue = []
        for i in range(12):
            month = (datetime.now().replace(day=1) - timedelta(days=30 * i)).strftime('%Y-%m')
            revenue = db.session.query(
                db.func.sum(Payment.amount)
            ).join(Invoice).join(Case).filter(
                Case.assigned_lawyer_id == user.id,
                db.func.strftime('%Y-%m', Payment.payment_date) == month
            ).scalar() or 0
            
            monthly_revenue.append({
                'month': month,
                'revenue': revenue
            })
        
        monthly_revenue.reverse()
        
        # Get top clients by revenue
        top_clients = db.session.query(
            Client.full_name,
            db.func.sum(Invoice.total).label('revenue')
        ).join(Invoice).join(Case).filter(
            Case.assigned_lawyer_id == user.id
        ).group_by(Client.id).order_by(db.func.sum(Invoice.total).desc()).limit(5).all()
        
        top_lawyers = []  # Not relevant for non-admin users
    
    return render_template('analytics.html',
                         user=user,
                         case_status_counts=case_status_counts,
                         client_type_counts=client_type_counts,
                         total_invoiced=total_invoiced,
                         total_paid=total_paid,
                         practice_area_counts=practice_area_counts,
                         monthly_revenue=monthly_revenue,
                         top_lawyers=top_lawyers,
                         top_clients=top_clients)

# AI & Automation Tools Routes (Step 11)
@app.route('/ai_tools')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def ai_tools():
    return render_template('ai_tools.html')

@app.route('/analyze_document/<int:document_id>', methods=['POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def analyze_document(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to analyze this document
    user = User.query.get(session['user_id'])
    if user.role != 'admin' and document.uploaded_by != user.id:
        return jsonify({'success': False, 'message': 'You do not have permission to analyze this document.'})
    
    # In a real implementation, this would call an AI service
    # For now, we'll simulate the analysis
    
    # Create document analysis record
    analysis = DocumentAnalysis(
        document_id=document_id,
        analysis_type='summary',
        analysis_result='This is a simulated summary of the document content.',
        confidence_score=0.85
    )
    
    db.session.add(analysis)
    db.session.commit()
    
    # Log activity
    log_activity(session['user_id'], 'analyze_document', 'document', document_id, f'Analyzed document: {document.title}')
    
    return jsonify({'success': True, 'message': 'Document analysis completed.'})

@app.route('/legal_research', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def legal_research():
    if request.method == 'POST':
        query = request.form.get('query')
        case_id = request.form.get('case_id')
        
        # In a real implementation, this would call an AI legal research service
        # For now, we'll simulate the research
        
        research = LegalResearch(
            query=query,
            case_id=case_id if case_id else None,
            user_id=session['user_id'],
            search_results='[]',  # JSON string of results
            relevant_cases='[]',  # JSON string of relevant case law
            summary='This is a simulated summary of the legal research results.'
        )
        
        db.session.add(research)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'legal_research', 'legal_research', research.id, f'Performed legal research: {query[:50]}')
        
        flash('Legal research completed!', 'success')
        return redirect(url_for('legal_research'))
    
    cases = Case.query.all()
    return render_template('legal_research.html', cases=cases)

@app.route('/automation_rules')
@login_required
@role_required('admin')
def automation_rules():
    rules = AutomationRule.query.all()
    return render_template('automation_rules.html', rules=rules)

@app.route('/add_automation_rule', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_automation_rule():
    if request.method == 'POST':
        rule = AutomationRule(
            name=request.form.get('name'),
            description=request.form.get('description'),
            trigger_event=request.form.get('trigger_event'),
            trigger_conditions=request.form.get('trigger_conditions'),
            actions=request.form.get('actions'),
            created_by=session['user_id']
        )
        
        db.session.add(rule)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_automation_rule', 'automation_rule', rule.id, f'Created automation rule: {rule.name}')
        
        flash('Automation rule created successfully!', 'success')
        return redirect(url_for('automation_rules'))
    
    return render_template('add_automation_rule.html')

# Security & Compliance Routes (Step 12)
@app.route('/security')
@login_required
@role_required('admin')
def security():
    return render_template('security.html')

@app.route('/activity_logs')
@login_required
@role_required('admin')
def activity_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get filter parameters
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action')
    resource_type = request.args.get('resource_type')
    
    # Build query
    query = ActivityLog.query
    
    # Apply filters
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if action:
        query = query.filter(ActivityLog.action == action)
    if resource_type:
        query = query.filter(ActivityLog.resource_type == resource_type)
    
    # Get paginated results
    logs = query.order_by(ActivityLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    users = User.query.filter_by(is_active=True).all()
    actions = db.session.query(ActivityLog.action).distinct().all()
    actions = [action[0] for action in actions if action[0]]
    resource_types = db.session.query(ActivityLog.resource_type).distinct().all()
    resource_types = [rt[0] for rt in resource_types if rt[0]]
    
    return render_template('activity_logs.html', 
                         logs=logs, 
                         users=users,
                         actions=actions,
                         resource_types=resource_types,
                         current_user_id=user_id,
                         current_action=action,
                         current_resource_type=resource_type)

@app.route('/permissions')
@login_required
@role_required('admin')
def permissions():
    permissions = Permission.query.all()
    role_permissions = RolePermission.query.all()
    
    # Group permissions by module
    modules = {}
    for permission in permissions:
        if permission.module not in modules:
            modules[permission.module] = []
        modules[permission.module].append(permission)
    
    return render_template('permissions.html',
                         permissions=permissions,
                         role_permissions=role_permissions,
                         modules=modules)

@app.route('/role_permissions')
@login_required
@role_required('admin')
def role_permissions():
    permissions = Permission.query.all()
    role_permissions = RolePermission.query.all()
    
    # Group permissions by module
    modules = {}
    for permission in permissions:
        if permission.module not in modules:
            modules[permission.module] = []
        modules[permission.module].append(permission)
    
    return render_template('role_permissions.html',
                         permissions=permissions,
                         role_permissions=role_permissions,
                         permission_groups=modules)

@app.route('/update_role_permissions', methods=['POST'])
@login_required
@role_required('admin')
def update_role_permissions():
    role = request.form.get('role')
    permission_ids = request.form.getlist('permission_ids')
    
    # Remove existing permissions for this role
    RolePermission.query.filter_by(role=role).delete()
    
    # Add new permissions
    for permission_id in permission_ids:
        role_permission = RolePermission(
            role=role,
            permission_id=permission_id
        )
        db.session.add(role_permission)
    
    db.session.commit()
    
    # Log activity
    log_activity(session['user_id'], 'update_role_permissions', 'role_permission', None, f'Updated permissions for role: {role}')
    
    flash('Role permissions updated successfully!', 'success')
    return redirect(url_for('permissions'))

# Integration Routes (Step 13)
@app.route('/integrations')
@login_required
@role_required('admin')
def integrations():
    return render_template('integrations.html')

@app.route('/update_integration_settings', methods=['POST'])
@login_required
@role_required('admin')
def update_integration_settings():
    # Update integration settings based on form data
    for key, value in request.form.items():
        if key.startswith('integration_'):
            setting_key = key.replace('integration_', '')
            setting = SystemSetting.query.filter_by(key=setting_key).first()
            
            if setting:
                setting.value = value
                db.session.commit()
            else:
                setting = SystemSetting(
                    key=setting_key,
                    value=value,
                    description=f'Integration setting for {setting_key}'
                )
                db.session.add(setting)
                db.session.commit()
    
    # Log activity
    log_activity(session['user_id'], 'update_integration_settings', 'system_setting', None, 'Updated integration settings')
    
    flash('Integration settings updated successfully!', 'success')
    return redirect(url_for('integrations'))

# Mobile App Routes (Step 14)
@app.route('/mobile_app_settings')
@login_required
@role_required('admin')
def mobile_app_settings():
    return render_template('mobile_app_settings.html')

@app.route('/mobile_app_analytics')
@login_required
@role_required('admin')
def mobile_app_analytics():
    return render_template('mobile_app_analytics.html')

# White-Label & Customization Routes (Step 15)
@app.route('/white_label_customization')
@login_required
@role_required('admin')
def white_label_customization():
    firm = Firm.query.first()
    return render_template('white_label_customization.html', firm=firm)

@app.route('/update_firm_settings', methods=['POST'])
@login_required
@role_required('admin')
def update_firm_settings():
    firm = Firm.query.first()
    
    if not firm:
        firm = Firm()
        db.session.add(firm)
    
    firm.name = request.form.get('name')
    firm.firm_code = request.form.get('firm_code')
    firm.subdomain = request.form.get('subdomain')
    firm.address = request.form.get('address')
    firm.phone = request.form.get('phone')
    firm.email = request.form.get('email')
    firm.website = request.form.get('website')
    firm.gst_number = request.form.get('gst_number')
    firm.pan_number = request.form.get('pan_number')
    firm.primary_color = request.form.get('primary_color', '#007bff')
    firm.secondary_color = request.form.get('secondary_color', '#6c757d')
    
    # Handle logo upload
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', filename)
            os.makedirs(os.path.dirname(logo_path), exist_ok=True)
            logo_file.save(logo_path)
            firm.logo_url = logo_path
    
    db.session.commit()
    
    # Log activity
    log_activity(session['user_id'], 'update_firm_settings', 'firm', firm.id, f'Updated firm settings')
    
    flash('Firm settings updated successfully!', 'success')
    return redirect(url_for('white_label_customization'))

@app.route('/preview_customization')
@login_required
@role_required('admin')
def preview_customization():
    firm = Firm.query.first()
    return render_template('preview_customization.html', firm=firm)

# Notifications & Workflow Automation Routes (Step 16)
@app.route('/notifications_workflow')
@login_required
@role_required('admin')
def notifications_workflow():
    return render_template('notifications_workflow.html')

@app.route('/notification_templates')
@login_required
@role_required('admin')
def notification_templates():
    templates = SystemSetting.query.filter(SystemSetting.key.like('notification_template_%')).all()
    return render_template('notification_templates.html', templates=templates)

@app.route('/add_notification_template', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_notification_template():
    if request.method == 'POST':
        template_key = f"notification_template_{request.form.get('template_type')}"
        
        setting = SystemSetting(
            key=template_key,
            value=json.dumps({
                'subject': request.form.get('subject'),
                'body': request.form.get('body')
            }),
            description=f'Notification template for {request.form.get("template_type")}',
            data_type='json'
        )
        
        db.session.add(setting)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_notification_template', 'system_setting', setting.id, f'Created notification template: {template_key}')
        
        flash('Notification template created successfully!', 'success')
        return redirect(url_for('notification_templates'))
    
    return render_template('add_notification_template.html')

@app.route('/workflow_rules')
@login_required
@role_required('admin')
def workflow_rules():
    rules = AutomationRule.query.filter(AutomationRule.trigger_event.like('case_%')).all()
    return render_template('workflow_rules.html', rules=rules)

@app.route('/add_workflow_rule', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_workflow_rule():
    if request.method == 'POST':
        rule = AutomationRule(
            name=request.form.get('name'),
            description=request.form.get('description'),
            trigger_event=request.form.get('trigger_event'),
            trigger_conditions=request.form.get('trigger_conditions'),
            actions=request.form.get('actions'),
            created_by=session['user_id']
        )
        
        db.session.add(rule)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_workflow_rule', 'automation_rule', rule.id, f'Created workflow rule: {rule.name}')
        
        flash('Workflow rule created successfully!', 'success')
        return redirect(url_for('workflow_rules'))
    
    return render_template('add_workflow_rule.html')

# Reporting & Compliance Routes (Step 17)
@app.route('/reports_compliance')
@login_required
@role_required('admin')
def reports_compliance():
    active_tab = request.args.get('tab', 'reports')
    
    # Prepare data for the template
    # Placeholder data for compliance statistics
    compliance_stats = {
        'overall_compliance': 85.5,
        'completed_tasks': 42,
        'total_tasks': 50,
        'pending_reviews': 8,
        'violations': 2
    }
    
    # Placeholder data for compliance trend chart
    compliance_trend_chart = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'data': [82, 84, 83, 85, 86, 85.5]
    }
    
    # Placeholder data for compliance by category chart
    compliance_by_category_chart = {
        'labels': ['Documentation', 'Security', 'Financial', 'Operational'],
        'data': [90, 85, 88, 80]
    }
    
    # Placeholder data for compliance requirements
    compliance_requirements = []
    
    # Placeholder data for audit logs
    audit_logs = []
    
    # Placeholder data for retention policies
    retention_policies = []
    
    # Placeholder data for upcoming retention actions
    upcoming_retention_actions = []
    
    # Placeholder data for standard reports
    standard_reports = {
        'Financial': [
            {'id': 1, 'name': 'Monthly Revenue Report', 'description': 'Monthly revenue breakdown by client and case', 'frequency': 'Monthly'},
            {'id': 2, 'name': 'Expense Analysis', 'description': 'Detailed expense analysis by category', 'frequency': 'Monthly'}
        ],
        'Case Management': [
            {'id': 3, 'name': 'Case Status Report', 'description': 'Current status of all active cases', 'frequency': 'Weekly'},
            {'id': 4, 'name': 'Lawyer Utilization', 'description': 'Billable hours and utilization rates', 'frequency': 'Monthly'}
        ]
    }
    
    # Placeholder data for scheduled reports
    scheduled_reports = []
    
    # Placeholder data for report history
    report_history = []
    
    return render_template('reports_compliance.html',
                         active_tab=active_tab,
                         compliance_stats=compliance_stats,
                         compliance_trend_chart=compliance_trend_chart,
                         compliance_by_category_chart=compliance_by_category_chart,
                         compliance_requirements=compliance_requirements,
                         audit_logs=audit_logs,
                         retention_policies=retention_policies,
                         upcoming_retention_actions=upcoming_retention_actions,
                         standard_reports=standard_reports,
                         scheduled_reports=scheduled_reports,
                         report_history=report_history)


@app.route('/generate_custom_report', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def generate_custom_report():
    if request.method == 'POST':
        # In a real implementation, this would generate a custom report
        # For now, we'll simulate the report generation
        
        flash('Custom report generated successfully!', 'success')
        return redirect(url_for('reports_compliance', tab='reports'))
    
    return render_template('generate_custom_report.html')

@app.route('/report_templates')
@login_required
@role_required('admin')
def report_templates():
    # In a real implementation, this would fetch report templates from the database
    # For now, we'll use placeholder data
    templates = []
    return render_template('report_templates.html', templates=templates)

@app.route('/export_all_reports')
@login_required
@role_required('admin')
def export_all_reports():
    # In a real implementation, this would export all reports
    flash('All reports exported successfully!', 'success')
    return redirect(url_for('reports_compliance', tab='reports'))

@app.route('/add_scheduled_report', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_scheduled_report():
    if request.method == 'POST':
        # In a real implementation, this would add a scheduled report
        flash('Scheduled report added successfully!', 'success')
        return redirect(url_for('reports_compliance', tab='reports'))
    
    return render_template('add_scheduled_report.html')

@app.route('/export_scheduled_reports')
@login_required
@role_required('admin')
def export_scheduled_reports():
    # In a real implementation, this would export scheduled reports
    flash('Scheduled reports exported successfully!', 'success')
    return redirect(url_for('reports_compliance', tab='reports'))

@app.route('/compliance_requirements')
@login_required
@role_required('admin')
def compliance_requirements():
    # In a real implementation, this would fetch compliance requirements from the database
    # For now, we'll use placeholder data
    requirements = []
    return render_template('compliance_requirements.html', requirements=requirements)

@app.route('/add_compliance_requirement', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_compliance_requirement():
    if request.method == 'POST':
        # In a real implementation, this would add a compliance requirement
        flash('Compliance requirement added successfully!', 'success')
        return redirect(url_for('reports_compliance', tab='compliance'))
    
    return render_template('add_compliance_requirement.html')

@app.route('/import_compliance_requirements', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def import_compliance_requirements():
    if request.method == 'POST':
        # In a real implementation, this would import compliance requirements
        flash('Compliance requirements imported successfully!', 'success')
        return redirect(url_for('reports_compliance', tab='compliance'))
    
    return render_template('import_compliance_requirements.html')

@app.route('/export_compliance_requirements')
@login_required
@role_required('admin')
def export_compliance_requirements():
    # In a real implementation, this would export compliance requirements
    flash('Compliance requirements exported successfully!', 'success')
    return redirect(url_for('reports_compliance', tab='compliance'))

@app.route('/run_audit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def run_audit():
    if request.method == 'POST':
        # In a real implementation, this would run an audit
        flash('Audit completed successfully!', 'success')
        return redirect(url_for('reports_compliance', tab='audits'))
    
    return render_template('run_audit.html')

@app.route('/export_audit_logs')
@login_required
@role_required('admin')
def export_audit_logs():
    # In a real implementation, this would export audit logs
    flash('Audit logs exported successfully!', 'success')
    return redirect(url_for('reports_compliance', tab='audits'))

@app.route('/retention_policies')
@login_required
@role_required('admin')
def retention_policies():
    # In a real implementation, this would fetch retention policies from the database
    # For now, we'll use placeholder data
    policies = []
    return render_template('retention_policies.html', policies=policies)

@app.route('/add_retention_policy', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_retention_policy():
    if request.method == 'POST':
        # In a real implementation, this would add a retention policy
        flash('Retention policy added successfully!', 'success')
        return redirect(url_for('reports_compliance', tab='document_retention'))
    
    return render_template('add_retention_policy.html')

@app.route('/export_retention_policies')
@login_required
@role_required('admin')
def export_retention_policies():
    # In a real implementation, this would export retention policies
    flash('Retention policies exported successfully!', 'success')
    return redirect(url_for('reports_compliance', tab='document_retention'))

# Onboarding & Support Routes (Step 18)
@app.route('/onboarding_support')
@login_required
@role_required('admin')
def onboarding_support():
    active_tab = request.args.get('tab', 'onboarding')
    return render_template('onboarding_support.html', active_tab=active_tab)

@app.route('/knowledge_base')
@login_required
def knowledge_base():
    search_query = request.args.get('q', '')
    
    # In a real implementation, this would fetch knowledge base articles from the database
    # For now, we'll use placeholder data
    categories = []
    popular_articles = []
    recent_articles = []
    search_results = []
    faqs = []
    
    return render_template('knowledge_base.html',
                         search_query=search_query,
                         categories=categories,
                         popular_articles=popular_articles,
                         recent_articles=recent_articles,
                         search_results=search_results,
                         faqs=faqs)

# Enterprise Features Routes (Step 19)
@app.route('/enterprise_features')
@login_required
@role_required('admin')
def enterprise_features():
    active_tab = request.args.get('tab', 'api_management')
    return render_template('enterprise_features.html', active_tab=active_tab)

@app.route('/add_api_key', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_api_key():
    if request.method == 'POST':
        # Generate API key
        api_key = f"lfms_{uuid.uuid4().hex}"
        
        # In a real implementation, this would save the API key to the database
        # For now, we'll simulate the API key creation
        
        flash('API key generated successfully!', 'success')
        return redirect(url_for('enterprise_features', tab='api_management'))
    
    return render_template('add_api_key.html')

@app.route('/sso_settings', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def sso_settings():
    if request.method == 'POST':
        # Update SSO settings based on form data
        for key, value in request.form.items():
            if key.startswith('sso_'):
                setting_key = key.replace('sso_', '')
                setting = SystemSetting.query.filter_by(key=setting_key).first()
                
                if setting:
                    setting.value = value
                    db.session.commit()
                else:
                    setting = SystemSetting(
                        key=setting_key,
                        value=value,
                        description=f'SSO setting for {setting_key}'
                    )
                    db.session.add(setting)
                    db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'update_sso_settings', 'system_setting', None, 'Updated SSO settings')
        
        flash('SSO settings updated successfully!', 'success')
        return redirect(url_for('enterprise_features', tab='sso_integration'))
    
    return render_template('sso_settings.html')

@app.route('/add_tenant', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_tenant():
    if request.method == 'POST':
        # In a real implementation, this would create a new tenant
        # For now, we'll simulate the tenant creation
        
        flash('Tenant created successfully!', 'success')
        return redirect(url_for('enterprise_features', tab='multi_tenancy'))
    
    return render_template('add_tenant.html')

# Premium Add-ons Routes (Step 20)
@app.route('/premium_addons')
@login_required
@role_required('admin')
def premium_addons():
    # In a real implementation, this would fetch premium add-ons from the database
    # For now, we'll use placeholder data
    available_addons = []
    active_addons = []
    addon_categories = []
    premium_addons_stats = {
        'active_addons': 0,
        'monthly_cost': 0,
        'available_addons': 0,
        'trial_days': 14
    }
    
    return render_template('premium_addons.html',
                         available_addons=available_addons,
                         active_addons=active_addons,
                         addon_categories=addon_categories,
                         premium_addons_stats=premium_addons_stats)

# Lead Management Routes
@app.route('/leads')
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def leads():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        leads = Lead.query.all()
    else:
        leads = Lead.query.filter_by(assigned_lawyer_id=user.id).all()
    return render_template('leads.html', leads=leads)

@app.route('/add_lead', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def add_lead():
    if request.method == 'POST':
        # Generate lead number
        last_lead = Lead.query.order_by(Lead.id.desc()).first()
        if last_lead:
            lead_num = int(last_lead.lead_number.split('-')[2]) + 1
        else:
            lead_num = 1
        
        lead_number = f"LD-2023-{lead_num:03d}"
        
        lead = Lead(
            lead_number=lead_number,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            company=request.form.get('company'),
            practice_area=request.form.get('practice_area'),
            case_description=request.form.get('case_description'),
            source=request.form.get('source'),
            priority=request.form.get('priority'),
            assigned_lawyer_id=request.form.get('assigned_lawyer_id') or session['user_id'],
            notes=request.form.get('notes')
        )
        
        db.session.add(lead)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_lead', 'lead', lead.id, f'Created lead: {lead.full_name}')
        
        # Create notification for assigned lawyer if different from current user
        if lead.assigned_lawyer_id != session['user_id']:
            create_notification(lead.assigned_lawyer_id, 'New Lead Assigned', 
                              f'You have been assigned a new lead: {lead.full_name}', 'lead')
        
        flash('Lead added successfully!', 'success')
        return redirect(url_for('leads'))
    
    lawyers = User.query.filter_by(role='lawyer').all()
    return render_template('add_lead.html', lawyers=lawyers)

@app.route('/convert_lead_to_client/<int:lead_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal')
def convert_lead_to_client(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    
    # Check if user has permission to convert this lead
    user = User.query.get(session['user_id'])
    if user.role != 'admin' and lead.assigned_lawyer_id != user.id:
        flash('You do not have permission to convert this lead.', 'danger')
        return redirect(url_for('leads'))
    
    if request.method == 'POST':
        # Generate client number
        last_client = Client.query.order_by(Client.id.desc()).first()
        if last_client:
            client_num = int(last_client.client_number.split('-')[2]) + 1
        else:
            client_num = 1
        
        client_number = f"CL-2023-{client_num:03d}"
        
        client = Client(
            client_number=client_number,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            client_type='individual',
            practice_area=lead.practice_area,
            priority=lead.priority,
            assigned_lawyer_id=lead.assigned_lawyer_id,
            notes=request.form.get('notes')
        )
        
        db.session.add(client)
        db.session.commit()
        
        # Update lead
        lead.converted_to_client = True
        lead.converted_client_id = client.id
        lead.status = 'converted'
        
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'convert_lead_to_client', 'lead', lead.id, f'Converted lead to client: {client.full_name}')
        
        flash('Lead converted to client successfully!', 'success')
        return redirect(url_for('view_client', client_id=client.id))
    
    return render_template('convert_lead_to_client.html', lead=lead)

# Communications Routes
@app.route('/communications')
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def communications():
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        communications = Communication.query.all()
    else:
        communications = Communication.query.filter_by(user_id=user.id).all()
    return render_template('communications.html', communications=communications)

@app.route('/add_communication', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'lawyer', 'paralegal', 'staff')
def add_communication():
    if request.method == 'POST':
        communication_date = datetime.strptime(request.form.get('communication_date'), '%Y-%m-%d') if request.form.get('communication_date') else datetime.utcnow()
        
        communication = Communication(
            client_id=request.form.get('client_id'),
            case_id=request.form.get('case_id'),
            user_id=session['user_id'],
            communication_type=request.form.get('communication_type'),
            subject=request.form.get('subject'),
            message=request.form.get('message'),
            direction=request.form.get('direction'),
            duration_minutes=int(request.form.get('duration_minutes')) if request.form.get('duration_minutes') else None,
            is_billable=True if request.form.get('is_billable') else False,
            communication_date=communication_date
        )
        
        db.session.add(communication)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_communication', 'communication', communication.id, f'Recorded communication with client: {communication.client.full_name}')
        
        flash('Communication recorded successfully!', 'success')
        return redirect(url_for('communications'))
    
    clients = Client.query.all()
    cases = Case.query.all()
    return render_template('add_communication.html', clients=clients, cases=cases)

# Firms & Branches Routes
@app.route('/firms')
@login_required
@role_required('admin')
def firms():
    firms = Firm.query.all()
    return render_template('firms.html', firms=firms)

@app.route('/add_firm', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_firm():
    if request.method == 'POST':
        firm = Firm(
            name=request.form.get('name'),
            firm_code=request.form.get('firm_code'),
            subdomain=request.form.get('subdomain'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            website=request.form.get('website'),
            gst_number=request.form.get('gst_number'),
            pan_number=request.form.get('pan_number')
        )
        
        db.session.add(firm)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_firm', 'firm', firm.id, f'Created firm: {firm.name}')
        
        flash('Firm created successfully!', 'success')
        return redirect(url_for('firms'))
    
    return render_template('add_firm.html')

@app.route('/branches')
@login_required
@role_required('admin')
def branches():
    branches = Branch.query.all()
    return render_template('branches.html', branches=branches)

@app.route('/add_branch', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_branch():
    if request.method == 'POST':
        branch = Branch(
            name=request.form.get('name'),
            branch_code=request.form.get('branch_code'),
            firm_id=request.form.get('firm_id'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            manager_id=request.form.get('manager_id')
        )
        
        db.session.add(branch)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_branch', 'branch', branch.id, f'Created branch: {branch.name}')
        
        flash('Branch created successfully!', 'success')
        return redirect(url_for('branches'))
    
    firms = Firm.query.all()
    managers = User.query.filter(User.role.in_(['admin', 'lawyer'])).all()
    return render_template('add_branch.html', firms=firms, managers=managers)

@app.route('/add_permission', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_permission():
    if request.method == 'POST':
        permission = Permission(
            name=request.form.get('name'),
            description=request.form.get('description'),
            module=request.form.get('module')
        )
        
        db.session.add(permission)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_permission', 'permission', permission.id, f'Created permission: {permission.name}')
        
        flash('Permission created successfully!', 'success')
        return redirect(url_for('permissions'))
    
    return render_template('add_permission.html')

@app.route('/add_role_permission', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_role_permission():
    if request.method == 'POST':
        role_permission = RolePermission(
            role=request.form.get('role'),
            permission_id=request.form.get('permission_id')
        )
        
        db.session.add(role_permission)
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'create_role_permission', 'role_permission', role_permission.id, f'Assigned permission to role: {role_permission.role}')
        
        flash('Role permission created successfully!', 'success')
        return redirect(url_for('role_permissions'))
    
    roles = ['admin', 'lawyer', 'paralegal', 'staff', 'finance']
    permissions = Permission.query.all()
    return render_template('add_role_permission.html', roles=roles, permissions=permissions)

@app.route('/settings')
@login_required
@role_required('admin')
def settings():
    # Get system settings
    settings = SystemSetting.query.all()
    
    # Group settings by category
    setting_categories = {}
    for setting in settings:
        category = setting.key.split('_')[0]
        if category not in setting_categories:
            setting_categories[category] = []
        setting_categories[category].append(setting)
    
    return render_template('settings.html', setting_categories=setting_categories)

@app.route('/update_settings', methods=['POST'])
@login_required
@role_required('admin')
def update_settings():
    # Update settings based on form data
    for key, value in request.form.items():
        setting = SystemSetting.query.filter_by(key=key).first()
        
        if setting:
            setting.value = value
            db.session.commit()
        else:
            setting = SystemSetting(
                key=key,
                value=value,
                description=f'System setting for {key}'
            )
            db.session.add(setting)
            db.session.commit()
    
    # Log activity
    log_activity(session['user_id'], 'update_settings', 'system_setting', None, 'Updated system settings')
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings'))

# API Endpoints for mobile app and integrations
@app.route('/api/v1/cases')
@login_required
def api_cases():
    user = User.query.get(session['user_id'])
    cases = []
    
    if user.role == 'admin':
        case_list = Case.query.all()
    else:
        case_list = Case.query.filter_by(assigned_lawyer_id=user.id).all()
    
    for case in case_list:
        cases.append({
            'id': case.id,
            'case_number': case.case_number,
            'title': case.title,
            'client_name': case.client.full_name,
            'status': case.status,
            'priority': case.priority,
            'stage': case.stage
        })
    
    return jsonify({'cases': cases})

@app.route('/api/v1/appointments')
@login_required
def api_appointments():
    user = User.query.get(session['user_id'])
    appointments = []
    
    if user.role == 'admin':
        apt_list = Appointment.query.all()
    elif user.role == 'lawyer':
        apt_list = Appointment.query.filter_by(lawyer_id=user.id).all()
    else:
        apt_list = []
    
    for apt in apt_list:
        appointments.append({
            'id': apt.id,
            'title': apt.title,
            'client_name': apt.client.full_name if apt.client else 'N/A',
            'start_time': apt.start_time.isoformat(),
            'end_time': apt.end_time.isoformat(),
            'location': apt.location,
            'status': apt.status,
            'is_virtual': apt.is_virtual
        })
    
    return jsonify({'appointments': appointments})

@app.route('/api/v1/notifications')
@login_required
def api_notifications():
    user = User.query.get(session['user_id'])
    notifications = Notification.query.filter_by(user_id=user.id, is_read=False).order_by(Notification.created_at.desc()).limit(10).all()
    
    notification_list = []
    for notification in notifications:
        notification_list.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.isoformat()
        })
    
    return jsonify({'notifications': notification_list})

@app.route('/api/v1/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if notification belongs to current user
    if notification.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/v1/client_portal/login', methods=['POST'])
def api_client_portal_login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    client_user = ClientPortalUser.query.filter_by(username=username).first()
    
    if client_user and client_user.check_password(password) and client_user.is_active:
        return jsonify({
            'success': True,
            'user_id': client_user.id,
            'client_id': client_user.client_id,
            'username': client_user.username
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/v1/client_portal/cases/<int:client_id>')
def api_client_portal_cases(client_id):
    # In a real implementation, this would authenticate the client user
    # For now, we'll skip authentication
    
    cases = Case.query.filter_by(client_id=client_id).all()
    
    case_list = []
    for case in cases:
        case_list.append({
            'id': case.id,
            'case_number': case.case_number,
            'title': case.title,
            'status': case.status,
            'stage': case.stage,
            'assigned_lawyer': case.assigned_lawyer.full_name if case.assigned_lawyer else 'N/A'
        })
    
    return jsonify({'cases': case_list})

@app.route('/api/v1/client_portal/appointments/<int:client_id>')
def api_client_portal_appointments(client_id):
    # In a real implementation, this would authenticate the client user
    # For now, we'll skip authentication
    
    appointments = Appointment.query.filter_by(client_id=client_id).all()
    
    apt_list = []
    for apt in appointments:
        apt_list.append({
            'id': apt.id,
            'title': apt.title,
            'start_time': apt.start_time.isoformat(),
            'end_time': apt.end_time.isoformat(),
            'location': apt.location,
            'status': apt.status,
            'is_virtual': apt.is_virtual,
            'meeting_link': apt.meeting_link
        })
    
    return jsonify({'appointments': apt_list})

@app.route('/api/v1/client_portal/documents/<int:client_id>')
def api_client_portal_documents(client_id):
    # In a real implementation, this would authenticate the client user
    # For now, we'll skip authentication
    
    documents = Document.query.filter_by(client_id=client_id).all()
    
    doc_list = []
    for doc in documents:
        doc_list.append({
            'id': doc.id,
            'title': doc.title,
            'filename': doc.filename,
            'file_type': doc.file_type,
            'category': doc.category,
            'created_at': doc.created_at.isoformat()
        })
    
    return jsonify({'documents': doc_list})

@app.route('/api/v1/client_portal/invoices/<int:client_id>')
def api_client_portal_invoices(client_id):
    # In a real implementation, this would authenticate the client user
    # For now, we'll skip authentication
    
    invoices = Invoice.query.filter_by(client_id=client_id).all()
    
    invoice_list = []
    for invoice in invoices:
        invoice_list.append({
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'issue_date': invoice.issue_date.isoformat(),
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'subtotal': invoice.subtotal,
            'tax_amount': invoice.tax_amount,
            'total': invoice.total,
            'status': invoice.status,
            'currency': invoice.currency
        })
    
    return jsonify({'invoices': invoice_list})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
