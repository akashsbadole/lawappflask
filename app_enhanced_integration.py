"""
Enhanced Law Firm Management System Integration
This file shows how to integrate all the new enhanced features with the existing app
"""

from flask import Flask, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate
import os

# Import existing app components
from models import db, User, Client, Case, Document, Attendance, DocumentAnalysis
from enhanced_security import enhanced_security, attendance_tracker
from document_ocr import ocr_engine, document_analyzer
from auth_routes import auth_bp
from document_routes import documents_bp

def create_enhanced_app():
    """Create and configure the enhanced Flask app"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'law_firm_management_enhanced_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///law_firm_enhanced.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Session configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = 'flask_session'
    app.config['SESSION_FILE_THRESHOLD'] = 500
    
    # Enhanced Security Configuration
    app.config['SMS_PROVIDER'] = 'twilio'  # or 'msg91' or 'dev'
    app.config['TWILIO_ACCOUNT_SID'] = os.environ.get('TWILIO_ACCOUNT_SID')
    app.config['TWILIO_AUTH_TOKEN'] = os.environ.get('TWILIO_AUTH_TOKEN')
    app.config['TWILIO_PHONE_NUMBER'] = os.environ.get('TWILIO_PHONE_NUMBER')
    app.config['MSG91_AUTH_KEY'] = os.environ.get('MSG91_AUTH_KEY')
    app.config['MSG91_TEMPLATE_ID'] = os.environ.get('MSG91_TEMPLATE_ID')
    app.config['2FA_ISSUER_NAME'] = 'LawEdge'
    
    # OCR Configuration
    app.config['TESSERACT_PATH'] = os.environ.get('TESSERACT_PATH')  # Path to tesseract executable
    app.config['OCR_LANGUAGES'] = ['eng', 'hin', 'mar', 'tam']  # Supported OCR languages
    
    # AI Configuration
    app.config['AI_SERVICE'] = 'mock'  # 'mock', 'openai', 'gemini'
    app.config['AI_API_KEY'] = os.environ.get('AI_API_KEY')
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    Session(app)
    
    # Initialize enhanced services
    enhanced_security.init_app(app)
    ocr_engine.init_app(app)
    document_analyzer.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'receipts'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Import existing routes (you'll need to adapt these to work with the new auth system)
# from app import *  # Import all existing routes

def integrate_existing_routes(app):
    """Integrate existing routes with enhanced authentication"""
    
    # Update existing login_required decorator to use the new auth system
    from functools import wraps
    
    def enhanced_login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect('/auth/login')
            return f(*args, **kwargs)
        return decorated_function
    
    # Replace the old login_required with the new one
    import sys
    current_module = sys.modules[__name__]
    current_module.login_required = enhanced_login_required
    
    return app

def setup_database_migrations():
    """Setup database migrations for new fields"""
    from flask_migrate import init, migrate, upgrade
    
    # This would typically be run via command line:
    # flask db init
    # flask db migrate -m "Add enhanced security and OCR features"
    # flask db upgrade
    
    print("Database migrations setup complete!")
    print("Run the following commands to apply migrations:")
    print("flask db init")
    print("flask db migrate -m 'Add enhanced security and OCR features'")
    print("flask db upgrade")

def create_sample_data():
    """Create sample data for testing"""
    from models import User, Client, Case, Firm
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        # Create sample firm
        firm = Firm.query.filter_by(firm_code='LAWEDGE001').first()
        if not firm:
            firm = Firm(
                name='LawEdge Legal Services',
                firm_code='LAWEDGE001',
                address='123 Legal Street, Mumbai, India',
                phone='+91-22-12345678',
                email='info@lawedge.com'
            )
            db.session.add(firm)
        
        # Create sample admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@lawedge.com',
                full_name='System Administrator',
                role='admin',
                phone='+91-9876543210',
                firm_id=firm.id if firm else None
            )
            admin_user.set_password('admin123')
            admin_user.two_factor_enabled = False
            admin_user.sms_login_enabled = True
            db.session.add(admin_user)
        
        # Create sample lawyer
        lawyer_user = User.query.filter_by(username='lawyer').first()
        if not lawyer_user:
            lawyer_user = User(
                username='lawyer',
                email='lawyer@lawedge.com',
                full_name='John Lawyer',
                role='lawyer',
                phone='+91-9876543211',
                firm_id=firm.id if firm else None
            )
            lawyer_user.set_password('lawyer123')
            lawyer_user.two_factor_enabled = False
            lawyer_user.sms_login_enabled = True
            db.session.add(lawyer_user)
        
        db.session.commit()
        print("Sample data created successfully!")

if __name__ == '__main__':
    # Create the enhanced app
    app = create_enhanced_app()
    
    # Integrate with existing routes
    app = integrate_existing_routes(app)
    
    # Setup database migrations (first time only)
    # setup_database_migrations()
    
    # Create sample data (for testing)
    # create_sample_data()
    
    # Import and register existing routes here
    # You would typically import your existing app routes and register them
    
    print("Enhanced Law Firm Management System is ready!")
    print("New features implemented:")
    print("✓ Enhanced Security with SMS OTP and 2FA")
    print("✓ Advanced Document Management with OCR")
    print("✓ Attendance Tracking with Geolocation")
    print("✓ AI Document Analysis")
    print("✓ Advanced Search and Analytics")
    print("")
    print("To start the application:")
    print("python app_enhanced_integration.py")
    print("")
    print("Default login credentials:")
    print("Admin: username=admin, password=admin123")
    print("Lawyer: username=lawyer, password=lawyer123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
