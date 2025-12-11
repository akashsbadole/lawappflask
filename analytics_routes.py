"""
Analytics Routes and Dashboard
Provides web interface for analytics, reporting, and business intelligence
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, send_file, make_response
from functools import wraps
from datetime import datetime, timedelta
from models import db, User, Client, Case, Document, Appointment, Invoice, Payment, ActivityLog
from analytics_reporting import analytics_engine
import logging

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)

# Configure logging
logger = logging.getLogger(__name__)

def analytics_login_required(f):
    """Decorator to require analytics login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/auth/login')
        
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['admin', 'lawyer', 'manager']:
            flash('Access denied. Admin/Lawyer access required.', 'danger')
            return redirect('/dashboard')
        
        return f(*args, **kwargs)
    return decorated_function

# Dashboard Routes
@analytics_bp.route('/')
@analytics_bp.route('/dashboard')
@analytics_login_required
def analytics_dashboard():
    """Main analytics dashboard"""
    try:
        # Get dashboard data type from request
        dashboard_type = request.args.get('type', 'overview')
        
        # Create dashboard data
        dashboard_data = analytics_engine.create_dashboard_data(dashboard_type)
        
        if not dashboard_data:
            flash('Error loading dashboard data', 'danger')
            return render_template('analytics/error.html', error='Failed to load dashboard data')
        
        return render_template('analytics/dashboard.html',
                             dashboard_type=dashboard_type,
                             dashboard_data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error loading analytics dashboard: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/overview')
@analytics_login_required
def analytics_overview():
    """Firm overview analytics"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        overview = analytics_engine.get_firm_overview(start_date, end_date)
        
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Error getting firm overview: {str(e)}")
        return jsonify({'error': str(e)})

# Firm Overview
@analytics_bp.route('/firm-overview')
@analytics_login_required
def analytics_firm_overview():
    """Firm overview page"""
    try:
        return render_template('analytics/firm_overview.html')
        
    except Exception as e:
        logger.error(f"Error loading firm overview page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/firm-overview')
@analytics_login_required
def analytics_firm_overview_api():
    """Firm overview API endpoint"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        overview = analytics_engine.get_firm_overview(start_date, end_date)
        
        return jsonify({'success': True, 'data': overview})
        
    except Exception as e:
        logger.error(f"Error getting firm overview: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Lawyer Performance
@analytics_bp.route('/lawyer-performance')
@analytics_login_required
def analytics_lawyer_performance():
    """Lawyer performance page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        performance = analytics_engine.get_lawyer_performance(start_date, end_date)
        
        return render_template('analytics/lawyer_performance.html',
                             performance=performance,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading lawyer performance page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/lawyer-performance')
@analytics_login_required
def analytics_lawyer_performance_api():
    """Lawyer performance API endpoint"""
    try:
        lawyer_id = request.args.get('lawyer_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        performance = analytics_engine.get_lawyer_performance(
            int(lawyer_id) if lawyer_id else None,
            start_date, end_date
        )
        
        return jsonify({'success': True, 'data': performance})
        
    except Exception as e:
        logger.error(f"Error getting lawyer performance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@analytics_bp.route('/lawyer/<int:lawyer_id>')
@analytics_login_required
def analytics_lawyer_detail(lawyer_id):
    """Individual lawyer performance page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data for specific lawyer
        performance = analytics_engine.get_lawyer_performance(lawyer_id, start_date, end_date)
        
        if not performance or not performance.get('lawyers'):
            flash('Lawyer not found', 'danger')
            return redirect(url_for('analytics.lawyer_performance'))
        
        lawyer_data = performance['lawyers'][0]
        
        return render_template('analytics/lawyer_detail.html',
                             lawyer=lawyer_data,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading lawyer detail page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

# Case Analytics
@analytics_bp.route('/case-analytics')
@analytics_login_required
def analytics_case_analytics():
    """Case analytics page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        case_analytics = analytics_engine.get_case_analytics(start_date, end_date)
        
        return render_template('analytics/case_analytics.html',
                             analytics=case_analytics,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading case analytics page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/case-analytics')
@analytics_login_required
def analytics_case_analytics_api():
    """Case analytics API endpoint"""
    try:
        case_id = request.args.get('case_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        case_analytics = analytics_engine.get_case_analytics(
            int(case_id) if case_id else None,
            start_date, end_date
        )
        
        return jsonify({'success': True, 'data': case_analytics})
        
    except Exception as e:
        logger.error(f"Error getting case analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@analytics_bp.route('/case/<int:case_id>')
@analytics_login_required
def analytics_case_detail(case_id):
    """Individual case analytics page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data for specific case
        case_analytics = analytics_engine.get_case_analytics(case_id, start_date, end_date)
        
        if not case_analytics or not case_analytics.get('cases'):
            flash('Case not found', 'danger')
            return redirect(url_for('analytics.case_analytics'))
        
        case_data = case_analytics['cases'][0]
        
        return render_template('analytics/case_detail.html',
                             case=case_data,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading case detail page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

# Financial Analytics
@analytics_bp.route('/financial-analytics')
@analytics_login_required
def analytics_financial_analytics():
    """Financial analytics page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        financials = analytics_engine.get_financial_analytics(start_date, end_date)
        
        return render_template('analytics/financial_analytics.html',
                             financials=financials,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading financial analytics page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/financial-analytics')
@analytics_login_required
def analytics_financial_analytics_api():
    """Financial analytics API endpoint"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        financials = analytics_engine.get_financial_analytics(start_date, end_date)
        
        return jsonify({'success': True, 'data': financials})
        
    except Exception as e:
        logger.error(f"Error getting financial analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Client Analytics
@analytics_bp.route('/client-analytics')
@analytics_login_required
def analytics_client_analytics():
    """Client analytics page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        client_analytics = analytics_engine.get_client_analytics(start_date, end_date)
        
        return render_template('analytics/client_analytics.html',
                             analytics=client_analytics,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading client analytics page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/client-analytics')
@analytics_login_required
def analytics_client_analytics_api():
    """Client analytics API endpoint"""
    try:
        client_id = request.args.get('client_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        client_analytics = analytics_engine.get_client_analytics(
            int(client_id) if client_id else None,
            start_date, end_date
        )
        
        return jsonify({'success': True, 'data': client_analytics})
        
    except Exception as e:
        logger.error(f"Error getting client analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@analytics_bp.route('/client/<int:client_id>')
@analytics_login_required
def analytics_client_details(client_id):
    """Individual client analytics page"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data for specific client
        client_analytics = analytics_engine.get_client_analytics(client_id, start_date, end_date)
        
        if not client_analytics or not client_analytics.get('clients'):
            flash('Client not found', 'danger')
            return redirect(url_for('analytics.client_analytics'))
        
        client_data = client_analytics['clients'][0]
        
        return render_template('analytics/client_detail.html',
                             client=client_data,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logger.error(f"Error loading client detail page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

# Reports
@analytics_bp.route('/reports')
@analytics_login_required
def analytics_reports():
    """Reports page"""
    try:
        return render_template('analytics/reports.html')
        
    except Exception as e:
        logger.error(f"Error loading reports page: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/generate-report')
@analytics_login_required
def analytics_generate_report():
    """Generate report API endpoint"""
    try:
        report_type = request.args.get('type', 'firm_overview')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        format_type = request.args.get('format', 'json')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Generate report
        report_data = analytics_engine.generate_report(
            report_type,
            start_date,
            end_date,
            format_type
        )
        
        if format_type == 'json':
            return jsonify(report_data)
        elif format_type == 'csv':
            response = make_response(report_data, mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
            return response
        elif format_type == 'excel':
            response = make_response(report_data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'
            return response
        elif format_type == 'pdf':
            response = make_response(report_data, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.pdf'
            return response
        else:
            return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@analytics_bp.route('/download-report/<report_type>')
@analytics_login_required
def analytics_download_report(report_type):
    """Download report"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        format_type = request.args.get('format', 'csv')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Generate report
        report_data = analytics_engine.generate_report(
            report_type,
            start_date,
            end_date,
            format_type
        )
        
        if format_type == 'csv':
            response = make_response(report_data, mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
            return response
        elif format_type == 'excel':
            response = make_response(report_data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'
            return response
        elif format_type == 'pdf':
            response = make_response(report_data, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.pdf'
            return response
        else:
            # Default to CSV
            response = make_response(report_data, mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
            return response
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash('Error downloading report', 'danger')
        return redirect(url_for('analytics.reports'))

# Charts and Visualizations
@analytics_bp.route('/api/charts/<chart_type>')
@analytics_login_required
def analytics_chart(chart_type):
    """Get chart data"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Create dashboard data to get chart data
        dashboard_data = analytics_engine.create_dashboard_data('overview')
        
        if chart_type == 'revenue_trend':
            return jsonify(dashboard_data.get('key_metrics', {}).get('revenue_trend', []))
        elif chart_type == 'case_trend':
            return jsonify(dashboard_data.get('key_metrics', {}).get('case_trend', []))
        elif chart_type == 'client_trend':
            return jsonify(dashboard_data.get('key_metrics', {}).get('client_trend', []))
        elif chart_type == 'financial_kpi':
            financials = dashboard_data.get('financials', {})
            return jsonify({
                'total_revenue': financials.get('total_revenue', 0),
                'collection_rate': financials.get('collection_rate', 0),
                'profit_margin': financials.get('profit_margin', 0),
                'growth_rate': financials.get('growth_rate', 0)
            })
        else:
            return jsonify({'error': f'Unknown chart type: {chart_type}'})
        
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({'error': f'Error getting chart data: {str(e)}'})

# AJAX Endpoints
@analytics_bp.route('/ajax/refresh-dashboard/<dashboard_type>')
@analytics_login_required
def analytics_refresh_dashboard(dashboard_type):
    """Refresh dashboard data"""
    try:
        # Clear cache to force fresh data
        analytics_engine.clear_cache()
        
        # Get fresh dashboard data
        dashboard_data = analytics_engine.create_dashboard_data(dashboard_type)
        
        return jsonify({'success': True, 'data': dashboard_data})
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@analytics_bp.route('/ajax/get-metrics')
@analytics_login_required
def analytics_get_metrics():
    """Get key metrics"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get overview for key metrics
        overview = analytics_engine.get_firm_overview(start_date, end_date)
        
        metrics = {
            'total_clients': overview.get('total_clients', 0),
            'total_cases': overview.get('total_cases', 0),
            'total_revenue': overview.get('paid_amount', 0),
            'collection_rate': overview.get('collection_rate', 0),
            'case_resolution_rate': overview.get('case_resolution_rate', 0),
            'new_clients': overview.get('new_clients', 0),
            'new_cases': overview.get('new_cases', 0),
            'pending_amount': overview.get('pending_amount', 0)
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)})

@analytics_bp.route('/ajax/get-alerts')
@analytics_login_required
def analytics_get_alerts():
    """Get analytics alerts"""
    try:
        # Create dashboard data to get alerts
        dashboard_data = analytics_engine.create_dashboard_data('overview')
        
        return jsonify(dashboard_data.get('alerts', []))
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)})

# Settings and Configuration
@analytics_bp.route('/settings')
@analytics_login_required
def analytics_settings():
    """Analytics settings page"""
    try:
        user = User.query.get(session['user_id'])
        
        if user.role != 'admin':
            flash('Access denied. Admin access required.', 'danger')
            return redirect('/dashboard')
        
        return render_template('analytics/settings.html')
        
    except Exception as e:
        logger.error(f"Error loading analytics settings: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

@analytics_bp.route('/api/clear-cache')
@analytics_login_required
def analytics_clear_cache():
    """Clear analytics cache"""
    try:
        analytics_engine.clear_cache()
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Export Data
@analytics_bp.route('/export/<export_type>')
@analytics_login_required
def analytics_export(export_type):
    """Export data"""
    try:
        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        format_type = request.args.get('format', 'csv')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.utcnow()
        
        # Get data based on export type
        if export_type == 'clients':
            client_analytics = analytics_engine.get_client_analytics(start_date, end_date)
            data = client_analytics.get('clients', [])
            
            # Create CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Client ID', 'Name', 'Email', 'Phone', 'Total Cases', 'Active Cases', 'Total Revenue', 'Pending Amount'])
            
            # Write data
            for client in data:
                writer.writerow([
                    client.get('id', ''),
                    client.get('name', ''),
                    client.get('email', ''),
                    client.get('phone', ''),
                    client.get('total_cases', 0),
                    client.get('active_cases', 0),
                    client.get('total_revenue', 0),
                    client.get('pending_amount', 0)
                ])
            
            response = make_response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = 'attachment; filename=clients_export.csv'
            return response
            
        elif export_type == 'cases':
            case_analytics = analytics_engine.get_case_analytics(start_date, end_date)
            data = case_analytics.get('cases', [])
            
            # Create CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Case ID', 'Title', 'Case Number', 'Status', 'Priority', 'Practice Area', 'Client ID', 'Lawyer ID', 'Duration', 'Total Documents', 'Estimated Value', 'Actual Value'])
            
            # Write data
            for case in data:
                writer.writerow([
                    case.get('id', ''),
                    case.get('title', ''),
                    case.get('case_number', ''),
                    case.get('status', ''),
                    case.get('priority', ''),
                    case.get('practice_area', ''),
                    case.get('client_id', ''),
                    case.get('assigned_lawyer_id', ''),
                    case.get('duration', 0),
                    case.get('total_documents', 0),
                    case.get('estimated_value', 0),
                    case.get('actual_value', 0)
                ])
            
            response = make_response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = 'attachment; filename=cases_export.csv'
            return response
            
        elif export_type == 'financial':
            financials = analytics_engine.get_financial_analytics(start_date, end_date)
            
            # Create CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Metric', 'Value'])
            
            # Write data
            for key, value in financials.items():
                if isinstance(value, (int, float)):
                    writer.writerow([key, value])
                else:
                    writer.writerow([key, str(value)])
            
            response = make_response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = 'attachment; filename=financial_export.csv'
            return response
            
        else:
            flash('Invalid export type', 'danger')
            return redirect(url_for('analytics.reports'))
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        flash('Error exporting data', 'danger')
        return redirect(url_for('analytics.reports'))

# Error handlers
@analytics_bp.errorhandler(404)
def analytics_not_found(error):
    """Handle 404 errors"""
    return render_template('analytics/error.html',
                         error_code=404,
                         error_message='Page not found'), 404

@analytics_bp.errorhandler(500)
def analytics_server_error(error):
    """Handle 500 errors"""
    logger.error(f"Analytics server error: {error}")
    return render_template('analytics/error.html',
                         error_code=500,
                         error_message='Internal server error'), 500

# API documentation
@analytics_bp.route('/api/docs')
@analytics_login_required
def analytics_api_docs():
    """API documentation"""
    try:
        return render_template('analytics/api_docs.html')
        
    except Exception as e:
        logger.error(f"Error loading API docs: {str(e)}")
        return render_template('analytics/error.html', error=str(e))

# Health check
@analytics_bp.route('/health')
def analytics_health():
    """Health check endpoint"""
    try:
        # Check if analytics engine is working
        overview = analytics_engine.get_firm_overview()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'analytics_engine': 'operational'
        })
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500
