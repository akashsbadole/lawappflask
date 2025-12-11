# LawEdge Enquiry Form & Chatbot Implementation Plan

## Overview

This plan outlines the implementation of a public enquiry form with email functionality and integration of a custom chatbot for the LawEdge law firm management system.

## Requirements Analysis

1. **Public Enquiry Form**: Accessible to all visitors without login
2. **Email Integration**: Send enquiries to designated email addresses
3. **Custom Chatbot**: AI-powered chatbot for visitor assistance
4. **Open Source Chatbot**: Research and integrate existing solutions

## Implementation Steps

### Phase 1: Enquiry Form Implementation

- [ ] Create Enquiry model in database
- [ ] Create enquiry form template
- [ ] Implement email sending functionality
- [ ] Add form validation and security
- [ ] Create enquiry management routes for admin
- [ ] Add enquiry to navigation and public pages

### Phase 2: Chatbot Research & Selection

- [ ] Research open source chatbot solutions
- [ ] Evaluate options based on:
  - Ease of integration
  - Customization capabilities
  - Legal industry suitability
  - Maintenance requirements
- [ ] Select best chatbot solution
- [ ] Plan integration approach

### Phase 3: Chatbot Implementation

- [ ] Install and configure selected chatbot
- [ ] Customize chatbot for legal services
- [ ] Integrate chatbot with website
- [ ] Add chatbot training data for legal Q&A
- [ ] Implement chatbot analytics

### Phase 4: Integration & Testing

- [ ] Integrate enquiry form with existing design
- [ ] Test email functionality
- [ ] Test chatbot responses
- [ ] Ensure mobile responsiveness
- [ ] Performance optimization

## Technical Specifications

### Enquiry Form Fields

- Name (Required)
- Email (Required)
- Phone Number
- Subject (Required)
- Message (Required)
- Practice Area Interest
- Urgency Level
- Preferred Contact Method

### Email Configuration

- Use Flask-Mail for email sending
- Configure SMTP settings
- Add email templates for notifications
- Implement email queue for reliability

### Chatbot Options to Research

1. **Botpress** - Open source conversational AI platform
2. **Rasa** - Open source machine learning framework for dialogue AI
3. **Microsoft Bot Framework** - Comprehensive bot development framework
4. **Dialogflow** - Google's natural language understanding platform (free tier available)
5. **Tidio** - User-friendly chatbot with free plan
6. **ChatBot** - AI-powered chatbot platform
7. **Crisp** - Customer service platform with chatbot capabilities

## Database Schema Updates

### Enquiry Model

```sql
CREATE TABLE enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    practice_area VARCHAR(100),
    urgency_level VARCHAR(20) DEFAULT 'medium',
    preferred_contact VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES users (id)
);
```

## File Structure

```
templates/
├── enquiry.html (new)
├── enquiry_success.html (new)
└── admin/
    └── enquiries.html (new)

static/
├── css/
│   └── enquiry.css (new)
└── js/
    └── chatbot.js (new)

routes/
├── enquiry_routes.py (new)
└── chatbot_routes.py (new)

models.py (update)
app.py (update)
```

## Security Considerations

- CSRF protection for forms
- Input validation and sanitization
- Rate limiting for form submissions
- Email injection prevention
- Chatbot input sanitization

## Timeline Estimate

- Phase 1: 2-3 days
- Phase 2: 1-2 days
- Phase 3: 3-4 days
- Phase 4: 1-2 days

**Total Estimated Time: 7-11 days**
