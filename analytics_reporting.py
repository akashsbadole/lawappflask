"""
Advanced Analytics & Reporting Module
Implements comprehensive analytics, reporting, and business intelligence for the law firm
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, and_, or_, desc, asc
from collections import defaultdict

# Try to import data visualization libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    MPLIB_AVAILABLE = True
except ImportError:
    MPLIB_AVAILABLE = False

try:
    import seaborn
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

try:
    import plotly.graph_objs as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Advanced analytics and reporting engine"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        # Analytics Configuration
        self.default_timezone = app.config.get('DEFAULT_TIMEZONE', 'Asia/Kolkata')
        self.report_retention_days = app.config.get('REPORT_RETENTION_DAYS', 365)
        self.cache_timeout = app.config.get('ANALYTICS_CACHE_TIMEOUT', 300)  # 5 minutes
        
        # Report Configuration
        self.enable_real_time_analytics = app.config.get('ENABLE_REAL_TIME_ANALYTICS', True)
        self.enable_predictive_analytics = app.config.get('ENABLE_PREDICTIVE_ANALYTICS', True)
        self.enable_custom_reports = app.config.get('ENABLE_CUSTOM_REPORTS', True)
        
        # Visualization Configuration
        self.default_chart_theme = app.config.get('DEFAULT_CHART_THEME', 'plotly_white')
        self.color_palette = app.config.get('COLOR_PALETTE', ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'])
        
        # Initialize cache
        self._cache = {}
    
    def get_firm_overview(self, start_date=None, end_date=None):
        """Get firm overview analytics"""
        try:
            from models import User, Client, Case, Document, Appointment, Invoice, Payment
            
            # Set date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Cache key
            cache_key = f"firm_overview_{start_date}_{end_date}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Calculate metrics
            overview = {}
            
            # User metrics
            total_users = User.query.filter_by(is_active=True).count()
            overview['total_users'] = total_users
            overview['users_by_role'] = self._get_user_distribution()
            
            # Client metrics
            total_clients = Client.query.filter_by(is_active=True).count()
            overview['total_clients'] = total_clients
            overview['new_clients'] = Client.query.filter(
                Client.created_at >= start_date,
                Client.created_at <= end_date,
                Client.is_active == True
            ).count()
            
            # Case metrics
            total_cases = Case.query.count()
            overview['total_cases'] = total_cases
            overview['active_cases'] = Case.query.filter(
                Case.status.in_(['active', 'pending', 'in_progress'])
            ).count()
            overview['new_cases'] = Case.query.filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date
            ).count()
            overview['closed_cases'] = Case.query.filter(
                Case.status == 'closed',
                Case.closed_at >= start_date,
                Case.closed_at <= end_date
            ).count()
            
            # Document metrics
            total_documents = Document.query.count()
            overview['total_documents'] = total_documents
            overview['new_documents'] = Document.query.filter(
                Document.uploaded_at >= start_date,
                Document.uploaded_at <= end_date
            ).count()
            
            # Appointment metrics
            total_appointments = Appointment.query.count()
            overview['total_appointments'] = total_appointments
            overview['scheduled_appointments'] = Appointment.query.filter(
                Appointment.start_time >= start_date,
                Appointment.start_time <= end_date
            ).count()
            
            # Financial metrics
            total_invoices = Invoice.query.count()
            overview['total_invoices'] = total_invoices
            overview['new_invoices'] = Invoice.query.filter(
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            ).count()
            
            # Payment metrics
            total_payments = Payment.query.count()
            overview['total_payments'] = total_payments
            overview['paid_amount'] = self._calculate_total_revenue(start_date, end_date)
            overview['pending_amount'] = self._calculate_pending_revenue(start_date, end_date)
            
            # Performance metrics
            overview['case_resolution_rate'] = self._calculate_case_resolution_rate(start_date, end_date)
            overview['average_case_duration'] = self._calculate_average_case_duration(start_date, end_date)
            overview['billable_hours'] = self._calculate_billable_hours(start_date, end_date)
            overview['collection_rate'] = self._calculate_collection_rate(start_date, end_date)
            
            # Growth metrics
            overview['client_growth_rate'] = self._calculate_growth_rate('clients', start_date, end_date)
            overview['case_growth_rate'] = self._calculate_growth_rate('cases', start_date, end_date)
            overview['revenue_growth_rate'] = self._calculate_revenue_growth_rate(start_date, end_date)
            
            # Productivity metrics
            overview['cases_per_lawyer'] = self._calculate_cases_per_lawyer(start_date, end_date)
            overview['documents_per_case'] = self._calculate_documents_per_case(start_date, end_date)
            overview['appointments_per_client'] = self._calculate_appointments_per_client(start_date, end_date)
            
            # Cache result
            self._cache[cache_key] = overview
            
            return overview
            
        except Exception as e:
            logger.error(f"Error generating firm overview: {str(e)}")
            return {}
    
    def get_lawyer_performance(self, lawyer_id=None, start_date=None, end_date=None):
        """Get lawyer performance analytics"""
        try:
            from models import User, Case, Appointment, ActivityLog, TimeEntry
            
            # Set date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Cache key
            cache_key = f"lawyer_performance_{lawyer_id}_{start_date}_{end_date}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            performance = {}
            
            # Get lawyers
            if lawyer_id:
                lawyers = [User.query.get(lawyer_id)]
            else:
                lawyers = User.query.filter_by(role='lawyer').all()
            
            lawyer_data = []
            for lawyer in lawyers:
                if not lawyer:
                    continue
                
                lawyer_stats = {
                    'id': lawyer.id,
                    'name': lawyer.full_name,
                    'email': lawyer.email
                }
                
                # Case metrics
                lawyer_stats['total_cases'] = Case.query.filter_by(assigned_lawyer_id=lawyer.id).count()
                lawyer_stats['active_cases'] = Case.query.filter(
                    Case.assigned_lawyer_id == lawyer.id,
                    Case.status.in_(['active', 'pending', 'in_progress'])
                ).count()
                lawyer_stats['new_cases'] = Case.query.filter(
                    Case.assigned_lawyer_id == lawyer.id,
                    Case.created_at >= start_date,
                    Case.created_at <= end_date
                ).count()
                lawyer_stats['closed_cases'] = Case.query.filter(
                    Case.assigned_lawyer_id == lawyer.id,
                    Case.status == 'closed',
                    Case.closed_at >= start_date,
                    Case.closed_at <= end_date
                ).count()
                
                # Appointment metrics
                lawyer_stats['total_appointments'] = Appointment.query.filter_by(lawyer_id=lawyer.id).count()
                lawyer_stats['scheduled_appointments'] = Appointment.query.filter(
                    Appointment.lawyer_id == lawyer.id,
                    Appointment.start_time >= start_date,
                    Appointment.start_time <= end_date
                ).count()
                
                # Time tracking metrics
                lawyer_stats['total_hours'] = TimeEntry.query.filter_by(user_id=lawyer.id).count()
                lawyer_stats['billable_hours'] = TimeEntry.query.filter(
                    TimeEntry.user_id == lawyer.id,
                    TimeEntry.is_billable == True
                ).count()
                lawyer_stats['non_billable_hours'] = TimeEntry.query.filter(
                    TimeEntry.user_id == lawyer.id,
                    TimeEntry.is_billable == False
                ).count()
                
                # Performance metrics
                lawyer_stats['cases_per_month'] = self._calculate_lawyer_cases_per_month(lawyer.id, start_date, end_date)
                lawyer_stats['hours_per_case'] = self._calculate_lawyer_hours_per_case(lawyer.id, start_date, end_date)
                lawyer_stats['billable_percentage'] = self._calculate_lawyer_billable_percentage(lawyer.id, start_date, end_date)
                lawyer_stats['utilization_rate'] = self._calculate_lawyer_utilization_rate(lawyer.id, start_date, end_date)
                
                # Financial metrics
                lawyer_stats['total_revenue'] = self._calculate_lawyer_revenue(lawyer.id, start_date, end_date)
                lawyer_stats['average_case_value'] = self._calculate_lawyer_average_case_value(lawyer.id, start_date, end_date)
                lawyer_stats['target_achievement'] = self._calculate_lawyer_target_achievement(lawyer.id, start_date, end_date)
                
                # Activity metrics
                lawyer_stats['login_count'] = ActivityLog.query.filter(
                    ActivityLog.user_id == lawyer.id,
                    ActivityLog.action == 'login_success',
                    ActivityLog.timestamp >= start_date,
                    ActivityLog.timestamp <= end_date
                ).count()
                
                lawyer_stats['document_access'] = ActivityLog.query.filter(
                    ActivityLog.user_id == lawyer.id,
                    ActivityLog.action.like('%document%'),
                    ActivityLog.timestamp >= start_date,
                    ActivityLog.timestamp <= end_date
                ).count()
                
                lawyer_data.append(lawyer_stats)
            
            performance['lawyers'] = lawyer_data
            
            # Calculate team metrics if no specific lawyer
            if not lawyer_id:
                performance['team_metrics'] = {
                    'total_lawyers': len(lawyers),
                    'average_cases_per_lawyer': sum(d['total_cases'] for d in lawyer_data) / len(lawyers) if lawyers else 0,
                    'average_hours_per_lawyer': sum(d['total_hours'] for d in lawyer_data) / len(lawyers) if lawyers else 0,
                    'average_revenue_per_lawyer': sum(d['total_revenue'] for d in lawyer_data) / len(lawyers) if lawyers else 0,
                    'top_performer': max(lawyer_data, key=lambda x: x['total_revenue']) if lawyer_data else None,
                    'improvement_needed': min(lawyer_data, key=lambda x: x['utilization_rate']) if lawyer_data else None
                }
            
            # Cache result
            self._cache[cache_key] = performance
            
            return performance
            
        except Exception as e:
            logger.error(f"Error generating lawyer performance: {str(e)}")
            return {}
    
    def get_case_analytics(self, case_id=None, start_date=None, end_date=None):
        """Get case analytics"""
        try:
            from models import Case, Document, Appointment, ActivityLog
            
            # Set date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Cache key
            cache_key = f"case_analytics_{case_id}_{start_date}_{end_date}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            analytics = {}
            
            # Get cases
            if case_id:
                cases = [Case.query.get(case_id)]
            else:
                cases = Case.query.all()
            
            case_data = []
            for case in cases:
                if not case:
                    continue
                
                case_stats = {
                    'id': case.id,
                    'title': case.title,
                    'case_number': case.case_number,
                    'status': case.status,
                    'priority': case.priority,
                    'practice_area': case.practice_area,
                    'client_id': case.client_id,
                    'assigned_lawyer_id': case.assigned_lawyer_id
                }
                
                # Timeline metrics
                case_stats['created_at'] = case.created_at
                case_stats['updated_at'] = case.updated_at
                if case.closed_at:
                    case_stats['duration'] = (case.closed_at - case.created_at).days
                else:
                    case_stats['duration'] = (datetime.utcnow() - case.created_at).days
                
                # Document metrics
                case_stats['total_documents'] = Document.query.filter_by(case_id=case.id).count()
                case_stats['confidential_documents'] = Document.query.filter(
                    Document.case_id == case.id,
                    Document.is_confidential == True
                ).count()
                
                # Appointment metrics
                case_stats['total_appointments'] = Appointment.query.filter_by(case_id=case.id).count()
                case_stats['upcoming_appointments'] = Appointment.query.filter(
                    Appointment.case_id == case.id,
                    Appointment.start_time >= datetime.utcnow()
                ).count()
                
                # Activity metrics
                case_stats['activity_count'] = ActivityLog.query.filter(
                    ActivityLog.resource_type == 'case',
                    ActivityLog.resource_id == case.id,
                    ActivityLog.timestamp >= start_date,
                    ActivityLog.timestamp <= end_date
                ).count()
                
                # Financial metrics
                case_stats['estimated_value'] = case.get('estimated_value', 0)
                case_stats['actual_value'] = self._calculate_case_actual_value(case.id)
                case_stats['costs'] = self._calculate_case_costs(case.id)
                
                case_data.append(case_stats)
            
            analytics['cases'] = case_data
            
            # Calculate summary metrics if no specific case
            if not case_id:
                analytics['summary'] = {
                    'total_cases': len(cases),
                    'cases_by_status': self._get_cases_by_status(),
                    'cases_by_priority': self._get_cases_by_priority(),
                    'cases_by_practice_area': self._get_cases_by_practice_area(),
                    'average_case_duration': sum(d['duration'] for d in case_data) / len(case_data) if case_data else 0,
                    'average_documents_per_case': sum(d['total_documents'] for d in case_data) / len(case_data) if case_data else 0,
                    'total_estimated_value': sum(d['estimated_value'] for d in case_data),
                    'total_actual_value': sum(d['actual_value'] for d in case_data),
                    'case_closure_rate': len([c for c in case_data if c.get('status') == 'closed']) / len(case_data) * 100 if case_data else 0
                }
            
            # Cache result
            self._cache[cache_key] = analytics
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating case analytics: {str(e)}")
            return {}
    
    def get_financial_analytics(self, start_date=None, end_date=None):
        """Get financial analytics"""
        try:
            from models import Invoice, Payment, Expense, Fee
            
            # Set date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Cache key
            cache_key = f"financial_analytics_{start_date}_{end_date}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            financials = {}
            
            # Revenue metrics
            financials['total_revenue'] = self._calculate_total_revenue(start_date, end_date)
            financials['revenue_by_month'] = self._calculate_revenue_by_month(start_date, end_date)
            financials['revenue_by_source'] = self._calculate_revenue_by_source(start_date, end_date)
            financials['revenue_by_practice_area'] = self._calculate_revenue_by_practice_area(start_date, end_date)
            
            # Invoice metrics
            financials['total_invoices'] = Invoice.query.filter(
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            ).count()
            financials['paid_invoices'] = Invoice.query.filter(
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date,
                Invoice.status == 'paid'
            ).count()
            financials['overdue_invoices'] = Invoice.query.filter(
                Invoice.issue_date <= end_date,
                Invoice.due_date < datetime.utcnow(),
                Invoice.status != 'paid'
            ).count()
            
            # Payment metrics
            financials['total_payments'] = Payment.query.filter(
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).count()
            financials['payment_methods'] = self._get_payment_methods_distribution(start_date, end_date)
            financials['average_payment_amount'] = self._calculate_average_payment_amount(start_date, end_date)
            
            # Expense metrics
            financials['total_expenses'] = self._calculate_total_expenses(start_date, end_date)
            financials['expenses_by_category'] = self._calculate_expenses_by_category(start_date, end_date)
            
            # Profitability metrics
            financials['gross_profit'] = financials['total_revenue'] - financials['total_expenses']
            financials['profit_margin'] = (financials['gross_profit'] / financials['total_revenue'] * 100) if financials['total_revenue'] > 0 else 0
            financials['collection_rate'] = self._calculate_collection_rate(start_date, end_date)
            
            # Growth metrics
            financials['revenue_growth_rate'] = self._calculate_revenue_growth_rate(start_date, end_date)
            financials['profit_growth_rate'] = self._calculate_profit_growth_rate(start_date, end_date)
            
            # Cash flow metrics
            financials['cash_in'] = self._calculate_cash_in(start_date, end_date)
            financials['cash_out'] = self._calculate_cash_out(start_date, end_date)
            financials['net_cash_flow'] = financials['cash_in'] - financials['cash_out']
            
            # Cache result
            self._cache[cache_key] = financials
            
            return financials
            
        except Exception as e:
            logger.error(f"Error generating financial analytics: {str(e)}")
            return {}
    
    def get_client_analytics(self, client_id=None, start_date=None, end_date=None):
        """Get client analytics"""
        try:
            from models import Client, Case, Invoice, Payment, Document
            
            # Set date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Cache key
            cache_key = f"client_analytics_{client_id}_{start_date}_{end_date}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            analytics = {}
            
            # Get clients
            if client_id:
                clients = [Client.query.get(client_id)]
            else:
                clients = Client.query.filter_by(is_active=True).all()
            
            client_data = []
            for client in clients:
                if not client:
                    continue
                
                client_stats = {
                    'id': client.id,
                    'name': client.full_name,
                    'email': client.email,
                    'phone': client.phone
                }
                
                # Case metrics
                client_stats['total_cases'] = Case.query.filter_by(client_id=client.id).count()
                client_stats['active_cases'] = Case.query.filter(
                    Case.client_id == client.id,
                    Case.status.in_(['active', 'pending', 'in_progress'])
                ).count()
                client_stats['new_cases'] = Case.query.filter(
                    Case.client_id == client.id,
                    Case.created_at >= start_date,
                    Case.created_at <= end_date
                ).count()
                client_stats['closed_cases'] = Case.query.filter(
                    Case.client_id == client.id,
                    Case.status == 'closed',
                    Case.closed_at >= start_date,
                    Case.closed_at <= end_date
                ).count()
                
                # Financial metrics
                client_stats['total_invoices'] = Invoice.query.filter_by(client_id=client.id).count()
                client_stats['total_revenue'] = self._calculate_client_revenue(client.id, start_date, end_date)
                client_stats['pending_amount'] = self._calculate_client_pending_amount(client.id, end_date)
                client_stats['payment_history'] = self._get_client_payment_history(client.id, start_date, end_date)
                
                # Engagement metrics
                client_stats['case_duration'] = self._calculate_average_client_case_duration(client.id, start_date, end_date)
                client_stats['document_count'] = Document.query.join(Case).filter(
                    Case.client_id == client.id
                ).count()
                client_stats['appointment_count'] = Appointment.query.filter_by(client_id=client.id).count()
                
                client_data.append(client_stats)
            
            analytics['clients'] = client_data
            
            # Calculate summary metrics if no specific client
            if not client_id:
                analytics['summary'] = {
                    'total_clients': len(clients),
                    'new_clients': len([c for c in client_data if c.get('new_cases', 0) > 0]),
                    'active_clients': len([c for c in client_data if c.get('active_cases', 0) > 0]),
                    'average_revenue_per_client': sum(c['total_revenue'] for c in client_data) / len(client_data) if client_data else 0,
                    'average_cases_per_client': sum(c['total_cases'] for c in client_data) / len(client_data) if client_data else 0,
                    'top_clients_by_revenue': sorted(client_data, key=lambda x: x['total_revenue'], reverse=True)[:10],
                    'clients_at_risk': [c for c in client_data if c.get('pending_amount', 0) > 10000]
                }
            
            # Cache result
            self._cache[cache_key] = analytics
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating client analytics: {str(e)}")
            return {}
    
    def generate_report(self, report_type, start_date=None, end_date=None, format='json'):
        """Generate analytics report"""
        try:
            report_data = {}
            
            if report_type == 'firm_overview':
                report_data = self.get_firm_overview(start_date, end_date)
                report_data['report_type'] = 'firm_overview'
                report_data['generated_at'] = datetime.utcnow().isoformat()
                
            elif report_type == 'lawyer_performance':
                report_data = self.get_lawyer_performance(start_date=start_date, end_date=end_date)
                report_data['report_type'] = 'lawyer_performance'
                report_data['generated_at'] = datetime.utcnow().isoformat()
                
            elif report_type == 'case_analytics':
                report_data = self.get_case_analytics(start_date=start_date, end_date=end_date)
                report_data['report_type'] = 'case_analytics'
                report_data['generated_at'] = datetime.utcnow().isoformat()
                
            elif report_type == 'financial_analytics':
                report_data = self.get_financial_analytics(start_date=start_date, end_date=end_date)
                report_data['report_type'] = 'financial_analytics'
                report_data['generated_at'] = datetime.utcnow().isoformat()
                
            elif report_type == 'client_analytics':
                report_data = self.get_client_analytics(start_date=start_date, end_date=end_date)
                report_data['report_type'] = 'client_analytics'
                report_data['generated_at'] = datetime.utcnow().isoformat()
                
            else:
                return {'error': f'Unknown report type: {report_type}'}
            
            # Format report based on format
            if format == 'json':
                return report_data
            elif format == 'csv':
                return self._format_csv_report(report_data, report_type)
            elif format == 'excel':
                return self._format_excel_report(report_data, report_type)
            elif format == 'pdf':
                return self._format_pdf_report(report_data, report_type)
            else:
                return report_data
                
        except Exception as e:
            logger.error(f"Error generating report {report_type}: {str(e)}")
            return {'error': f'Error generating report: {str(e)}'}
    
    def create_dashboard_data(self, dashboard_type='overview'):
        """Create dashboard data for visualization"""
        try:
            dashboard_data = {}
            
            if dashboard_type == 'overview':
                # Get recent data for overview dashboard
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                
                overview = self.get_firm_overview(start_date, end_date)
                financials = self.get_financial_analytics(start_date, end_date)
                
                dashboard_data = {
                    'overview': overview,
                    'financials': financials,
                    'recent_activity': self._get_recent_activity(limit=10),
                    'key_metrics': {
                        'revenue_trend': self._get_revenue_trend(),
                        'case_trend': self._get_case_trend(),
                        'client_trend': self._get_client_trend()
                    },
                    'alerts': self._get_analytics_alerts()
                }
                
            elif dashboard_type == 'financial':
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                
                financials = self.get_financial_analytics(start_date, end_date)
                dashboard_data = {
                    'financials': financials,
                    'charts': {
                        'revenue_by_month': financials.get('revenue_by_month', []),
                        'revenue_by_source': financials.get('revenue_by_source', {}),
                        'payment_methods': financials.get('payment_methods', {}),
                        'expenses_by_category': financials.get('expenses_by_category', {})
                    },
                    'kpi': {
                        'total_revenue': financials.get('total_revenue', 0),
                        'collection_rate': financials.get('collection_rate', 0),
                        'profit_margin': financials.get('profit_margin', 0),
                        'growth_rate': financials.get('revenue_growth_rate', 0)
                    }
                }
                
            elif dashboard_type == 'performance':
                performance = self.get_lawyer_performance(start_date=start_date, end_date=end_date)
                dashboard_data = {
                    'performance': performance,
                    'charts': {
                        'lawyer_performance': performance.get('lawyers', []),
                        'team_metrics': performance.get('team_metrics', {})
                    },
                    'kpi': {
                        'average_cases_per_lawyer': performance.get('team_metrics', {}).get('average_cases_per_lawyer', 0),
                        'average_revenue_per_lawyer': performance.get('team_metrics', {}).get('average_revenue_per_lawyer', 0),
                        'top_performer': performance.get('team_metrics', {}).get('top_performer'),
                        'utilization_rate': performance.get('team_metrics', {}).get('average_utilization_rate', 0)
                    }
                }
                
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error creating dashboard data {dashboard_type}: {str(e)}")
            return {}
    
    def _get_user_distribution(self):
        """Get user distribution by role"""
        try:
            from models import User
            
            distribution = {}
            roles = ['admin', 'lawyer', 'staff', 'assistant']
            
            for role in roles:
                count = User.query.filter_by(role=role, is_active=True).count()
                distribution[role] = count
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting user distribution: {str(e)}")
            return {}
    
    def _calculate_total_revenue(self, start_date, end_date):
        """Calculate total revenue for date range"""
        try:
            from models import db, Invoice
            
            total = db.session.query(func.sum(Invoice.total)).filter(
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date,
                Invoice.status == 'paid'
            ).scalar() or 0
            
            return total
            
        except Exception as e:
            logger.error(f"Error calculating total revenue: {str(e)}")
            return 0
    
    def _calculate_pending_revenue(self, start_date, end_date):
        """Calculate pending revenue for date range"""
        try:
            from models import Invoice
            
            total = db.session.query(func.sum(Invoice.total)).filter(
                Invoice.issue_date <= end_date,
                Invoice.due_date >= start_date,
                Invoice.status != 'paid'
            ).scalar() or 0
            
            return total
            
        except Exception as e:
            logger.error(f"Error calculating pending revenue: {str(e)}")
            return 0
    
    def _calculate_case_resolution_rate(self, start_date, end_date):
        """Calculate case resolution rate"""
        try:
            from models import Case
            
            total_cases = Case.query.filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date
            ).count()
            
            if total_cases == 0:
                return 0
            
            closed_cases = Case.query.filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date,
                Case.status == 'closed',
                Case.closed_at >= start_date,
                Case.closed_at <= end_date
            ).count()
            
            return (closed_cases / total_cases) * 100
            
        except Exception as e:
            logger.error(f"Error calculating case resolution rate: {str(e)}")
            return 0
    
    def _calculate_average_case_duration(self, start_date, end_date):
        """Calculate average case duration"""
        try:
            from models import Case
            
            cases = Case.query.filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date,
                Case.status == 'closed',
                Case.closed_at >= start_date,
                Case.closed_at <= end_date
            ).all()
            
            if not cases:
                return 0
            
            total_duration = sum((case.closed_at - case.created_at).days for case in cases)
            return total_duration / len(cases)
            
        except Exception as e:
            logger.error(f"Error calculating average case duration: {str(e)}")
            return 0
    
    def _calculate_billable_hours(self, start_date, end_date):
        """Calculate billable hours"""
        try:
            from models import db, TimeEntry
            
            total = db.session.query(func.sum(TimeEntry.hours)).filter(
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date,
                TimeEntry.is_billable == True
            ).scalar() or 0
            
            return total
            
        except Exception as e:
            logger.error(f"Error calculating billable hours: {str(e)}")
            return 0
    
    def _calculate_collection_rate(self, start_date, end_date):
        """Calculate collection rate"""
        try:
            from models import Invoice, Payment
            
            total_invoiced = Invoice.query.filter(
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            ).count()
            
            if total_invoiced == 0:
                return 0
            
            total_paid = Invoice.query.filter(
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date,
                Invoice.status == 'paid'
            ).count()
            
            return (total_paid / total_invoiced) * 100
            
        except Exception as e:
            logger.error(f"Error calculating collection rate: {str(e)}")
            return 0
    
    def _calculate_growth_rate(self, entity_type, start_date, end_date):
        """Calculate growth rate for an entity type"""
        try:
            if entity_type == 'clients':
                from models import Client
                
                current_period = Client.query.filter(
                    Client.created_at >= start_date,
                    Client.created_at <= end_date,
                    Client.is_active == True
                ).count()
            elif entity_type == 'cases':
                from models import Case
                
                current_period = Case.query.filter(
                    Case.created_at >= start_date,
                    Case.created_at <= end_date
                ).count()
            else:
                return 0
            
            # Calculate growth rate
            previous_end = start_date - timedelta(days=30)
            previous_start = previous_end - timedelta(days=30)
            
            if entity_type == 'clients':
                previous_period = Client.query.filter(
                    Client.created_at >= previous_start,
                    Client.created_at <= previous_end,
                    Client.is_active == True
                ).count()
            else:
                previous_period = 0
            
            if previous_period == 0:
                return 0
            
            growth_rate = ((current_period - previous_period) / previous_period) * 100
            return growth_rate
            
        except Exception as e:
            logger.error(f"Error calculating growth rate for {entity_type}: {str(e)}")
            return 0
    
    def _calculate_revenue_growth_rate(self, start_date, end_date):
        """Calculate revenue growth rate"""
        try:
            current_revenue = self._calculate_total_revenue(start_date, end_date)
            
            previous_end = start_date - timedelta(days=30)
            previous_start = previous_end - timedelta(days=30)
            previous_revenue = self._calculate_total_revenue(previous_start, previous_end)
            
            if previous_revenue == 0:
                return 0
            
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
            return growth_rate
            
        except Exception as e:
            logger.error(f"Error calculating revenue growth rate: {str(e)}")
            return 0
    
    def _calculate_cases_per_lawyer(self, start_date, end_date):
        """Calculate average cases per lawyer"""
        try:
            from models import User, Case
            
            active_lawyers = User.query.filter_by(role='lawyer', is_active=True).count()
            
            if active_lawyers == 0:
                return 0
            
            total_cases = Case.query.filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date
            ).count()
            
            return total_cases / active_lawyers
            
        except Exception as e:
            logger.error(f"Error calculating cases per lawyer: {str(e)}")
            return 0
    
    def _calculate_documents_per_case(self, start_date, end_date):
        """Calculate average documents per case"""
        try:
            from models import Case, Document
            
            total_cases = Case.query.filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date
            ).count()
            
            if total_cases == 0:
                return 0
            
            total_documents = Document.query.join(Case).filter(
                Case.created_at >= start_date,
                Case.created_at <= end_date
            ).count()
            
            return total_documents / total_cases
            
        except Exception as e:
            logger.error(f"Error calculating documents per case: {str(e)}")
            return 0
    
    def _calculate_appointments_per_client(self, start_date, end_date):
        """Calculate average appointments per client"""
        try:
            from models import Client, Appointment
            
            active_clients = Client.query.filter_by(is_active=True).count()
            
            if active_clients == 0:
                return 0
            
            total_appointments = Appointment.query.filter(
                Appointment.start_time >= start_date,
                Appointment.start_time <= end_date
            ).count()
            
            return total_appointments / active_clients
            
        except Exception as e:
            logger.error(f"Error calculating appointments per client: {str(e)}")
            return 0
    
    def _get_recent_activity(self, limit=10):
        """Get recent activity"""
        try:
            from models import ActivityLog
            
            activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
            
            activity_list = []
            for activity in activities:
                activity_list.append({
                    'id': activity.id,
                    'user_id': activity.user_id,
                    'action': activity.action,
                    'resource_type': activity.resource_type,
                    'details': activity.details,
                    'timestamp': activity.timestamp.isoformat(),
                    'ip_address': activity.ip_address
                })
            
            return activity_list
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    def _get_analytics_alerts(self):
        """Get analytics alerts"""
        try:
            alerts = []
            
            # Check for overdue invoices
            from models import Invoice
            
            overdue_invoices = Invoice.query.filter(
                Invoice.due_date < datetime.utcnow(),
                Invoice.status != 'paid'
            ).count()
            
            if overdue_invoices > 10:
                alerts.append({
                    'type': 'overdue_invoices',
                    'level': 'high',
                    'message': f'{overdue_invoices} invoices are overdue',
                    'count': overdue_invoices
                })
            elif overdue_invoices > 5:
                alerts.append({
                    'type': 'overdue_invoices',
                    'level': 'medium',
                    'message': f'{overdue_invoices} invoices are overdue',
                    'count': overdue_invoices
                })
            
            # Check for low collection rate
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            collection_rate = self._calculate_collection_rate(start_date, end_date)
            
            if collection_rate < 70:
                alerts.append({
                    'type': 'low_collection_rate',
                    'level': 'high',
                    'message': f'Collection rate is {collection_rate:.1f}% (below target)',
                    'rate': collection_rate
                })
            elif collection_rate < 85:
                alerts.append({
                    'type': 'low_collection_rate',
                    'level': 'medium',
                    'message': f'Collection rate is {collection_rate:.1f}% (below target)',
                    'rate': collection_rate
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting analytics alerts: {str(e)}")
            return []
    
    def _get_revenue_trend(self, months=6):
        """Get revenue trend"""
        try:
            from models import Invoice
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            trend = []
            current_date = start_date
            
            while current_date <= end_date:
                period_end = current_date + timedelta(days=30)
                if period_end > end_date:
                    period_end = end_date
                
                revenue = self._calculate_total_revenue(current_date, period_end)
                
                trend.append({
                    'month': current_date.strftime('%Y-%m'),
                    'revenue': revenue,
                    'period_start': current_date.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d')
                })
                
                current_date = period_end + timedelta(days=1)
            
            return trend
            
        except Exception as e:
            logger.error(f"Error getting revenue trend: {str(e)}")
            return []
    
    def _get_case_trend(self, months=6):
        """Get case trend"""
        try:
            from models import Case
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            trend = []
            current_date = start_date
            
            while current_date <= end_date:
                period_end = current_date + timedelta(days=30)
                if period_end > end_date:
                    period_end = end_date
                
                new_cases = Case.query.filter(
                    Case.created_at >= current_date,
                    Case.created_at <= period_end
                ).count()
                
                closed_cases = Case.query.filter(
                    Case.created_at >= current_date,
                    Case.created_at <= period_end,
                    Case.status == 'closed'
                ).count()
                
                trend.append({
                    'month': current_date.strftime('%Y-%m'),
                    'new_cases': new_cases,
                    'closed_cases': closed_cases,
                    'period_start': current_date.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d')
                })
                
                current_date = period_end + timedelta(days=1)
            
            return trend
            
        except Exception as e:
            logger.error(f"Error getting case trend: {str(e)}")
            return []
    
    def _get_client_trend(self, months=6):
        """Get client trend"""
        try:
            from models import Client
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            trend = []
            current_date = start_date
            
            while current_date <= end_date:
                period_end = current_date + timedelta(days=30)
                if period_end > end_date:
                    period_end = end_date
                
                new_clients = Client.query.filter(
                    Client.created_at >= current_date,
                    Client.created_at <= period_end,
                    Client.is_active == True
                ).count()
                
                trend.append({
                    'month': current_date.strftime('%Y-%m'),
                    'new_clients': new_clients,
                    'period_start': current_date.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d')
                })
                
                current_date = period_end + timedelta(days=1)
            
            return trend
            
        except Exception as e:
            logger.error(f"Error getting client trend: {str(e)}")
            return []
    
    def _format_csv_report(self, data, report_type):
        """Format report as CSV"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            
            if report_type == 'firm_overview':
                writer = csv.writer(output)
                
                # Write headers
                writer.writerow(['Metric', 'Value'])
                
                # Write data
                overview = data.get('overview', {})
                for key, value in overview.items():
                    if isinstance(value, (int, float)):
                        writer.writerow([key, value])
                    else:
                        writer.writerow([key, str(value)])
            
            # Return CSV content
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error formatting CSV report: {str(e)}")
            return ""
    
    def _format_excel_report(self, data, report_type):
        """Format report as Excel"""
        try:
            import pandas as pd
            
            if report_type == 'firm_overview':
                # Create DataFrame
                overview = data.get('overview', {})
                df = pd.DataFrame(list(overview.items()), columns=['Metric', 'Value'])
                
                # Convert to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Firm Overview', index=False)
                
                return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error formatting Excel report: {str(e)}")
            return ""
    
    def _format_pdf_report(self, data, report_type):
        """Format report as PDF"""
        try:
            # This would require a PDF library like ReportLab
            # For now, return empty string
            return ""
            
        except Exception as e:
            logger.error(f"Error formatting PDF report: {str(e)}")
            return ""
    
    def clear_cache(self):
        """Clear analytics cache"""
        self._cache.clear()
        logger.info("Analytics cache cleared")

# Initialize analytics engine
analytics_engine = AnalyticsEngine()
