from app_enhanced import app, db
from models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, TrustAccount, TrustTransaction, Notification, ActivityLog, Firm, Branch, Permission, RolePermission, Communication, Lead, CaseWorkflow, DocumentVersion, Expense, InvoiceLineItem, ClientPortalUser, DocumentAnalysis, LegalResearch, AutomationRule, SystemSetting
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def init_db():
    """Initialize the database with default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@lawfirm.com',
                full_name='System Administrator',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            # Create default firm
            firm = Firm(
                name='Law Firm Management System',
                firm_code='LFMS',
                subdomain='lfms',
                address='123 Legal Street, City, State',
                phone='123-456-7890',
                email='info@lawfirm.com',
                website='https://lawfirm.com'
            )
            db.session.add(firm)
            
            # Create default permissions
            permissions = [
                {'name': 'view_users', 'description': 'View users', 'module': 'users', 'action': 'read'},
                {'name': 'create_users', 'description': 'Create users', 'module': 'users', 'action': 'create'},
                {'name': 'update_users', 'description': 'Update users', 'module': 'users', 'action': 'update'},
                {'name': 'delete_users', 'description': 'Delete users', 'module': 'users', 'action': 'delete'},
                {'name': 'view_clients', 'description': 'View clients', 'module': 'clients', 'action': 'read'},
                {'name': 'create_clients', 'description': 'Create clients', 'module': 'clients', 'action': 'create'},
                {'name': 'update_clients', 'description': 'Update clients', 'module': 'clients', 'action': 'update'},
                {'name': 'delete_clients', 'description': 'Delete clients', 'module': 'clients', 'action': 'delete'},
                {'name': 'view_cases', 'description': 'View cases', 'module': 'cases', 'action': 'read'},
                {'name': 'create_cases', 'description': 'Create cases', 'module': 'cases', 'action': 'create'},
                {'name': 'update_cases', 'description': 'Update cases', 'module': 'cases', 'action': 'update'},
                {'name': 'delete_cases', 'description': 'Delete cases', 'module': 'cases', 'action': 'delete'},
                {'name': 'view_appointments', 'description': 'View appointments', 'module': 'appointments', 'action': 'read'},
                {'name': 'create_appointments', 'description': 'Create appointments', 'module': 'appointments', 'action': 'create'},
                {'name': 'update_appointments', 'description': 'Update appointments', 'module': 'appointments', 'action': 'update'},
                {'name': 'delete_appointments', 'description': 'Delete appointments', 'module': 'appointments', 'action': 'delete'},
                {'name': 'view_documents', 'description': 'View documents', 'module': 'documents', 'action': 'read'},
                {'name': 'create_documents', 'description': 'Create documents', 'module': 'documents', 'action': 'create'},
                {'name': 'update_documents', 'description': 'Update documents', 'module': 'documents', 'action': 'update'},
                {'name': 'delete_documents', 'description': 'Delete documents', 'module': 'documents', 'action': 'delete'},
                {'name': 'view_time_entries', 'description': 'View time entries', 'module': 'time_entries', 'action': 'read'},
                {'name': 'create_time_entries', 'description': 'Create time entries', 'module': 'time_entries', 'action': 'create'},
                {'name': 'update_time_entries', 'description': 'Update time entries', 'module': 'time_entries', 'action': 'update'},
                {'name': 'delete_time_entries', 'description': 'Delete time entries', 'module': 'time_entries', 'action': 'delete'},
                {'name': 'view_invoices', 'description': 'View invoices', 'module': 'invoices', 'action': 'read'},
                {'name': 'create_invoices', 'description': 'Create invoices', 'module': 'invoices', 'action': 'create'},
                {'name': 'update_invoices', 'description': 'Update invoices', 'module': 'invoices', 'action': 'update'},
                {'name': 'delete_invoices', 'description': 'Delete invoices', 'module': 'invoices', 'action': 'delete'},
                {'name': 'view_trust_accounts', 'description': 'View trust accounts', 'module': 'trust_accounts', 'action': 'read'},
                {'name': 'create_trust_accounts', 'description': 'Create trust accounts', 'module': 'trust_accounts', 'action': 'create'},
                {'name': 'update_trust_accounts', 'description': 'Update trust accounts', 'module': 'trust_accounts', 'action': 'update'},
                {'name': 'delete_trust_accounts', 'description': 'Delete trust accounts', 'module': 'trust_accounts', 'action': 'delete'},
                {'name': 'view_reports', 'description': 'View reports', 'module': 'reports', 'action': 'read'},
                {'name': 'create_reports', 'description': 'Create reports', 'module': 'reports', 'action': 'create'},
                {'name': 'view_settings', 'description': 'View settings', 'module': 'settings', 'action': 'read'},
                {'name': 'update_settings', 'description': 'Update settings', 'module': 'settings', 'action': 'update'}
            ]
            
            for perm_data in permissions:
                permission = Permission(**perm_data)
                db.session.add(permission)
            
            # Create default role permissions for admin
            admin_permissions = Permission.query.all()
            for permission in admin_permissions:
                role_permission = RolePermission(role='admin', permission_id=permission.id)
                db.session.add(role_permission)
            
            # Create default role permissions for lawyer
            lawyer_permissions = [
                'view_clients', 'create_clients', 'update_clients',
                'view_cases', 'create_cases', 'update_cases',
                'view_appointments', 'create_appointments', 'update_appointments',
                'view_documents', 'create_documents', 'update_documents',
                'view_time_entries', 'create_time_entries', 'update_time_entries',
                'view_invoices', 'create_invoices', 'update_invoices',
                'view_reports'
            ]
            
            for perm_name in lawyer_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role_permission = RolePermission(role='lawyer', permission_id=permission.id)
                    db.session.add(role_permission)
            
            # Create default role permissions for paralegal
            paralegal_permissions = [
                'view_clients', 'create_clients', 'update_clients',
                'view_cases', 'create_cases', 'update_cases',
                'view_appointments', 'create_appointments', 'update_appointments',
                'view_documents', 'create_documents', 'update_documents',
                'view_time_entries', 'create_time_entries', 'update_time_entries'
            ]
            
            for perm_name in paralegal_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role_permission = RolePermission(role='paralegal', permission_id=permission.id)
                    db.session.add(role_permission)
            
            # Create default role permissions for staff
            staff_permissions = [
                'view_clients',
                'view_cases',
                'view_appointments', 'create_appointments', 'update_appointments',
                'view_documents', 'create_documents', 'update_documents'
            ]
            
            for perm_name in staff_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role_permission = RolePermission(role='staff', permission_id=permission.id)
                    db.session.add(role_permission)
            
            # Create default role permissions for finance
            finance_permissions = [
                'view_clients',
                'view_cases',
                'view_invoices', 'create_invoices', 'update_invoices',
                'view_trust_accounts', 'create_trust_accounts', 'update_trust_accounts',
                'view_reports'
            ]
            
            for perm_name in finance_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role_permission = RolePermission(role='finance', permission_id=permission.id)
                    db.session.add(role_permission)
            
            # Create default system settings
            settings = [
                {'key': 'app_name', 'value': 'Law Firm Management System', 'description': 'Application name'},
                {'key': 'app_version', 'value': '1.0.0', 'description': 'Application version'},
                {'key': 'default_currency', 'value': 'INR', 'description': 'Default currency'},
                {'key': 'default_time_zone', 'value': 'Asia/Kolkata', 'description': 'Default time zone'},
                {'key': 'enable_email_notifications', 'value': 'true', 'description': 'Enable email notifications', 'data_type': 'boolean'},
                {'key': 'enable_sms_notifications', 'value': 'false', 'description': 'Enable SMS notifications', 'data_type': 'boolean'},
                {'key': 'enable_two_factor_auth', 'value': 'false', 'description': 'Enable two-factor authentication', 'data_type': 'boolean'},
                {'key': 'session_timeout_minutes', 'value': '30', 'description': 'Session timeout in minutes', 'data_type': 'integer'},
                {'key': 'max_login_attempts', 'value': '5', 'description': 'Maximum login attempts', 'data_type': 'integer'},
                {'key': 'password_expiry_days', 'value': '90', 'description': 'Password expiry in days', 'data_type': 'integer'},
                {'key': 'backup_schedule', 'value': 'daily', 'description': 'Database backup schedule'},
                {'key': 'enable_audit_logging', 'value': 'true', 'description': 'Enable audit logging', 'data_type': 'boolean'},
                {'key': 'enable_data_encryption', 'value': 'true', 'description': 'Enable data encryption', 'data_type': 'boolean'},
                {'key': 'enable_multi_tenancy', 'value': 'false', 'description': 'Enable multi-tenancy', 'data_type': 'boolean'},
                {'key': 'max_tenants', 'value': '10', 'description': 'Maximum number of tenants', 'data_type': 'integer'},
                {'key': 'max_users_per_tenant', 'value': '50', 'description': 'Maximum users per tenant', 'data_type': 'integer'},
                {'key': 'enable_tenant_isolation', 'value': 'true', 'description': 'Enable tenant isolation', 'data_type': 'boolean'},
                {'key': 'enable_tenant_branding', 'value': 'true', 'description': 'Enable tenant branding', 'data_type': 'boolean'},
                {'key': 'enable_custom_themes', 'value': 'true', 'description': 'Enable custom themes', 'data_type': 'boolean'},
                {'key': 'enable_custom_layouts', 'value': 'true', 'description': 'Enable custom layouts', 'data_type': 'boolean'},
                {'key': 'enable_custom_fields', 'value': 'true', 'description': 'Enable custom fields', 'data_type': 'boolean'},
                {'key': 'enable_custom_workflows', 'value': 'true', 'description': 'Enable custom workflows', 'data_type': 'boolean'},
                {'key': 'enable_custom_reports', 'value': 'true', 'description': 'Enable custom reports', 'data_type': 'boolean'},
                {'key': 'enable_custom_integrations', 'value': 'true', 'description': 'Enable custom integrations', 'data_type': 'boolean'}
            ]
            
            for setting_data in settings:
                setting = SystemSetting(**setting_data)
                db.session.add(setting)
            
            # Create upload directories
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']), exist_ok=True)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'receipts'), exist_ok=True)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
            
            # Commit all changes
            db.session.commit()
            
            print("Database initialized successfully!")
            print("Default admin user created:")
            print("Username: admin")
            print("Password: admin123")
            print("\nPlease change the default password after first login.")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)