# Enhanced Law Firm Management System - Setup Guide

## Overview

This guide will help you set up the enhanced Law Firm Management System with advanced security, OCR, and AI features.

## 🚀 New Features Implemented

### Phase 1 Critical Features:

- ✅ **Enhanced Security & Authentication**

  - SMS OTP login with Twilio/MSG91 integration
  - Two-Factor Authentication (2FA) with TOTP
  - Account locking after failed attempts
  - Comprehensive security logging

- ✅ **Advanced Document Management with OCR**

  - Multi-language OCR (English, Hindi, Marathi, Tamil)
  - AI-powered document analysis and summarization
  - Legal entity extraction and keyword detection
  - Advanced search with relevance scoring

- ✅ **Attendance & Performance Tracking**
  - Geolocation-based check-in/check-out
  - Automated performance metrics calculation
  - Utilization rate analysis

## 📋 Prerequisites

### System Requirements

- Python 3.8+
- 4GB RAM minimum
- 2GB disk space

### Software Dependencies

- **Tesseract OCR** (for document text extraction)
- **Redis** (optional, for session storage and caching)
- **PostgreSQL/MySQL** (optional, for production)

### External Services (Optional)

- **Twilio** or **MSG91** (for SMS OTP)
- **Google Gemini** or **OpenAI** (for AI features)
- **Email Service** (SendGrid, AWS SES)

## 🛠️ Installation Steps

### 1. Install Python Dependencies

```bash
# Create virtual environment
python -m venv lawedge_env

# Activate virtual environment
# Windows:
lawedge_env\Scripts\activate
# Linux/Mac:
source lawedge_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

#### Windows:

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Set environment variable:
   ```
   set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

#### Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-hin tesseract-ocr-mar tesseract-ocr-tam
```

#### macOS:

```bash
brew install tesseract
brew install tesseract-lang
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite:///law_firm_enhanced.db

# SMS Service Configuration (Choose one)
# Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# MSG91 (Alternative to Twilio)
MSG91_AUTH_KEY=your_msg91_auth_key
MSG91_TEMPLATE_ID=your_msg91_template_id

# AI Service Configuration (Optional)
AI_SERVICE=mock  # Options: mock, openai, gemini
AI_API_KEY=your_ai_api_key

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract  # Linux/Mac
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows

# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 4. Database Setup

#### Option 1: SQLite (Default - Development)

```bash
# Database will be created automatically
python app_enhanced_integration.py
```

#### Option 2: PostgreSQL (Production)

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update .env file
DATABASE_URL=postgresql://username:password@localhost/lawedge_db

# Create database
createdb lawedge_db
```

#### Option 3: MySQL (Production)

```bash
# Install MySQL adapter
pip install mysql-connector-python

# Update .env file
DATABASE_URL=mysql://username:password@localhost/lawedge_db

# Create database
mysql -u root -p
CREATE DATABASE lawedge_db;
```

### 5. Run Database Migrations

```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Add enhanced security and OCR features"

# Apply migrations
flask db upgrade
```

### 6. Create Sample Data (Optional)

```bash
# Uncomment the create_sample_data() call in app_enhanced_integration.py
# Or run manually:
python -c "
from app_enhanced_integration import create_enhanced_app, create_sample_data
app = create_enhanced_app()
with app.app_context():
    create_sample_data()
"
```

## 🔧 Configuration

### SMS Service Setup

#### Twilio Setup:

1. Sign up at https://www.twilio.com
2. Get Account SID, Auth Token, and Phone Number
3. Add to environment variables
4. Verify phone number in Twilio console

#### MSG91 Setup:

1. Sign up at https://msg91.com
2. Get Auth Key and create Template
3. Add to environment variables

### AI Service Setup

#### Google Gemini (Recommended):

1. Get API key from https://makersuite.google.com
2. Set `AI_SERVICE=gemini` and `AI_API_KEY=your_key`
3. Enable Gemini API in Google Cloud Console

#### OpenAI:

1. Get API key from https://platform.openai.com
2. Set `AI_SERVICE=openai` and `AI_API_KEY=your_key`

## 🚀 Running the Application

### Development Mode:

```bash
python app_enhanced_integration.py
```

### Production Mode:

```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_enhanced_integration:create_enhanced_app()

# Using Waitress (Windows)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app_enhanced_integration:create_enhanced_app()
```

## 📱 Default Login Credentials

After setup, you can login with:

- **Admin**: username=`admin`, password=`admin123`
- **Lawyer**: username=`lawyer`, password=`lawyer123`

## 🔍 Testing the Features

### 1. Enhanced Security

- Try SMS login (requires SMS service setup)
- Setup 2FA in security settings
- Test account locking with failed attempts

### 2. Document OCR

- Upload a PDF or image document
- Check automatic OCR processing
- Test AI document analysis

### 3. Search and Analytics

- Use advanced search with filters
- Check document analytics dashboard
- Test document similarity detection

## 🔒 Security Configuration

### Production Security Settings:

```python
# In production config
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
```

### Recommended Security Practices:

1. Change default passwords immediately
2. Use environment variables for sensitive data
3. Enable HTTPS in production
4. Regularly update dependencies
5. Implement backup strategy

## 📊 Monitoring and Logging

### Enable Debug Logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Monitor:

- Failed login attempts
- OCR processing errors
- Document upload failures
- SMS OTP delivery status

## 🐛 Troubleshooting

### Common Issues:

#### 1. Tesseract Not Found

```
Error: TesseractNotFoundError
Solution: Install Tesseract OCR and set TESSERACT_PATH
```

#### 2. SMS OTP Not Working

```
Error: Failed to send SMS OTP
Solution: Check API keys and phone number verification
```

#### 3. OCR Processing Failed

```
Error: OCR processing failed
Solution: Check file format and Tesseract installation
```

#### 4. Database Migration Issues

```
Error: Table already exists
Solution: Drop and recreate database, or check migration state
```

## 📚 API Documentation

### Authentication Endpoints:

- `POST /auth/login` - Enhanced login with SMS/2FA
- `POST /auth/verify_sms_otp` - Verify SMS OTP
- `POST /auth/verify_2fa` - Verify 2FA token
- `POST /auth/setup_2fa` - Setup 2FA

### Document Endpoints:

- `GET /documents` - Enhanced document list with search
- `POST /documents/upload_document` - Upload with OCR processing
- `GET /documents/view_document/<id>` - View with analysis
- `POST /documents/process_ocr/<id>` - Manual OCR processing
- `GET /documents/document_analytics` - Document analytics

## 🔄 Updating the System

### Update Dependencies:

```bash
pip install --upgrade -r requirements.txt
```

### Database Migrations:

```bash
flask db migrate -m "Update description"
flask db upgrade
```

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error details
3. Check environment variable configuration
4. Verify external service API keys

## 🗺️ Roadmap

### Next Phase Features:

- Real Integrations (Email, Calendar, Payment Gateways)
- Enhanced Client Portal with 2FA
- Advanced Analytics & Reporting
- Mobile Application Development

---

**Note**: This enhanced system is designed to be modular and can be easily integrated with your existing codebase. All new features are backward compatible and can be enabled/disabled through configuration.
