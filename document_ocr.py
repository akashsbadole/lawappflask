"""
Document OCR Module
Implements OCR-based document text extraction and AI document analysis
"""

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    import io
    import cv2
    import numpy as np
except ImportError:
    pytesseract = None
    Image = None
    pdf2image = None
    cv2 = None
    np = None

import os
import json
import re
from datetime import datetime
from flask import current_app
from models import db, Document, DocumentAnalysis

class OCREngine:
    """OCR Engine for extracting text from documents"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        # Configure Tesseract path if provided
        self.tesseract_path = app.config.get('TESSERACT_PATH')
        if self.tesseract_path and pytesseract:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Supported file formats
        self.supported_formats = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']
        
        # OCR languages
        self.languages = app.config.get('OCR_LANGUAGES', 'eng')
    
    def extract_text_from_file(self, file_path, file_type=None):
        """Extract text from a file using OCR"""
        if not pytesseract or not Image:
            current_app.logger.error("OCR libraries not available")
            return None, "OCR libraries not available"
        
        try:
            # Determine file type if not provided
            if not file_type:
                file_type = os.path.splitext(file_path)[1].lower().lstrip('.')
            
            if file_type not in self.supported_formats:
                return None, f"Unsupported file format: {file_type}"
            
            # Process based on file type
            if file_type == 'pdf':
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)
        
        except Exception as e:
            current_app.logger.error(f"OCR extraction error: {str(e)}")
            return None, f"OCR extraction failed: {str(e)}"
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file"""
        if not pdf2image:
            return None, "pdf2image library not available"
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(file_path)
            all_text = []
            
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Extract text
                text = pytesseract.image_to_string(
                    processed_image,
                    lang=self.languages,
                    config='--psm 6'  # Assume uniform block of text
                )
                
                if text.strip():
                    all_text.append(f"--- Page {i+1} ---\n{text}")
            
            full_text = '\n\n'.join(all_text)
            return full_text, None
        
        except Exception as e:
            return None, f"PDF processing failed: {str(e)}"
    
    def _extract_from_image(self, file_path):
        """Extract text from image file"""
        try:
            # Open image
            image = Image.open(file_path)
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.languages,
                config='--psm 6'
            )
            
            return text, None
        
        except Exception as e:
            return None, f"Image processing failed: {str(e)}"
    
    def _preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        if not cv2 or not np:
            return image
        
        try:
            # Convert PIL to OpenCV format
            cv_image = np.array(image)
            
            # Convert to grayscale
            if len(cv_image.shape) == 3:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
            
            # Apply threshold to get binary image
            _, cv_image = cv2.threshold(cv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Noise removal
            cv_image = cv2.medianBlur(cv_image, 3)
            
            # Convert back to PIL
            return Image.fromarray(cv_image)
        
        except Exception as e:
            current_app.logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def is_supported_format(self, file_path):
        """Check if file format is supported for OCR"""
        file_type = os.path.splitext(file_path)[1].lower().lstrip('.')
        return file_type in self.supported_formats

class DocumentAnalyzer:
    """AI-powered document analysis"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        # AI service configuration
        self.ai_service = app.config.get('AI_SERVICE', 'local')
        self.ai_api_key = app.config.get('AI_API_KEY')
        self.ai_model = app.config.get('AI_MODEL', 'gpt-3.5-turbo')
    
    def analyze_document(self, document_id, text=None):
        """Analyze document content and extract insights"""
        document = Document.query.get(document_id)
        if not document:
            return False, "Document not found"
        
        # Get text if not provided
        if not text:
            text = document.ocr_text
            if not text:
                return False, "No text available for analysis"
        
        try:
            # Perform different types of analysis
            analyses = {}
            
            # Extract keywords
            analyses['keywords'] = self._extract_keywords(text)
            
            # Detect document type
            analyses['document_type'] = self._detect_document_type(text)
            
            # Extract entities
            analyses['entities'] = self._extract_entities(text)
            
            # Generate summary
            analyses['summary'] = self._generate_summary(text)
            
            # Extract dates
            analyses['dates'] = self._extract_dates(text)
            
            # Extract amounts/money
            analyses['amounts'] = self._extract_amounts(text)
            
            # Legal-specific analysis
            if document.category in ['contract', 'court_filing', 'legal_brief', 'motion', 'pleading']:
                analyses['legal_analysis'] = self._legal_document_analysis(text)
            
            # Save analyses to database
            for analysis_type, result in analyses.items():
                if result:
                    analysis = DocumentAnalysis(
                        document_id=document_id,
                        analysis_type=analysis_type,
                        analysis_result=json.dumps(result) if isinstance(result, dict) else result,
                        confidence_score=0.85  # Placeholder confidence score
                    )
                    db.session.add(analysis)
            
            db.session.commit()
            return True, "Document analysis completed"
        
        except Exception as e:
            current_app.logger.error(f"Document analysis error: {str(e)}")
            return False, f"Analysis failed: {str(e)}"
    
    def _extract_keywords(self, text):
        """Extract keywords from text"""
        # Simple keyword extraction using frequency and legal terms
        legal_terms = [
            'agreement', 'contract', 'party', 'clause', 'liability', 'indemnity',
            'jurisdiction', 'governing law', 'termination', 'breach', 'damages',
            'court', 'judge', 'plaintiff', 'defendant', 'evidence', 'testimony',
            'attorney', 'counsel', 'legal', 'law', 'statute', 'regulation'
        ]
        
        # Count word frequency
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word in legal_terms or len(word) > 6:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:20]]
    
    def _detect_document_type(self, text):
        """Detect document type based on content"""
        # Simple pattern matching for document types
        patterns = {
            'contract': [
                r'agreement', r'contract', r'terms and conditions', r'party',
                r'signature', r'date of execution', r'consideration'
            ],
            'court_filing': [
                r'court', r'case number', r'plaintiff', r'defendant',
                r'filed', r'judgment', r'decree'
            ],
            'invoice': [
                r'invoice', r'bill to', r'amount due', r'payment terms',
                r'tax', r'due date'
            ],
            'legal_notice': [
                r'legal notice', r'demand', r'notice period', r'breach',
                r'cure period', r'legal action'
            ],
            'power_of_attorney': [
                r'power of attorney', r'attorney-in-fact', r'authorize',
                r'special power', r'general power'
            ]
        }
        
        text_lower = text.lower()
        scores = {}
        
        for doc_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                if re.search(pattern, text_lower):
                    score += 1
            scores[doc_type] = score
        
        # Return document type with highest score
        if scores:
            detected_type = max(scores, key=scores.get)
            if scores[detected_type] > 0:
                return detected_type
        
        return 'unknown'
    
    def _extract_entities(self, text):
        """Extract named entities from text"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'amounts': []
        }
        
        # Extract person names (simple pattern)
        person_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        potential_names = re.findall(person_pattern, text)
        entities['persons'] = list(set(potential_names))[:10]  # Limit to 10
        
        # Extract organizations (simple pattern)
        org_pattern = r'\b([A-Z][a-zA-Z&\s]+(?:Inc|Ltd|LLC|Corp|Corporation|Company|LLP|Pvt\.? Ltd\.?)\b'
        potential_orgs = re.findall(org_pattern, text)
        entities['organizations'] = list(set(potential_orgs))[:10]
        
        # Extract dates
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        entities['dates'] = list(set(re.findall(date_pattern, text)))[:10]
        
        # Extract monetary amounts
        amount_pattern = r'\b(?:₹|Rs\.?|\$|USD|EUR|GBP)?\s*[\d,]+(?:\.\d{2})?\b'
        entities['amounts'] = list(set(re.findall(amount_pattern, text)))[:10]
        
        return entities
    
    def _generate_summary(self, text):
        """Generate a summary of the document"""
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 3:
            return text[:500] + '...' if len(text) > 500 else text
        
        # Score sentences based on position and length
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Prefer sentences at the beginning
            if i < len(sentences) * 0.3:
                score += 2
            elif i < len(sentences) * 0.6:
                score += 1
            
            # Prefer sentences with legal terms
            legal_terms = ['agreement', 'contract', 'party', 'court', 'law', 'legal']
            for term in legal_terms:
                if term.lower() in sentence.lower():
                    score += 1
            
            # Prefer sentences with moderate length
            if 50 <= len(sentence) <= 200:
                score += 1
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        summary_sentences = [s[0] for s in scored_sentences[:3]]
        
        return '. '.join(summary_sentences) + '.'
    
    def _extract_dates(self, text):
        """Extract and normalize dates from text"""
        date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
            r'\b(\d{1,2})(?:st|nd|rd|th)\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates[:10]  # Limit to 10 dates
    
    def _extract_amounts(self, text):
        """Extract monetary amounts from text"""
        # Indian currency patterns
        inr_patterns = [
            r'₹\s*[\d,]+(?:\.\d{2})?',
            r'Rs\.?\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:rupees|Rs\.?|INR)'
        ]
        
        # International currency patterns
        other_patterns = [
            r'\$\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|dollars)',
            r'EUR\s*[\d,]+(?:\.\d{2})?',
            r'£\s*[\d,]+(?:\.\d{2})?'
        ]
        
        amounts = []
        all_patterns = inr_patterns + other_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))[:10]  # Limit to 10 unique amounts
    
    def _legal_document_analysis(self, text):
        """Perform legal-specific document analysis"""
        analysis = {
            'clauses_identified': [],
            'risk_indicators': [],
            'key_terms': [],
            'jurisdiction': None,
            'governing_law': None,
            'parties': []
        }
        
        # Identify common legal clauses
        clause_patterns = {
            'indemnity': r'indemnif[y|i](?:es|ication)?',
            'liability': r'liabilit[y|ies]',
            'termination': r'terminat(?:e|ion)(?:\s+clause)?',
            'confidentiality': r'confidential(?:ity|ity\s+agreement)',
            'force_majeure': r'force\s+majeure',
            'dispute_resolution': r'dispute\s+resolution',
            'governing_law': r'governing\s+law',
            'jurisdiction': r'jurisdicition',
            'assignment': r'assign(?:ment|able)?',
            'amendment': r'amend(?:ment|s)?'
        }
        
        for clause, pattern in clause_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                analysis['clauses_identified'].append(clause)
        
        # Identify risk indicators
        risk_patterns = [
            (r'as\s+is', "No warranty provided"),
            (r'limit(?:s)?\s+liabilit[y|ies]', "Liability limitations"),
            (r'no\s+warrant[y|ies]', "No warranties"),
            (r'penalt(?:y|ies)', "Penalty clauses"),
            (r'liquidated\s+damages', "Liquidated damages")
        ]
        
        for pattern, description in risk_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                analysis['risk_indicators'].append(description)
        
        # Extract jurisdiction and governing law
        jurisdiction_match = re.search(r'jurisdic[t|i]ion[^.]*', text, re.IGNORECASE)
        if jurisdiction_match:
            analysis['jurisdiction'] = jurisdiction_match.group(0).strip()
        
        law_match = re.search(r'governing\s+law[^.]*', text, re.IGNORECASE)
        if law_match:
            analysis['governing_law'] = law_match.group(0).strip()
        
        return analysis

class DocumentSearcher:
    """Advanced document search functionality"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
    
    def search_documents(self, query, user_id=None, case_id=None, client_id=None):
        """Search documents with advanced filtering"""
        # Build base query
        documents = Document.query
        
        # Apply filters
        if user_id:
            documents = documents.filter(Document.uploaded_by == user_id)
        
        if case_id:
            documents = documents.filter(Document.case_id == case_id)
        
        if client_id:
            documents = documents.filter(Document.client_id == client_id)
        
        # Get all documents that match filters
        documents = documents.all()
        
        # Search in OCR text and metadata
        results = []
        query_lower = query.lower()
        
        for doc in documents:
            score = 0
            match_context = []
            
            # Search in title
            if doc.title and query_lower in doc.title.lower():
                score += 10
                match_context.append(f"Title: {doc.title}")
            
            # Search in description
            if doc.description and query_lower in doc.description.lower():
                score += 5
                match_context.append(f"Description: {doc.description[:100]}...")
            
            # Search in OCR text
            if doc.ocr_text and query_lower in doc.ocr_text.lower():
                score += 3
                # Find context around match
                text_lower = doc.ocr_text.lower()
                start_idx = text_lower.find(query_lower)
                if start_idx != -1:
                    context_start = max(0, start_idx - 50)
                    context_end = min(len(doc.ocr_text), start_idx + len(query) + 50)
                    context = doc.ocr_text[context_start:context_end].replace('\n', ' ')
                    match_context.append(f"Content: ...{context}...")
            
            # Search in tags
            if doc.tags and query_lower in doc.tags.lower():
                score += 2
                match_context.append(f"Tags: {doc.tags}")
            
            # Add to results if matched
            if score > 0:
                results.append({
                    'document': doc,
                    'score': score,
                    'context': match_context
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results

# Initialize OCR engine components
ocr_engine = OCREngine()
document_analyzer = DocumentAnalyzer()
document_searcher = DocumentSearcher()

def process_document_ocr(document_id):
    """Process OCR for a document (background task)"""
    document = Document.query.get(document_id)
    if not document:
        return False, "Document not found"
    
    try:
        # Check if file exists
        if not os.path.exists(document.file_path):
            return False, "File not found"
        
        # Extract text using OCR
        text, error = ocr_engine.extract_text_from_file(document.file_path)
        
        if error:
            return False, error
        
        # Update document with OCR text
        document.ocr_text = text
        db.session.commit()
        
        # Analyze document
        analysis_success, analysis_message = document_analyzer.analyze_document(document_id, text)
        
        return True, "OCR processing completed"
    
    except Exception as e:
        current_app.logger.error(f"OCR processing error for document {document_id}: {str(e)}")
        return False, f"OCR processing failed: {str(e)}"