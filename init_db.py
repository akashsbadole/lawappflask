from app import app, db
from models import User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, TrustAccount, TrustTransaction, Notification, ActivityLog
from datetime import datetime, timedelta
import random

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if users already exist
        if User.query.first():
            print("Database already initialized!")
            return
        
        # Create default users
        admin_user = User(
            username='admin',
            email='admin@lawedge.com',
            full_name='System Administrator',
            role='admin',
            phone='+91-9876543210',
            address='123 Main Street, Mumbai, Maharashtra 400001, India'
        )
        admin_user.set_password('admin123')
        
        lawyer_user = User(
            username='jdoe',
            email='jdoe@lawedge.com',
            full_name='John Doe',
            role='lawyer',
            phone='+91-9876543211',
            address='456 Park Avenue, Delhi, Delhi 110001, India'
        )
        lawyer_user.set_password('lawyer123')
        
        staff_user = User(
            username='msmith',
            email='msmith@lawedge.com',
            full_name='Mary Smith',
            role='staff',
            phone='+91-9876543212',
            address='789 Market Street, Bangalore, Karnataka 560001, India'
        )
        staff_user.set_password('staff123')
        
        db.session.add_all([admin_user, lawyer_user, staff_user])
        db.session.commit()
        
        # Create sample clients
        clients = [
            Client(
                client_number='CL-2023-001',
                first_name='John',
                last_name='Smith',
                email='john.smith@email.com',
                phone='+91-9876543213',
                address='123 Residential Area, Mumbai, Maharashtra 400001, India',
                city='Mumbai',
                state='Maharashtra',
                postal_code='400001',
                client_type='individual',
                practice_area='Property Law',
                priority='high',
                assigned_lawyer_id=lawyer_user.id,
                notes='Client interested in property dispute resolution.'
            ),
            Client(
                client_number='CL-2023-002',
                first_name='Sarah',
                last_name='Johnson',
                email='sarah.j@company.com',
                phone='+91-9876543214',
                address='456 Business Park, Bangalore, Karnataka 560001, India',
                city='Bangalore',
                state='Karnataka',
                postal_code='560001',
                company='Tech Solutions Pvt. Ltd.',
                client_type='corporate',
                practice_area='Corporate Law',
                priority='medium',
                assigned_lawyer_id=lawyer_user.id,
                notes='Corporate client for contract review and compliance.'
            ),
            Client(
                client_number='CL-2023-003',
                first_name='Michael',
                last_name='Brown',
                email='michael.b@email.com',
                phone='+91-9876543215',
                address='789 Urban Estate, Delhi, Delhi 110001, India',
                city='Delhi',
                state='Delhi',
                postal_code='110001',
                client_type='individual',
                practice_area='Employment Law',
                priority='low',
                assigned_lawyer_id=lawyer_user.id,
                notes='Employment dispute case.'
            )
        ]
        
        db.session.add_all(clients)
        db.session.commit()
        
        # Create sample cases
        cases = [
            Case(
                case_number='CASE-2023-001',
                title='Property Dispute - Residential Complex',
                description='Dispute regarding ownership of residential property in Mumbai.',
                client_id=clients[0].id,
                assigned_lawyer_id=lawyer_user.id,
                case_type='Civil',
                status='in_progress',
                stage='Filing',
                date_opened=datetime.utcnow() - timedelta(days=30),
                estimated_completion=datetime.utcnow() + timedelta(days=60),
                billing_method='hourly',
                hourly_rate=2000.0,
                budget=50000.0,
                notes='Property dispute case requiring title verification and court proceedings.'
            ),
            Case(
                case_number='CASE-2023-002',
                title='Contract Review - Service Agreement',
                description='Review and negotiation of service agreement for Tech Solutions.',
                client_id=clients[1].id,
                assigned_lawyer_id=lawyer_user.id,
                case_type='Corporate',
                status='open',
                stage='Review',
                date_opened=datetime.utcnow() - timedelta(days=15),
                estimated_completion=datetime.utcnow() + timedelta(days=15),
                billing_method='flat_fee',
                budget=25000.0,
                notes='Standard contract review for corporate client.'
            ),
            Case(
                case_number='CASE-2023-003',
                title='Employment Termination Dispute',
                description='Wrongful termination claim against former employer.',
                client_id=clients[2].id,
                assigned_lawyer_id=lawyer_user.id,
                case_type='Employment',
                status='closed',
                stage='Closure',
                date_opened=datetime.utcnow() - timedelta(days=90),
                date_closed=datetime.utcnow() - timedelta(days=10),
                actual_completion=datetime.utcnow() - timedelta(days=10),
                billing_method='hourly',
                hourly_rate=1500.0,
                notes='Employment dispute resolved through mediation.'
            )
        ]
        
        db.session.add_all(cases)
        db.session.commit()
        
        # Create sample appointments
        appointments = [
            Appointment(
                title='Client Consultation - Property Dispute',
                description='Initial consultation regarding property dispute case.',
                client_id=clients[0].id,
                lawyer_id=lawyer_user.id,
                case_id=cases[0].id,
                appointment_type='Consultation',
                start_time=datetime.utcnow() + timedelta(days=1, hours=14),
                end_time=datetime.utcnow() + timedelta(days=1, hours=15),
                location='Office Meeting Room 1',
                status='scheduled'
            ),
            Appointment(
                title='Court Hearing - Property Case',
                description='Court hearing for property dispute case.',
                client_id=clients[0].id,
                lawyer_id=lawyer_user.id,
                case_id=cases[0].id,
                appointment_type='Hearing',
                start_time=datetime.utcnow() + timedelta(days=5, hours=10),
                end_time=datetime.utcnow() + timedelta(days=5, hours=12),
                location='District Court, Mumbai',
                status='scheduled'
            ),
            Appointment(
                title='Contract Review Meeting',
                description='Meeting to discuss contract review findings.',
                client_id=clients[1].id,
                lawyer_id=lawyer_user.id,
                case_id=cases[1].id,
                appointment_type='Client Meeting',
                start_time=datetime.utcnow() + timedelta(days=2, hours=15),
                end_time=datetime.utcnow() + timedelta(days=2, hours=16),
                is_virtual=True,
                meeting_link='https://zoom.us/j/123456789',
                status='scheduled'
            )
        ]
        
        db.session.add_all(appointments)
        db.session.commit()
        
        # Create sample documents
        documents = [
            Document(
                title='Property Title Deed',
                description='Original title deed for the disputed property.',
                filename='title_deed.pdf',
                file_path='uploads/documents/title_deed.pdf',
                file_size=2048576,
                file_type='application/pdf',
                category='Evidence',
                case_id=cases[0].id,
                client_id=clients[0].id,
                uploaded_by=lawyer_user.id,
                tags='property, title, evidence'
            ),
            Document(
                title='Service Agreement',
                description='Service agreement for Tech Solutions Pvt. Ltd.',
                filename='service_agreement.docx',
                file_path='uploads/documents/service_agreement.docx',
                file_size=1024000,
                file_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                category='Contracts',
                case_id=cases[1].id,
                client_id=clients[1].id,
                uploaded_by=lawyer_user.id,
                tags='contract, service, corporate'
            ),
            Document(
                title='Employment Contract',
                description='Employment contract for termination dispute.',
                filename='employment_contract.pdf',
                file_path='uploads/documents/employment_contract.pdf',
                file_size=1536000,
                file_type='application/pdf',
                category='Contracts',
                case_id=cases[2].id,
                client_id=clients[2].id,
                uploaded_by=lawyer_user.id,
                tags='employment, contract, termination'
            )
        ]
        
        db.session.add_all(documents)
        db.session.commit()
        
        # Create sample time entries
        time_entries = [
            TimeEntry(
                user_id=lawyer_user.id,
                case_id=cases[0].id,
                description='Legal research for property dispute case',
                start_time=datetime.utcnow() - timedelta(days=5, hours=9),
                end_time=datetime.utcnow() - timedelta(days=5, hours=11),
                duration_minutes=120,
                is_billable=True,
                hourly_rate=2000.0,
                status='approved'
            ),
            TimeEntry(
                user_id=lawyer_user.id,
                case_id=cases[0].id,
                description='Client consultation - property dispute',
                start_time=datetime.utcnow() - timedelta(days=4, hours=14),
                end_time=datetime.utcnow() - timedelta(days=4, hours=15),
                duration_minutes=60,
                is_billable=True,
                hourly_rate=2000.0,
                status='approved'
            ),
            TimeEntry(
                user_id=lawyer_user.id,
                case_id=cases[1].id,
                description='Contract review and analysis',
                start_time=datetime.utcnow() - timedelta(days=3, hours=10),
                end_time=datetime.utcnow() - timedelta(days=3, hours=12),
                duration_minutes=120,
                is_billable=True,
                hourly_rate=2000.0,
                status='submitted'
            )
        ]
        
        # Calculate amounts
        for entry in time_entries:
            entry.calculate_amount()
        
        db.session.add_all(time_entries)
        db.session.commit()
        
        # Create sample invoices
        invoices = [
            Invoice(
                invoice_number='INV-2023-001',
                client_id=clients[0].id,
                case_id=cases[0].id,
                issue_date=datetime.utcnow().date(),
                due_date=(datetime.utcnow() + timedelta(days=30)).date(),
                subtotal=6000.0,
                tax_rate=18.0,
                status='sent'
            ),
            Invoice(
                invoice_number='INV-2023-002',
                client_id=clients[1].id,
                case_id=cases[1].id,
                issue_date=datetime.utcnow().date(),
                due_date=(datetime.utcnow() + timedelta(days=30)).date(),
                subtotal=25000.0,
                tax_rate=18.0,
                status='draft'
            )
        ]
        
        # Calculate totals
        for invoice in invoices:
            invoice.calculate_total()
        
        db.session.add_all(invoices)
        db.session.commit()
        
        # Create sample trust accounts
        trust_accounts = [
            TrustAccount(
                client_id=clients[0].id,
                account_number='TA-CL-001',
                balance=25000.0
            ),
            TrustAccount(
                client_id=clients[1].id,
                account_number='TA-CL-002',
                balance=50000.0
            )
        ]
        
        db.session.add_all(trust_accounts)
        db.session.commit()
        
        # Create sample notifications
        notifications = [
            Notification(
                user_id=lawyer_user.id,
                title='Upcoming Appointment',
                message='You have a client consultation scheduled for tomorrow at 2:00 PM.',
                notification_type='appointment'
            ),
            Notification(
                user_id=lawyer_user.id,
                title='New Case Assigned',
                message='A new case has been assigned to you: Contract Review - Service Agreement.',
                notification_type='case'
            ),
            Notification(
                user_id=admin_user.id,
                title='System Update',
                message='The LawEdge system has been successfully updated to version 1.0.',
                notification_type='system'
            )
        ]
        
        db.session.add_all(notifications)
        db.session.commit()
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()