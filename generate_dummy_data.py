from app_enhanced import app, db
from models import (
    User, Client, Case, Appointment, Document, TimeEntry, Invoice, Payment, 
    TrustAccount, TrustTransaction, Notification, ActivityLog, Firm, Branch, 
    Permission, RolePermission, Communication, Lead, CaseWorkflow, DocumentVersion, 
    Expense, InvoiceLineItem, ClientPortalUser, DocumentAnalysis, LegalResearch, 
    AutomationRule, SystemSetting, Attendance, UserPerformance
)
from datetime import datetime, timedelta
import random
import os

def generate_dummy_data():
    with app.app_context():
        # Check if data already exists
        if User.query.count() > 10:
            print("Dummy data already exists!")
            return
        
        # Get or create default firm and branch
        firm = Firm.query.first()
        if not firm:
            firm = Firm(
                name='LawEdge Legal Services',
                firm_code='LELS-001',
                subdomain='lawedge',
                address='123 Legal Street, Mumbai, Maharashtra 400001, India',
                phone='+91-22-12345678',
                email='info@lawedge.com',
                website='https://lawedge.com',
                gst_number='27ABCDE1234F1Z5',
                pan_number='ABCDE1234F',
                primary_color='#007bff',
                secondary_color='#6c757d'
            )
            db.session.add(firm)
            db.session.commit()
        
        branch = Branch.query.first()
        if not branch:
            branch = Branch(
                firm_id=firm.id,
                name='Head Office',
                branch_code='HO-001',
                address='123 Legal Street, Mumbai, Maharashtra 400001, India',
                phone='+91-22-12345678',
                email='mumbai@lawedge.com',
                city='Mumbai',
                state='Maharashtra',
                postal_code='400001'
            )
            db.session.add(branch)
            db.session.commit()
        
        # Create additional users
        # Check if users already exist
        existing_users = User.query.all()
        existing_usernames = [user.username for user in existing_users]
        existing_emails = [user.email for user in existing_users]
        
        # Generate unique usernames and emails if needed
        def get_unique_username(base_name):
            counter = 1
            username = base_name
            while username in existing_usernames:
                username = f"{base_name}{counter}"
                counter += 1
            return username
        
        def get_unique_email(base_name):
            counter = 1
            email = f"{base_name}@lawedge.com"
            while email in existing_emails:
                email = f"{base_name}{counter}@lawedge.com"
                counter += 1
            return email
        
        users = [
            User(
                username=get_unique_username('rsharma'),
                email=get_unique_email('rsharma'),
                full_name='Rahul Sharma',
                role='lawyer',
                phone='+91-9876543215',
                address='456 Park Avenue, Delhi, Delhi 110001, India',
                firm_id=firm.id,
                branch_id=branch.id
            ),
            User(
                username=get_unique_username('spatel'),
                email=get_unique_email('spatel'),
                full_name='Priya Patel',
                role='lawyer',
                phone='+91-9876543216',
                address='789 Market Street, Bangalore, Karnataka 560001, India',
                firm_id=firm.id,
                branch_id=branch.id
            ),
            User(
                username=get_unique_username('vverma'),
                email=get_unique_email('vverma'),
                full_name='Vikram Verma',
                role='paralegal',
                phone='+91-9876543217',
                address='101 Business Park, Chennai, Tamil Nadu 600001, India',
                firm_id=firm.id,
                branch_id=branch.id
            ),
            User(
                username=get_unique_username('akumar'),
                email=get_unique_email('akumar'),
                full_name='Ananya Kumar',
                role='staff',
                phone='+91-9876543218',
                address='202 Financial District, Hyderabad, Telangana 500001, India',
                firm_id=firm.id,
                branch_id=branch.id
            ),
            User(
                username=get_unique_username('msingh'),
                email=get_unique_email('msingh'),
                full_name='Manpreet Singh',
                role='finance',
                phone='+91-9876543219',
                address='303 Tech Park, Pune, Maharashtra 411001, India',
                firm_id=firm.id,
                branch_id=branch.id
            )
        ]
        
        for user in users:
            user.set_password('password123')
        
        # Get existing admin user
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.firm_id = firm.id
            admin_user.branch_id = branch.id
        
        db.session.add_all(users)
        db.session.commit()
        
        # Create sample clients
        # Check if clients already exist
        existing_clients = Client.query.all()
        client_numbers = [client.client_number for client in existing_clients]
        
        # Generate new client numbers if needed
        base_number = 100
        while f'CL-2023-{base_number:03d}' in client_numbers:
            base_number += 1
        
        clients = [
            Client(
                client_number=f'CL-2023-{base_number:03d}',
                first_name='Rajesh',
                last_name='Kumar',
                email='rajesh.kumar@email.com',
                phone='+91-9876543220',
                address='123 Residential Area, Mumbai, Maharashtra 400001, India',
                city='Mumbai',
                state='Maharashtra',
                postal_code='400001',
                client_type='individual',
                practice_area='Property Law',
                priority='high',
                assigned_lawyer_id=users[0].id,
                notes='Client interested in property dispute resolution.'
            ),
            Client(
                client_number=f'CL-2023-{base_number+1:03d}',
                first_name='Amita',
                last_name='Shah',
                email='amita.shah@company.com',
                phone='+91-9876543221',
                address='456 Business Park, Bangalore, Karnataka 560001, India',
                city='Bangalore',
                state='Karnataka',
                postal_code='560001',
                company='Tech Solutions Pvt. Ltd.',
                client_type='corporate',
                practice_area='Corporate Law',
                priority='medium',
                assigned_lawyer_id=users[1].id,
                notes='Corporate client for contract review and compliance.'
            ),
            Client(
                client_number=f'CL-2023-{base_number+2:03d}',
                first_name='Sanjay',
                last_name='Verma',
                email='sanjay.v@email.com',
                phone='+91-9876543222',
                address='789 Urban Estate, Delhi, Delhi 110001, India',
                city='Delhi',
                state='Delhi',
                postal_code='110001',
                client_type='individual',
                practice_area='Employment Law',
                priority='low',
                assigned_lawyer_id=users[0].id,
                notes='Employment dispute case.'
            ),
            Client(
                client_number=f'CL-2023-{base_number+3:03d}',
                first_name='Neha',
                last_name='Gupta',
                email='neha.gupta@email.com',
                phone='+91-9876543223',
                address='101 Suburb, Kolkata, West Bengal 700001, India',
                city='Kolkata',
                state='West Bengal',
                postal_code='700001',
                client_type='individual',
                practice_area='Family Law',
                priority='high',
                assigned_lawyer_id=users[1].id,
                notes='Divorce and child custody case.'
            ),
            Client(
                client_number=f'CL-2023-{base_number+4:03d}',
                first_name='Vikram',
                last_name='Malhotra',
                email='vikram.m@enterprise.com',
                phone='+91-9876543224',
                address='202 Industrial Area, Ahmedabad, Gujarat 380001, India',
                city='Ahmedabad',
                state='Gujarat',
                postal_code='380001',
                company='Malhotra Enterprises',
                client_type='corporate',
                practice_area='Intellectual Property',
                priority='medium',
                assigned_lawyer_id=users[0].id,
                notes='Trademark registration case.'
            )
        ]
        
        db.session.add_all(clients)
        db.session.commit()
        
        # Create sample cases
        # Check if cases already exist
        existing_cases = Case.query.all()
        case_numbers = [case.case_number for case in existing_cases]
        
        # Generate new case numbers if needed
        case_base_number = 100
        while f'CASE-2023-{case_base_number:03d}' in case_numbers:
            case_base_number += 1
        
        cases = [
            Case(
                case_number=f'CASE-2023-{case_base_number:03d}',
                title='Property Dispute - Residential Complex',
                description='Dispute regarding ownership of residential property in Mumbai.',
                client_id=clients[0].id,
                assigned_lawyer_id=users[0].id,
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
                case_number=f'CASE-2023-{case_base_number+1:03d}',
                title='Contract Review - Service Agreement',
                description='Review and negotiation of service agreement for Tech Solutions.',
                client_id=clients[1].id,
                assigned_lawyer_id=users[1].id,
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
                case_number=f'CASE-2023-{case_base_number+2:03d}',
                title='Employment Termination Dispute',
                description='Wrongful termination claim against former employer.',
                client_id=clients[2].id,
                assigned_lawyer_id=users[0].id,
                case_type='Employment',
                status='closed',
                stage='Closure',
                date_opened=datetime.utcnow() - timedelta(days=90),
                date_closed=datetime.utcnow() - timedelta(days=10),
                actual_completion=datetime.utcnow() - timedelta(days=10),
                billing_method='hourly',
                hourly_rate=1500.0,
                notes='Employment dispute resolved through mediation.'
            ),
            Case(
                case_number=f'CASE-2023-{case_base_number+3:03d}',
                title='Divorce Proceedings',
                description='Divorce case with child custody and alimony considerations.',
                client_id=clients[3].id,
                assigned_lawyer_id=users[1].id,
                case_type='Family',
                status='in_progress',
                stage='Negotiation',
                date_opened=datetime.utcnow() - timedelta(days=45),
                estimated_completion=datetime.utcnow() + timedelta(days=75),
                billing_method='hourly',
                hourly_rate=1800.0,
                budget=60000.0,
                notes='Complex divorce case with child custody dispute.'
            ),
            Case(
                case_number=f'CASE-2023-{case_base_number+4:03d}',
                title='Trademark Registration',
                description='Trademark registration for company logo and brand name.',
                client_id=clients[4].id,
                assigned_lawyer_id=users[0].id,
                case_type='Intellectual Property',
                status='open',
                stage='Application',
                date_opened=datetime.utcnow() - timedelta(days=20),
                estimated_completion=datetime.utcnow() + timedelta(days=120),
                billing_method='flat_fee',
                budget=35000.0,
                notes='Trademark registration process for Malhotra Enterprises.'
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
                lawyer_id=users[0].id,
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
                lawyer_id=users[0].id,
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
                lawyer_id=users[1].id,
                case_id=cases[1].id,
                appointment_type='Client Meeting',
                start_time=datetime.utcnow() + timedelta(days=2, hours=15),
                end_time=datetime.utcnow() + timedelta(days=2, hours=16),
                is_virtual=True,
                meeting_link='https://zoom.us/j/123456789',
                status='scheduled'
            ),
            Appointment(
                title='Divorce Mediation',
                description='Mediation session for divorce proceedings.',
                client_id=clients[3].id,
                lawyer_id=users[1].id,
                case_id=cases[3].id,
                appointment_type='Mediation',
                start_time=datetime.utcnow() + timedelta(days=3, hours=11),
                end_time=datetime.utcnow() + timedelta(days=3, hours=13),
                location='Mediation Center, Kolkata',
                status='scheduled'
            ),
            Appointment(
                title='Trademark Application Discussion',
                description='Discussion about trademark application process.',
                client_id=clients[4].id,
                lawyer_id=users[0].id,
                case_id=cases[4].id,
                appointment_type='Consultation',
                start_time=datetime.utcnow() + timedelta(days=4, hours=16),
                end_time=datetime.utcnow() + timedelta(days=4, hours=17),
                is_virtual=True,
                meeting_link='https://meet.google.com/abc-defg-hij',
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
                uploaded_by=users[0].id,
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
                uploaded_by=users[1].id,
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
                uploaded_by=users[0].id,
                tags='employment, contract, termination'
            ),
            Document(
                title='Marriage Certificate',
                description='Marriage certificate of the client.',
                filename='marriage_certificate.pdf',
                file_path='uploads/documents/marriage_certificate.pdf',
                file_size=512000,
                file_type='application/pdf',
                category='Evidence',
                case_id=cases[3].id,
                client_id=clients[3].id,
                uploaded_by=users[1].id,
                tags='marriage, certificate, evidence'
            ),
            Document(
                title='Company Logo',
                description='Company logo for trademark registration.',
                filename='company_logo.png',
                file_path='uploads/documents/company_logo.png',
                file_size=256000,
                file_type='image/png',
                category='Evidence',
                case_id=cases[4].id,
                client_id=clients[4].id,
                uploaded_by=users[0].id,
                tags='logo, trademark, brand'
            )
        ]
        
        db.session.add_all(documents)
        db.session.commit()
        
        # Create sample time entries
        time_entries = [
            TimeEntry(
                user_id=users[0].id,
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
                user_id=users[0].id,
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
                user_id=users[1].id,
                case_id=cases[1].id,
                description='Contract review and analysis',
                start_time=datetime.utcnow() - timedelta(days=3, hours=10),
                end_time=datetime.utcnow() - timedelta(days=3, hours=12),
                duration_minutes=120,
                is_billable=True,
                hourly_rate=2000.0,
                status='submitted'
            ),
            TimeEntry(
                user_id=users[1].id,
                case_id=cases[3].id,
                description='Divorce mediation preparation',
                start_time=datetime.utcnow() - timedelta(days=2, hours=13),
                end_time=datetime.utcnow() - timedelta(days=2, hours=15),
                duration_minutes=120,
                is_billable=True,
                hourly_rate=1800.0,
                status='draft'
            ),
            TimeEntry(
                user_id=users[0].id,
                case_id=cases[4].id,
                description='Trademark search and analysis',
                start_time=datetime.utcnow() - timedelta(days=1, hours=11),
                end_time=datetime.utcnow() - timedelta(days=1, hours=13),
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
        # Check if invoices already exist
        existing_invoices = Invoice.query.all()
        invoice_numbers = [invoice.invoice_number for invoice in existing_invoices]
        
        # Generate new invoice numbers if needed
        invoice_base_number = 100
        while f'INV-2023-{invoice_base_number:03d}' in invoice_numbers:
            invoice_base_number += 1
        
        invoices = [
            Invoice(
                invoice_number=f'INV-2023-{invoice_base_number:03d}',
                client_id=clients[0].id,
                case_id=cases[0].id,
                issue_date=datetime.utcnow().date(),
                due_date=(datetime.utcnow() + timedelta(days=30)).date(),
                subtotal=6000.0,
                tax_rate=18.0,
                status='sent'
            ),
            Invoice(
                invoice_number=f'INV-2023-{invoice_base_number+1:03d}',
                client_id=clients[1].id,
                case_id=cases[1].id,
                issue_date=datetime.utcnow().date(),
                due_date=(datetime.utcnow() + timedelta(days=30)).date(),
                subtotal=25000.0,
                tax_rate=18.0,
                status='draft'
            ),
            Invoice(
                invoice_number=f'INV-2023-{invoice_base_number+2:03d}',
                client_id=clients[2].id,
                case_id=cases[2].id,
                issue_date=(datetime.utcnow() - timedelta(days=10)).date(),
                due_date=(datetime.utcnow() + timedelta(days=20)).date(),
                subtotal=15000.0,
                tax_rate=18.0,
                status='paid'
            )
        ]
        
        # Calculate totals
        for invoice in invoices:
            invoice.calculate_total()
        
        db.session.add_all(invoices)
        db.session.commit()
        
        # Create sample payments
        payments = [
            Payment(
                invoice_id=invoices[2].id,
                amount=17700.0,  # 15000 + 18% tax
                payment_date=datetime.utcnow() - timedelta(days=5),
                payment_method='bank_transfer',
                transaction_id='TXN123456789'
            )
        ]
        
        db.session.add_all(payments)
        db.session.commit()
        
        # Create sample trust accounts
        # Check if trust accounts already exist
        existing_trust_accounts = TrustAccount.query.all()
        trust_account_numbers = [account.account_number for account in existing_trust_accounts]
        
        # Generate new trust account numbers if needed
        trust_base_number = 100
        while f'TA-CL-{trust_base_number:03d}' in trust_account_numbers:
            trust_base_number += 1
        
        trust_accounts = [
            TrustAccount(
                client_id=clients[0].id,
                account_number=f'TA-CL-{trust_base_number:03d}',
                balance=25000.0
            ),
            TrustAccount(
                client_id=clients[1].id,
                account_number=f'TA-CL-{trust_base_number+1:03d}',
                balance=50000.0
            )
        ]
        
        db.session.add_all(trust_accounts)
        db.session.commit()
        
        # Create sample trust transactions
        trust_transactions = [
            TrustTransaction(
                trust_account_id=trust_accounts[0].id,
                transaction_type='deposit',
                amount=25000.0,
                description='Initial deposit for property dispute case'
            ),
            TrustTransaction(
                trust_account_id=trust_accounts[1].id,
                transaction_type='deposit',
                amount=50000.0,
                description='Initial deposit for contract review case'
            )
        ]
        
        db.session.add_all(trust_transactions)
        db.session.commit()
        
        # Create sample notifications
        notifications = [
            Notification(
                user_id=users[0].id,
                title='Upcoming Appointment',
                message='You have a client consultation scheduled for tomorrow at 2:00 PM.',
                notification_type='appointment'
            ),
            Notification(
                user_id=users[1].id,
                title='New Case Assigned',
                message='A new case has been assigned to you: Contract Review - Service Agreement.',
                notification_type='case'
            ),
            Notification(
                user_id=admin_user.id,
                title='System Update',
                message='The LawEdge system has been successfully updated to version 1.0.',
                notification_type='system'
            ),
            Notification(
                user_id=users[3].id,
                title='Document Upload',
                message='A new document has been uploaded for the Property Dispute case.',
                notification_type='document'
            ),
            Notification(
                user_id=users[4].id,
                title='Invoice Payment',
                message='Invoice INV-2023-003 has been paid by the client.',
                notification_type='payment'
            )
        ]
        
        db.session.add_all(notifications)
        db.session.commit()
        
        # Create sample activity logs
        activity_logs = [
            ActivityLog(
                user_id=users[0].id,
                action='login',
                resource_type='user',
                details='User logged in to the system',
                ip_address='192.168.1.100',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ),
            ActivityLog(
                user_id=users[1].id,
                action='create',
                resource_type='case',
                resource_id=cases[1].id,
                details='Created new case: Contract Review - Service Agreement',
                ip_address='192.168.1.101',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ),
            ActivityLog(
                user_id=users[3].id,
                action='upload',
                resource_type='document',
                resource_id=documents[0].id,
                details='Uploaded document: Property Title Deed',
                ip_address='192.168.1.102',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ),
            ActivityLog(
                user_id=users[4].id,
                action='create',
                resource_type='invoice',
                resource_id=invoices[0].id,
                details='Created new invoice: INV-2023-001',
                ip_address='192.168.1.103',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ),
            ActivityLog(
                user_id=admin_user.id,
                action='update',
                resource_type='user',
                resource_id=users[2].id,
                details='Updated user profile: Vikram Verma',
                ip_address='192.168.1.104',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
        ]
        
        db.session.add_all(activity_logs)
        db.session.commit()
        
        # Create sample attendance records
        attendance_records = [
            Attendance(
                user_id=users[0].id,
                date=datetime.utcnow().date(),
                check_in_time=datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0),
                check_out_time=datetime.utcnow().replace(hour=17, minute=30, second=0, microsecond=0),
                break_duration_minutes=30,
                status='present'
            ),
            Attendance(
                user_id=users[1].id,
                date=datetime.utcnow().date(),
                check_in_time=datetime.utcnow().replace(hour=8, minute=45, second=0, microsecond=0),
                check_out_time=datetime.utcnow().replace(hour=17, minute=15, second=0, microsecond=0),
                break_duration_minutes=45,
                status='present'
            ),
            Attendance(
                user_id=users[2].id,
                date=datetime.utcnow().date(),
                check_in_time=datetime.utcnow().replace(hour=9, minute=15, second=0, microsecond=0),
                check_out_time=datetime.utcnow().replace(hour=18, minute=0, second=0, microsecond=0),
                break_duration_minutes=30,
                status='present'
            ),
            Attendance(
                user_id=users[3].id,
                date=datetime.utcnow().date(),
                check_in_time=datetime.utcnow().replace(hour=8, minute=30, second=0, microsecond=0),
                check_out_time=datetime.utcnow().replace(hour=17, minute=0, second=0, microsecond=0),
                break_duration_minutes=60,
                status='present'
            ),
            Attendance(
                user_id=users[4].id,
                date=datetime.utcnow().date(),
                check_in_time=datetime.utcnow().replace(hour=9, minute=30, second=0, microsecond=0),
                check_out_time=datetime.utcnow().replace(hour=18, minute=30, second=0, microsecond=0),
                break_duration_minutes=30,
                status='present'
            )
        ]
        
        # Calculate total hours for attendance
        for record in attendance_records:
            record.calculate_total_hours()
        
        db.session.add_all(attendance_records)
        db.session.commit()
        
        # Create sample leads
        # Check if leads already exist
        existing_leads = Lead.query.all()
        lead_numbers = [lead.lead_number for lead in existing_leads]
        
        # Generate new lead numbers if needed
        lead_base_number = 100
        while f'LD-2023-{lead_base_number:03d}' in lead_numbers:
            lead_base_number += 1
        
        leads = [
            Lead(
                lead_number=f'LD-2023-{lead_base_number:03d}',
                first_name='Rakesh',
                last_name='Mehta',
                email='rakesh.mehta@email.com',
                phone='+91-9876543225',
                company='Mehta Constructions',
                practice_area='Property Law',
                case_description='Need legal assistance for a property dispute with a neighbor.',
                source='Website',
                status='contacted',
                priority='high',
                assigned_lawyer_id=users[0].id,
                notes='Potential client for property dispute case. Initial call completed.'
            ),
            Lead(
                lead_number=f'LD-2023-{lead_base_number+1:03d}',
                first_name='Pooja',
                last_name='Reddy',
                email='pooja.reddy@startup.com',
                phone='+91-9876543226',
                company='TechStart Pvt. Ltd.',
                practice_area='Corporate Law',
                case_description='Need help with company registration and compliance.',
                source='Referral',
                status='qualified',
                priority='medium',
                assigned_lawyer_id=users[1].id,
                notes='Referred by existing client. Interested in corporate legal services.'
            ),
            Lead(
                lead_number=f'LD-2023-{lead_base_number+2:03d}',
                first_name='Arun',
                last_name='Nair',
                email='arun.nair@email.com',
                phone='+91-9876543227',
                practice_area='Employment Law',
                case_description='Facing wrongful termination from current employer.',
                source='Advertisement',
                status='new',
                priority='medium',
                assigned_lawyer_id=users[0].id,
                notes='New lead from online advertisement. Needs initial consultation.'
            )
        ]
        
        db.session.add_all(leads)
        db.session.commit()
        
        # Create sample expenses
        expenses = [
            Expense(
                user_id=users[0].id,
                case_id=cases[0].id,
                expense_type='travel',
                description='Travel to court for property dispute hearing',
                amount=500.0,
                currency='INR',
                date_incurred=(datetime.utcnow() - timedelta(days=2)).date(),
                is_billable=True,
                status='approved',
                approved_by=users[4].id,
                approved_date=datetime.utcnow() - timedelta(days=1),
                notes='Taxi fare to and from court'
            ),
            Expense(
                user_id=users[1].id,
                case_id=cases[1].id,
                expense_type='meals',
                description='Business lunch with client for contract discussion',
                amount=1200.0,
                currency='INR',
                date_incurred=(datetime.utcnow() - timedelta(days=3)).date(),
                is_billable=True,
                status='approved',
                approved_by=users[4].id,
                approved_date=datetime.utcnow() - timedelta(days=2),
                notes='Lunch meeting at upscale restaurant'
            ),
            Expense(
                user_id=users[2].id,
                expense_type='supplies',
                description='Stationery and office supplies for case preparation',
                amount=350.0,
                currency='INR',
                date_incurred=(datetime.utcnow() - timedelta(days=5)).date(),
                is_billable=False,
                status='approved',
                approved_by=users[4].id,
                approved_date=datetime.utcnow() - timedelta(days=4),
                notes='Pens, papers, folders, and other supplies'
            )
        ]
        
        db.session.add_all(expenses)
        db.session.commit()
        
        print("Dummy data created successfully!")
        print("\nLogin Credentials:")
        print("Admin: admin / admin123")
        for user in users:
            print(f"{user.role.capitalize()}: {user.username} / password123")

if __name__ == '__main__':
    generate_dummy_data()