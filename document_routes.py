"""
Enhanced Document Management Routes
Implements routes for OCR, document analysis, and advanced document features
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from models import db, User, Document, DocumentAnalysis
from document_ocr import ocr_engine, document_analyzer, document_searcher, process_document_ocr
from werkzeug.utils import secure_filename
import os
import json
from functools import wraps
from datetime import datetime

# Create blueprint
documents_bp = Blueprint('documents', __name__, url_prefix='/documents_enhanced')

# Helper decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Document OCR Routes
@documents_bp.route('/process-ocr/<int:document_id>', methods=['POST'])
@login_required
def process_ocr(document_id):
    """Process OCR for a document"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission
    user = User.query.get(session['user_id'])
    if user.role != 'admin' and document.uploaded_by != user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        # Process OCR in background
        success, message = process_document_ocr(document_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        current_app.logger.error(f"Error processing OCR for document {document_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'OCR processing failed: {str(e)}'}), 500

@documents_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_documents():
    """Advanced document search"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        case_id = request.form.get('case_id', type=int)
        client_id = request.form.get('client_id', type=int)
        
        if not query:
            flash('Please enter a search query', 'warning')
            return redirect(url_for('documents.search_documents'))
        
        # Perform search
        if user.role == 'admin':
            results = document_searcher.search_documents(
                query=query,
                case_id=case_id,
                client_id=client_id
            )
        else:
            results = document_searcher.search_documents(
                query=query,
                user_id=user.id,
                case_id=case_id,
                client_id=client_id
            )
        
        return render_template('documents_enhanced/search_results.html',
                             query=query,
                             results=results,
                             case_id=case_id,
                             client_id=client_id)
    
    # GET request - show search form
    return render_template('documents_enhanced/search.html')

@documents_bp.route('/analyze/<int:document_id>', methods=['POST'])
@login_required
def analyze_document(document_id):
    """Analyze document content"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission
    user = User.query.get(session['user_id'])
    if user.role != 'admin' and document.uploaded_by != user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        # Analyze document
        success, message = document_analyzer.analyze_document(document_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        current_app.logger.error(f"Error analyzing document {document_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Analysis failed: {str(e)}'}), 500

@documents_bp.route('/view-analysis/<int:document_id>')
@login_required
def view_analysis(document_id):
    """View document analysis results"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission
    user = User.query.get(session['user_id'])
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to view this document.', 'danger')
        return redirect(url_for('documents'))
    
    # Get document analyses
    analyses = DocumentAnalysis.query.filter_by(document_id=document_id).all()
    analysis_data = {}
    
    for analysis in analyses:
        try:
            if analysis.analysis_type in ['keywords', 'entities', 'dates', 'amounts', 'legal_analysis']:
                analysis_data[analysis.analysis_type] = json.loads(analysis.analysis_result)
            else:
                analysis_data[analysis.analysis_type] = analysis.analysis_result
        except:
            analysis_data[analysis.analysis_type] = analysis.analysis_result
    
    return render_template('documents_enhanced/view_analysis.html',
                         document=document,
                         analyses=analyses,
                         analysis_data=analysis_data)

@documents_bp.route('/batch-process', methods=['GET', 'POST'])
@login_required
def batch_process():
    """Batch process multiple documents"""
    user = User.query.get(session['user_id'])
    
    if user.role != 'admin':
        flash('Only administrators can perform batch processing', 'danger')
        return redirect(url_for('documents'))
    
    if request.method == 'POST':
        document_ids = request.form.getlist('document_ids')
        process_type = request.form.get('process_type')  # 'ocr' or 'analysis'
        
        if not document_ids:
            flash('Please select at least one document', 'warning')
            return redirect(url_for('documents.batch_process'))
        
        processed = []
        failed = []
        
        for doc_id in document_ids:
            try:
                if process_type == 'ocr':
                    success, message = process_document_ocr(int(doc_id))
                else:  # analysis
                    success, message = document_analyzer.analyze_document(int(doc_id))
                
                if success:
                    processed.append(doc_id)
                else:
                    failed.append((doc_id, message))
            
            except Exception as e:
                failed.append((doc_id, str(e)))
        
        flash(f'Processed {len(processed)} documents successfully', 'success')
        if failed:
            flash(f'Failed to process {len(failed)} documents', 'warning')
        
        return redirect(url_for('documents'))
    
    # GET request - show batch processing form
    documents = Document.query.filter_by(ocr_text=None).all()
    return render_template('documents_enhanced/batch_process.html', documents=documents)

@documents_bp.route('/templates')
@login_required
def document_templates():
    """Manage document templates"""
    user = User.query.get(session['user_id'])
    
    # Get template documents
    templates = Document.query.filter_by(is_template=True).all()
    
    if user.role != 'admin':
        templates = [t for t in templates if t.uploaded_by == user.id]
    
    return render_template('documents_enhanced/templates.html', templates=templates)

@documents_bp.route('/create-template', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create a new document template"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        template_content = request.form.get('template_content')
        variables = request.form.get('variables')  # JSON string of template variables
        
        if not title or not template_content:
            flash('Title and template content are required', 'danger')
            return redirect(url_for('documents.create_template'))
        
        # Create template document
        template = Document(
            title=title,
            description=description,
            filename=f"{title.replace(' ', '_')}_template.txt",
            file_path="",  # Templates don't have actual files
            file_type="text/plain",
            category=category,
            uploaded_by=user.id,
            is_template=True,
            template_details=template_content,
            tags=variables
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('Template created successfully!', 'success')
        return redirect(url_for('documents.document_templates'))
    
    return render_template('documents_enhanced/create_template.html')

@documents_bp.route('/use-template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def use_template(template_id):
    """Use a template to create a new document"""
    template = Document.query.get_or_404(template_id)
    
    if not template.is_template:
        flash('Invalid template', 'danger')
        return redirect(url_for('documents.document_templates'))
    
    if request.method == 'POST':
        # Get template variables and values
        variables = json.loads(template.tags) if template.tags else {}
        document_content = template.template_details
        
        # Replace variables with values
        for var_name, var_value in variables.items():
            form_value = request.form.get(f'var_{var_name}', '')
            document_content = document_content.replace(f'{{{var_name}}}', form_value)
        
        # Create new document from template
        new_document = Document(
            title=request.form.get('title'),
            description=request.form.get('description'),
            filename=f"{request.form.get('title').replace(' ', '_')}.txt",
            file_path="",  # Will be generated
            file_type="text/plain",
            category=template.category,
            case_id=request.form.get('case_id', type=int),
            client_id=request.form.get('client_id', type=int),
            uploaded_by=session['user_id'],
            tags=request.form.get('tags')
        )
        
        db.session.add(new_document)
        db.session.commit()
        
        # Save the generated content to a file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_document.filename)
        with open(file_path, 'w') as f:
            f.write(document_content)
        
        new_document.file_path = file_path
        db.session.commit()
        
        flash('Document created from template successfully!', 'success')
        return redirect(url_for('documents.view_document', document_id=new_document.id))
    
    # Parse template variables
    variables = json.loads(template.tags) if template.tags else {}
    
    return render_template('documents_enhanced/use_template.html',
                         template=template,
                         variables=variables)

@documents_bp.route('/version-history/<int:document_id>')
@login_required
def version_history(document_id):
    """View document version history"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission
    user = User.query.get(session['user_id'])
    if user.role != 'admin' and document.uploaded_by != user.id:
        flash('You do not have permission to view this document.', 'danger')
        return redirect(url_for('documents'))
    
    # Get document versions
    from models import DocumentVersion
    versions = DocumentVersion.query.filter_by(document_id=document_id).order_by(DocumentVersion.version_number.desc()).all()
    
    return render_template('documents_enhanced/version_history.html',
                         document=document,
                         versions=versions)

@documents_bp.route('/retention-policies')
@login_required
def retention_policies():
    """Manage document retention policies"""
    user = User.query.get(session['user_id'])
    
    if user.role != 'admin':
        flash('Only administrators can manage retention policies', 'danger')
        return redirect(url_for('documents'))
    
    # Placeholder for retention policies
    policies = []
    
    return render_template('documents_enhanced/retention_policies.html', policies=policies)

# API Routes
@documents_bp.route('/api/extract-text', methods=['POST'])
@login_required
def api_extract_text():
    """API endpoint to extract text from uploaded file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        # Extract text
        text, error = ocr_engine.extract_text_from_file(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        return jsonify({'success': True, 'text': text})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@documents_bp.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API endpoint for document search"""
    data = request.get_json()
    query = data.get('query', '')
    case_id = data.get('case_id')
    client_id = data.get('client_id')
    
    if not query:
        return jsonify({'success': False, 'message': 'Query required'})
    
    user = User.query.get(session['user_id'])
    
    # Perform search
    if user.role == 'admin':
        results = document_searcher.search_documents(
            query=query,
            case_id=case_id,
            client_id=client_id
        )
    else:
        results = document_searcher.search_documents(
            query=query,
            user_id=user.id,
            case_id=case_id,
            client_id=client_id
        )
    
    # Format results for API
    formatted_results = []
    for result in results:
        doc = result['document']
        formatted_results.append({
            'id': doc.id,
            'title': doc.title,
            'description': doc.description,
            'category': doc.category,
            'score': result['score'],
            'context': result['context']
        })
    
    return jsonify({'success': True, 'results': formatted_results})