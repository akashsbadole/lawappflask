from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# Create a standalone instance of SQLAlchemy
db = SQLAlchemy()

# Multi-tenant Firm/Branch Model
class Firm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    firm_code = db.Column(db.String(20), unique=True, nullable=False)
    subdomain = db.Column(db.String(50), unique=True)
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), default='#007bff')
    secondary_color = db.Column(db.String(7), default='#6c757d')
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    gst_number = db.Column(db.String(20))
    pan_number = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branches = db.relationship('Branch', backref='firm', lazy='dynamic')
    users = db.relationship('User', backref='firm', lazy='dynamic')
    
    def __repr__(self):
        return f'<Firm {self.name}>'

# Branch Model for multi-office support
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firm.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    branch_code = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50), default='India')
    postal_code = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='branch', lazy='dynamic')
    
    def __repr__(self):
        return f'<Branch {self.name}>'

# Permission Model for role-based access control
class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    module = db.Column(db.String(50))  # clients, cases, documents, etc.
    action = db.Column(db.String(50))  # create, read, update, delete, etc.
    
    def __repr__(self):
        return f'<Permission {self.name}>'

# Role-Permission Mapping
class RolePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    
    # Relationships
    permission = db.relationship('Permission', backref='role_permissions')
    
    def __repr__(self):
        return f'<RolePermission {self.role}:{self.permission.name}>'

# Client Communication History
class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    communication_type = db.Column(db.String(50))  # email, phone, meeting, chat, etc.
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    direction = db.Column(db.String(20))  # inbound, outbound
    duration_minutes = db.Column(db.Integer)  # for calls/meetings
    attachment_url = db.Column(db.String(500))
    is_billable = db.Column(db.Boolean, default=False)
    communication_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', backref='communications')
    case = db.relationship('Case', backref='communications')
    user = db.relationship('User', backref='communications')
    
    def __repr__(self):
        return f'<Communication {self.communication_type}>'

# Lead Management Model
class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    practice_area = db.Column(db.String(50))
    case_description = db.Column(db.Text)
    source = db.Column(db.String(50))  # website, referral, advertisement, etc.
    status = db.Column(db.String(20), default='new')  # new, contacted, qualified, converted, lost
    priority = db.Column(db.String(20), default='medium')
    assigned_lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime)
    converted_to_client = db.Column(db.Boolean, default=False)
    converted_client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_lawyer = db.relationship('User', foreign_keys=[assigned_lawyer_id], backref='assigned_leads')
    converted_client = db.relationship('Client', foreign_keys=[converted_client_id])
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Lead {self.lead_number}>'

# Case Workflow/Stage Model
class CaseWorkflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    stage_name = db.Column(db.String(50), nullable=False)
    stage_order = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    due_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    case = db.relationship('Case', backref='workflows')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    
    def __repr__(self):
        return f'<CaseWorkflow {self.stage_name}>'

# Document Version Control
class DocumentVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_notes = db.Column(db.Text)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    document = db.relationship('Document', backref='versions')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f'<DocumentVersion v{self.version_number}>'

# Expense Tracking Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    expense_type = db.Column(db.String(50))  # travel, meals, supplies, etc.
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    date_incurred = db.Column(db.Date, nullable=False)
    is_billable = db.Column(db.Boolean, default=True)
    receipt_filename = db.Column(db.String(255))
    receipt_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, reimbursed
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='expenses')
    case = db.relationship('Case', backref='expenses')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<Expense {self.description}>'

# Invoice Line Items
class InvoiceLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    item_type = db.Column(db.String(50))  # time_entry, expense, flat_fee, etc.
    reference_id = db.Column(db.Integer)  # Reference to time_entry, expense, etc.
    
    # Relationships
    invoice = db.relationship('Invoice', backref='line_items')
    
    def __repr__(self):
        return f'<InvoiceLineItem {self.description}>'

# Client Portal User Model
class ClientPortalUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', backref='portal_users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<ClientPortalUser {self.username}>'

# AI Document Analysis
class DocumentAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    analysis_type = db.Column(db.String(50))  # summary, keywords, entities, sentiment
    analysis_result = db.Column(db.Text)
    confidence_score = db.Column(db.Float)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    document = db.relationship('Document', backref='analyses')
    
    def __repr__(self):
        return f'<DocumentAnalysis {self.analysis_type}>'

# AI Legal Research
class LegalResearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_results = db.Column(db.Text)  # JSON string of results
    relevant_cases = db.Column(db.Text)  # JSON string of relevant case law
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    case = db.relationship('Case', backref='legal_research')
    user = db.relationship('User', foreign_keys='LegalResearch.user_id', backref='legal_research')
    
    def __repr__(self):
        return f'<LegalResearch {self.query[:50]}>'

# Workflow Automation Rules
class AutomationRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    trigger_event = db.Column(db.String(50))  # case_created, appointment_scheduled, etc.
    trigger_conditions = db.Column(db.Text)  # JSON string of conditions
    actions = db.Column(db.Text)  # JSON string of actions to perform
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<AutomationRule {self.name}>'

# System Settings
class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    data_type = db.Column(db.String(20), default='string')  # string, integer, boolean, json
    is_public = db.Column(db.Boolean, default=False)  # Can be accessed by client portal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>'

# User Model for Step 1: User Management & Roles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firm.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, lawyer, paralegal, client, finance, support
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Enhanced Security Fields
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    backup_codes = db.Column(db.Text)  # Comma-separated backup codes
    sms_login_enabled = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clients_assigned = db.relationship('Client', foreign_keys='Client.assigned_lawyer_id', backref='assigned_lawyer', lazy='dynamic')
    cases_assigned = db.relationship('Case', foreign_keys='Case.assigned_lawyer_id', backref='assigned_lawyer', lazy='dynamic')
    appointments = db.relationship('Appointment', foreign_keys='Appointment.lawyer_id', backref='lawyer', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', foreign_keys='TimeEntry.user_id', backref='user', lazy='dynamic')
    attendance_records = db.relationship('Attendance', foreign_keys='Attendance.user_id', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        """Check if account is locked due to failed attempts"""
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    def lock_account(self, hours=24):
        """Lock account for specified hours"""
        self.account_locked_until = datetime.utcnow() + timedelta(hours=hours)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock account"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def verify_backup_code(self, code):
        """Verify backup code for 2FA"""
        if not self.backup_codes:
            return False
        
        codes = self.backup_codes.split(',')
        if code in codes:
            # Remove used backup code
            codes.remove(code)
            self.backup_codes = ','.join(codes)
            db.session.commit()
            return True
        
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

# Client Model for Step 2: Client & CRM Management
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='India')
    company = db.Column(db.String(100))
    client_type = db.Column(db.String(20))  # individual, corporate
    practice_area = db.Column(db.String(50))
    priority = db.Column(db.String(20), default='medium')  # high, medium, low
    assigned_lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cases = db.relationship('Case', backref='client', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='client', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='client', lazy='dynamic')
    trust_account = db.relationship('TrustAccount', backref='client', uselist=False)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Client {self.client_number}>'

# Case Model for Step 3: Case/Matter Management
class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    assigned_lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    case_type = db.Column(db.String(50))  # Civil, Criminal, Corporate, Tax, etc.
    status = db.Column(db.String(20), default='open')  # open, in_progress, closed, archived
    priority = db.Column(db.String(20), default='medium')  # high, medium, low
    stage = db.Column(db.String(50))  # Intake, Drafting, Filing, Review, Closure
    date_opened = db.Column(db.DateTime, default=datetime.utcnow)
    date_closed = db.Column(db.DateTime)
    estimated_completion = db.Column(db.DateTime)
    actual_completion = db.Column(db.DateTime)
    billing_method = db.Column(db.String(20), default='hourly')  # hourly, flat_fee, retainer
    hourly_rate = db.Column(db.Float)
    budget = db.Column(db.Float)
    court_number = db.Column(db.String(100))  # Court case number for legal tracking
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='case', lazy='dynamic')
    documents = db.relationship('Document', backref='case', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='case', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='case', lazy='dynamic')
    
    def __repr__(self):
        return f'<Case {self.case_number}>'

# Appointment Model for Step 4: Appointments & Scheduling
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    appointment_type = db.Column(db.String(50))  # Consultation, Hearing, Client Meeting, etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    is_virtual = db.Column(db.Boolean, default=False)
    meeting_link = db.Column(db.String(500))
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    notes = db.Column(db.Text)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.title}>'

# Document Model for Step 5: Document Management System
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    category = db.Column(db.String(50))  # Contracts, Evidence, Petitions, etc.
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    version = db.Column(db.Integer, default=1)
    is_confidential = db.Column(db.Boolean, default=False)
    is_signed = db.Column(db.Boolean, default=False)
    signature_date = db.Column(db.DateTime)
    tags = db.Column(db.String(500))  # Comma-separated tags
    ocr_text = db.Column(db.Text)  # Extracted text from OCR
    ai_summary = db.Column(db.Text)  # AI-generated summary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='uploaded_documents')
    
    def __repr__(self):
        return f'<Document {self.title}>'

# TimeEntry Model for Step 6: Time & Expense Tracking
class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    description = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    is_billable = db.Column(db.Boolean, default=True)
    hourly_rate = db.Column(db.Float)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='draft')  # draft, submitted, approved, rejected, invoiced
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_amount(self):
        if self.duration_minutes and self.hourly_rate:
            self.amount = (self.duration_minutes / 60) * self.hourly_rate
        return self.amount
    
    def __repr__(self):
        return f'<TimeEntry {self.id}>'

# Invoice Model for Step 7: Billing & Invoicing
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    issue_date = db.Column(db.Date, default=datetime.utcnow().date)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=0)  # Percentage
    tax_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid, overdue, cancelled
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')
    
    def calculate_total(self):
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount
        return self.total
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

# Payment Model for Step 7: Billing & Invoicing
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))  # cash, check, credit_card, bank_transfer, online
    transaction_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.id}>'

# TrustAccount Model for Step 8: Trust/Escrow & Financial Management
class TrustAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('TrustTransaction', backref='trust_account', lazy='dynamic')
    
    def __repr__(self):
        return f'<TrustAccount {self.account_number}>'

# TrustTransaction Model for Step 8: Trust/Escrow & Financial Management
class TrustTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trust_account_id = db.Column(db.Integer, db.ForeignKey('trust_account.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrustTransaction {self.id}>'

# Notification Model for Step 16: Notifications & Workflow Automation
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # appointment, case, invoice, payment, system
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recipient = db.relationship('User', foreign_keys='Notification.user_id', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'

# ActivityLog Model for Step 12: Security & Compliance
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))  # client, case, document, etc.
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys='ActivityLog.user_id', backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'

# Attendance Model for Enhanced User Management
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_out_time = db.Column(db.DateTime)
    check_in_latitude = db.Column(db.Float)
    check_in_longitude = db.Column(db.Float)
    check_out_latitude = db.Column(db.Float)
    check_out_longitude = db.Column(db.Float)
    check_in_method = db.Column(db.String(20), default='manual')  # manual, gps, biometric
    check_out_method = db.Column(db.String(20), default='manual')
    break_duration_minutes = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Float)
    overtime_hours = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='present')  # present, absent, half_day, leave
    notes = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def calculate_total_hours(self):
        """Calculate total working hours"""
        if self.check_out_time and self.check_in_time:
            total_seconds = (self.check_out_time - self.check_in_time).total_seconds()
            total_hours = total_seconds / 3600
            # Subtract break time
            if self.break_duration_minutes:
                total_hours -= (self.break_duration_minutes / 60)
            self.total_hours = max(0, total_hours)
            
            # Calculate overtime (assuming 8 hours is standard)
            if self.total_hours > 8:
                self.overtime_hours = self.total_hours - 8
            else:
                self.overtime_hours = 0
        
        return self.total_hours or 0
    
    def is_late(self, standard_time='09:00'):
        """Check if check-in is late"""
        if self.check_in_time:
            standard_hour, standard_minute = map(int, standard_time.split(':'))
            standard_time_obj = self.check_in_time.replace(
                hour=standard_hour, 
                minute=standard_minute, 
                second=0, 
                microsecond=0
            )
            return self.check_in_time > standard_time_obj
        return False
    
    def __repr__(self):
        return f'<Attendance {self.user.full_name} - {self.date}>'

# User Performance Metrics Model
class UserPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period = db.Column(db.String(20), nullable=False)  # monthly, quarterly, yearly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    total_hours_worked = db.Column(db.Float, default=0)
    billable_hours = db.Column(db.Float, default=0)
    utilization_rate = db.Column(db.Float, default=0)  # percentage
    cases_handled = db.Column(db.Integer, default=0)
    cases_won = db.Column(db.Integer, default=0)
    revenue_generated = db.Column(db.Float, default=0)
    client_satisfaction_score = db.Column(db.Float)  # 1-5 scale
    productivity_score = db.Column(db.Float, default=0)  # calculated metric
    attendance_score = db.Column(db.Float, default=0)  # percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys='UserPerformance.user_id', backref='performance_metrics')
    
    def calculate_utilization_rate(self):
        """Calculate utilization rate (billable hours / total hours)"""
        if self.total_hours_worked > 0:
            self.utilization_rate = (self.billable_hours / self.total_hours_worked) * 100
        else:
            self.utilization_rate = 0
        return self.utilization_rate
    
    def calculate_productivity_score(self):
        """Calculate overall productivity score"""
        # Weighted calculation based on multiple factors
        weights = {
            'utilization': 0.3,
            'cases_won_rate': 0.25,
            'revenue_per_hour': 0.2,
            'client_satisfaction': 0.15,
            'attendance': 0.1
        }
        
        score = 0
        
        # Utilization score (0-100)
        score += (self.utilization_rate / 100) * weights['utilization'] * 100
        
        # Cases won rate (0-100)
        if self.cases_handled > 0:
            cases_won_rate = (self.cases_won / self.cases_handled) * 100
            score += (cases_won_rate / 100) * weights['cases_won_rate'] * 100
        
        # Revenue per hour (normalized)
        if self.total_hours_worked > 0:
            revenue_per_hour = self.revenue_generated / self.total_hours_worked
            # Assuming $100/hour as benchmark
            revenue_score = min(revenue_per_hour / 100, 1) * 100
            score += revenue_score * weights['revenue_per_hour']
        
        # Client satisfaction (0-100)
        if self.client_satisfaction_score:
            score += (self.client_satisfaction_score / 5) * weights['client_satisfaction'] * 100
        
        # Attendance (0-100)
        score += self.attendance_score * weights['attendance']
        
        self.productivity_score = min(score, 100)
        return self.productivity_score
    
    def __repr__(self):
        return f'<UserPerformance {self.user.full_name} - {self.period}>'

# Enquiry Model for Public Enquiry Form
class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    practice_area = db.Column(db.String(100))
    urgency_level = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    preferred_contact = db.Column(db.String(50))  # email, phone, both
    status = db.Column(db.String(20), default='pending')  # pending, contacted, assigned, closed
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_enquiries')
    
    @property
    def full_name(self):
        return self.name
    
    def __repr__(self):
        return f'<Enquiry {self.name} - {self.subject}>'
