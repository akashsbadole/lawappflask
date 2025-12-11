"""
Enhanced Document Management Routes
Integrates OCR, AI analysis, and advanced search functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app, session
from models import db, Document, DocumentAnalysis, Client, Case, User
from document_ocr import ocr_engine, document_analyzer, document_search, process_document_ocr
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import logging
from functools import wraps

# Create blueprint
documents_bp = Blueprint('documents', __name__)

# Configure logging
logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@documents_bp.route('/documents')
@login_required
def documents():
    """Enhanced documents list with search and filters"""
    user = User.query.get(session['user_id'])
    
    # Get search parameters
    search_query = request.args.get('q', '')
    category_filter = request.args.get('category', '')
    client_filter = request.args.get('client_id', type=int)
    case_filter = request.args.get('case_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build filters
    filters = {}
    if category_filter:
        filters['category'] = category_filter
    if client_filter:
        filters['client_id'] = client_filter
    if case_filter:
        filters['case_id'] = case_filter
    if date_from:
        filters['date_from'] = datetime.strptime(date_from, '%Y-%m-%d')
    if date_to:
        filters['date_to'] = datetime.strptime(date_to, '%Y-%m-%d')
    
    # Search documents
    if search_query or filters:
        documents = document_search.search_documents(
            search_query, 
            user_id=user.id if user.role != 'admin' else None,
            filters=filters
        )
    else:
        # Get documents based on user role
        if user.role == 'admin':
            documents = Document.query.all()
        else:
            documents = Document.query.filter_by(uploaded_by=user.id).all()
    
    # Get filter options
    categories = ['contract', 'court_filing', 'correspondence', 'evidence', 'legal_brief', 'motion', 'pleading', 'research', 'other']
    clients = Client.query.all() if user.role == 'admin' else Client.query.filter_by(assigned_lawyer_id=user.id).all()
    cases = Case.query.all() if user.role == 'admin' else Case.query.filter_by(assigned_lawyer_id=user.id).all()
    
    return render_template('documents_enhanced.html',
                         documents=documents,
                         search_query=search_query,
                         categories=categories,
                         clients=clients,
                         cases=cases,
                         current_category=category_filter,
                         current_client=client_filter,
                         current_case=case_filter,
                         current_date_from=date_from,
                         current_date_to=date_to)

@documents_bp.route('/upload_document', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Enhanced document upload with automatic OCR processing"""
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file:
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            # Validate file
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            # Check file extension
            allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
            if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                flash('Invalid file type. Allowed types: PDF, DOC, DOCX, TXT, JPG, PNG, BMP, TIFF', 'danger')
                return redirect(request.url)
            
            # Secure filename
            filename = secure_filename(file.filename)
            
            # Create unique filename to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Save file
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Create document record
            document = Document(
                title=request.form.get('title', filename),
                description=request.form.get('description', ''),
                filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_type=file.content_type,
                category=request.form.get('category', 'other'),
                client_id=request.form.get('client_id', type=int) or None,
                case_id=request.form.get('case_id', type=int) or None,
                uploaded_by=session['user_id'],
                tags=request.form.get('tags', ''),
                is_confidential='is_confidential' in request.form,
                requires_signature='requires_signature' in request.form
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Process OCR in background (you might want to use Celery for this)
            try:
                process_document_ocr(document.id)
                flash('Document uploaded successfully! OCR processing started.', 'success')
            except Exception as e:
                logger.error(f"OCR processing failed for document {document.id}: {str(e)}")
                flash('Document uploaded successfully! OCR processing failed. You can process it manually.', 'warning')
            
            return redirect(url_for('documents.documents'))
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            flash('Error uploading document. Please try again.', 'danger')
            return redirect(request.url)
    
    # Get form data
    user = User.query.get(session['user_id'])
    clients = Client.query.all() if user.role == 'admin' else Client.query.filter_by(assigned_lawyer_id=user.id).all()
    cases = Case.query.all() if user.role == 'admin' else Case.query.filter_by(assigned_lawyer_id=user.id).all()
    
    categories = [
        ('contract', 'Contract'),
        ('court_filing', 'Court Filing'),
        ('correspondence', 'Correspondence'),
        ('evidence', 'Evidence'),
        ('legal_brief', 'Legal Brief'),
        ('motion', 'Motion'),
        ('pleading', 'Pleading'),
        ('research', 'Research'),
        ('other', 'Other')
    ]
    
    return render_template('upload_document_enhanced.html',
                         clients=clients,
                         cases=cases,
                         categories=categories)

@documents_bp.route('/view_document/<int:document_id>')
@login_required
def view_document(document_id):
    """Enhanced document view with OCR text and analysis"""
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to view this document.', 'danger')
        return redirect(url_for('documents.documents'))
    
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
                         analyses=analyses,
                         analysis_data=analysis_data)

@documents_bp.route('/process_ocr/<int:document_id>', methods=['POST'])
@login_required
def process_ocr(document_id):
    """Manually trigger OCR processing for a document"""
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if user.role != 'admin' and document.uploaded_by != user.id:
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    try:
        process_document_ocr(document_id)
        return jsonify({'success': True, 'message': 'OCR processing completed successfully'})
    except Exception as e:
        logger.error(f"Error processing OCR for document {document_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'OCR processing failed: {str(e)}'})

@documents_bp.route('/search_documents', methods=['POST'])
@login_required
def search_documents():
    """AJAX endpoint for document search"""
    user = User.query.get(session['user_id'])
    
    search_query = request.form.get('query', '')
    filters = {}
    
    # Parse filters
    if request.form.get('category'):
        filters['category'] = request.form.get('category')
    if request.form.get('client_id'):
        filters['client_id'] = int(request.form.get('client_id'))
    if request.form.get('case_id'):
        filters['case_id'] = int(request.form.get('case_id'))
    if request.form.get('date_from'):
        filters['date_from'] = datetime.strptime(request.form.get('date_from'), '%Y-%m-%d')
    if request.form.get('date_to'):
        filters['date_to'] = datetime.strptime(request.form.get('date_to'), '%Y-%m-%d')
    
    # Search documents
    documents = document_search.search_documents(
        search_query,
        user_id=user.id if user.role != 'admin' else None,
        filters=filters
    )
    
    # Render results
    return render_template('document_search_results.html', documents=documents)

@documents_bp.route('/document_analytics')
@login_required
def document_analytics():
    """Document analytics dashboard"""
    user = User.query.get(session['user_id'])
    
    # Get analytics based on user role
    if user.role == 'admin':
        documents = Document.query.all()
    else:
        documents = Document.query.filter_by(uploaded_by=user.id).all()
    
    # Calculate statistics
    total_documents = len(documents)
    total_size = sum(doc.file_size or 0 for doc in documents)
    
    # Documents by category
    category_stats = {}
    for doc in documents:
        category = doc.category or 'other'
        category_stats[category] = category_stats.get(category, 0) + 1
    
    # Documents by file type
    file_type_stats = {}
    for doc in documents:
        file_type = doc.file_type or 'unknown'
        file_type_stats[file_type] = file_type_stats.get(file_type, 0) + 1
    
    # Documents with OCR
    documents_with_ocr = len([doc for doc in documents if doc.ocr_text])
    ocr_percentage = (documents_with_ocr / total_documents * 100) if total_documents > 0 else 0
    
    # Documents with AI analysis
    documents_with_analysis = len([doc for doc in documents if doc.ai_summary])
    analysis_percentage = (documents_with_analysis / total_documents * 100) if total_documents > 0 else 0
    
    # Recent uploads
    recent_documents = sorted(documents, key=lambda x: x.created_at, reverse=True)[:10]
    
    return render_template('document_analytics.html',
                         total_documents=total_documents,
                         total_size=total_size,
                         category_stats=category_stats,
                         file_type_stats=file_type_stats,
                         ocr_percentage=ocr_percentage,
                         analysis_percentage=analysis_percentage,
                         recent_documents=recent_documents)

@documents_bp.route('/download_document/<int:document_id>')
@login_required
def download_document(document_id):
    """Download document with permission check"""
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to download this document.', 'danger')
        return redirect(url_for('documents.documents'))
    
    return send_file(document.file_path, as_attachment=True, download_name=document.filename)

@documents_bp.route('/delete_document/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    """Delete document with permission check"""
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to delete this document.', 'danger')
        return redirect(url_for('documents.documents'))
    
    try:
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete document analyses
        DocumentAnalysis.query.filter_by(document_id=document_id).delete()
        
        # Delete document
        db.session.delete(document)
        db.session.commit()
        
        flash('Document deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        flash('Error deleting document', 'danger')
    
    return redirect(url_for('documents.documents'))

@documents_bp.route('/batch_process_ocr', methods=['POST'])
@login_required
def batch_process_ocr():
    """Batch process OCR for multiple documents"""
    user = User.query.get(session['user_id'])
    
    if user.role != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    document_ids = request.form.getlist('document_ids')
    results = []
    
    for doc_id in document_ids:
        try:
            process_document_ocr(int(doc_id))
            results.append({'id': doc_id, 'success': True})
        except Exception as e:
            results.append({'id': doc_id, 'success': False, 'error': str(e)})
    
    return jsonify({'results': results})

@documents_bp.route('/document_similarity/<int:document_id>')
@login_required
def document_similarity(document_id):
    """Find similar documents based on content"""
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if user.role != 'admin' and document.uploaded_by != user.id:
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    if not document.ocr_text:
        return jsonify({'success': False, 'message': 'Document has no OCR text for comparison'})
    
    # Find similar documents (simple text similarity)
    similar_docs = []
    documents = Document.query.filter(Document.id != document_id).all()
    
    for doc in documents:
        if doc.ocr_text:
            # Simple similarity calculation based on common words
            doc1_words = set(document.ocr_text.lower().split())
            doc2_words = set(doc.ocr_text.lower().split())
            
            if doc1_words and doc2_words:
                intersection = doc1_words.intersection(doc2_words)
                union = doc1_words.union(doc2_words)
                similarity = len(intersection) / len(union)
                
                if similarity > 0.1:  # Threshold for similarity
                    similar_docs.append({
                        'id': doc.id,
                        'title': doc.title,
                        'similarity': similarity
                    })
    
    # Sort by similarity
    similar_docs.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({'success': True, 'similar_documents': similar_docs[:10]})
