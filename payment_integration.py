"""
Payment Gateway Integration Module
Implements payment processing with multiple payment gateways (Razorpay, Stripe, PayPal, etc.)
"""

import os
import json
import logging
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from flask import current_app

# Try to import payment gateway libraries
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

try:
    import paypalrestsdk
    PAYPAL_AVAILABLE = True
except ImportError:
    PAYPAL_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class PaymentGateway:
    """Payment gateway integration with multiple providers"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        # Razorpay Configuration
        self.razorpay_key_id = app.config.get('RAZORPAY_KEY_ID')
        self.razorpay_key_secret = app.config.get('RAZORPAY_KEY_SECRET')
        self.razorpay_webhook_secret = app.config.get('RAZORPAY_WEBHOOK_SECRET')
        
        # Stripe Configuration
        self.stripe_publishable_key = app.config.get('STRIPE_PUBLISHABLE_KEY')
        self.stripe_secret_key = app.config.get('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')
        
        # PayPal Configuration
        self.paypal_client_id = app.config.get('PAYPAL_CLIENT_ID')
        self.paypal_client_secret = app.config.get('PAYPAL_CLIENT_SECRET')
        self.paypal_sandbox = app.config.get('PAYPAL_SANDBOX', True)
        
        # Payment Settings
        self.default_currency = app.config.get('DEFAULT_CURRENCY', 'INR')
        self.payment_timeout = app.config.get('PAYMENT_TIMEOUT', 15)  # minutes
        self.success_url = app.config.get('PAYMENT_SUCCESS_URL')
        self.failure_url = app.config.get('PAYMENT_FAILURE_URL')
    
    def create_razorpay_order(self, amount, currency=None, receipt=None, notes=None, customer_info=None):
        """Create Razorpay order"""
        if not RAZORPAY_AVAILABLE:
            return False, "Razorpay library not available"
        
        try:
            if not self.razorpay_key_id or not self.razorpay_key_secret:
                return False, "Razorpay credentials not configured"
            
            client = razorpay.Client(auth=(self.razorpay_key_id, self.razorpay_key_secret))
            
            # Prepare order data
            order_data = {
                'amount': int(amount * 100),  # Razorpay expects amount in paise
                'currency': currency or self.default_currency,
                'receipt': receipt,
                'notes': notes or {},
                'payment': {
                    'capture': 'automatic',
                    'timeout': self.payment_timeout * 60  # Convert to seconds
                }
            }
            
            # Add customer info if provided
            if customer_info:
                order_data['customer'] = customer_info
            
            # Create order
            order = client.order.create(data=order_data)
            
            logger.info(f"Razorpay order created: {order['id']}")
            return True, order
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            return False, f"Error creating Razorpay order: {str(e)}"
    
    def capture_razorpay_payment(self, payment_id, amount):
        """Capture Razorpay payment"""
        if not RAZORPAY_AVAILABLE:
            return False, "Razorpay library not available"
        
        try:
            if not self.razorpay_key_id or not self.razorpay_key_secret:
                return False, "Razorpay credentials not configured"
            
            client = razorpay.Client(auth=(self.razorpay_key_id, self.razorpay_key_secret))
            
            # Capture payment
            payment = client.payment.capture(
                payment_id,
                int(amount * 100)  # Razorpay expects amount in paise
            )
            
            if payment['status'] == 'captured':
                logger.info(f"Razorpay payment captured: {payment_id}")
                return True, payment
            else:
                logger.error(f"Razorpay payment capture failed: {payment}")
                return False, payment
                
        except Exception as e:
            logger.error(f"Error capturing Razorpay payment: {str(e)}")
            return False, f"Error capturing Razorpay payment: {str(e)}"
    
    def create_stripe_payment_intent(self, amount, currency=None, metadata=None, customer_email=None):
        """Create Stripe payment intent"""
        if not STRIPE_AVAILABLE:
            return False, "Stripe library not available"
        
        try:
            if not self.stripe_publishable_key:
                return False, "Stripe publishable key not configured"
            
            stripe.api_key = self.stripe_publishable_key
            
            # Create payment intent
            intent_data = {
                'amount': int(amount * 100),  # Stripe expects amount in cents
                'currency': currency or self.default_currency,
                'payment_method_types': ['card'],
                'capture_method': 'automatic',
                'confirmation_method': 'manual'
            }
            
            if metadata:
                intent_data['metadata'] = metadata
            
            if customer_email:
                intent_data['receipt_email'] = customer_email
            
            intent = stripe.PaymentIntent.create(**intent_data)
            
            logger.info(f"Stripe payment intent created: {intent.id}")
            return True, intent
            
        except Exception as e:
            logger.error(f"Error creating Stripe payment intent: {str(e)}")
            return False, f"Error creating Stripe payment intent: {str(e)}"
    
    def confirm_stripe_payment(self, payment_intent_id):
        """Confirm Stripe payment"""
        if not STRIPE_AVAILABLE:
            return False, "Stripe library not available"
        
        try:
            if not self.stripe_publishable_key:
                return False, "Stripe publishable key not configured"
            
            stripe.api_key = self.stripe_publishable_key
            
            # Confirm payment intent
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id
            )
            
            if intent.status == 'succeeded':
                logger.info(f"Stripe payment confirmed: {payment_intent_id}")
                return True, intent
            else:
                logger.error(f"Stripe payment confirmation failed: {intent}")
                return False, intent
                
        except Exception as e:
            logger.error(f"Error confirming Stripe payment: {str(e)}")
            return False, f"Error confirming Stripe payment: {str(e)}"
    
    def create_paypal_payment(self, amount, currency=None, description=None, return_url=None, cancel_url=None):
        """Create PayPal payment"""
        if not PAYPAL_AVAILABLE:
            return False, "PayPal library not available"
        
        try:
            if not self.paypal_client_id or not self.paypal_client_secret:
                return False, "PayPal credentials not configured"
            
            # Configure PayPal SDK
            if self.paypal_sandbox:
                paypalrestsdk.configure(
                    mode="sandbox",
                    client_id=self.paypal_client_id,
                    client_secret=self.paypal_client_secret
                )
            else:
                paypalrestsdk.configure(
                    mode="live",
                    client_id=self.paypal_client_id,
                    client_secret=self.paypal_client_secret
                )
            
            # Create payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency or self.default_currency
                    },
                    "description": description
                }],
                "redirect_urls": {
                    "return_url": return_url or self.success_url,
                    "cancel_url": cancel_url or self.failure_url
                }
            })
            
            # Create payment
            payment.create()
            
            logger.info(f"PayPal payment created: {payment.id}")
            return True, payment
            
        except Exception as e:
            logger.error(f"Error creating PayPal payment: {str(e)}")
            return False, f"Error creating PayPal payment: {str(e)}"
    
    def execute_paypal_payment(self, payment_id, payer_id):
        """Execute PayPal payment"""
        if not PAYPAL_AVAILABLE:
            return False, "PayPal library not available"
        
        try:
            # Get payment details
            payment = paypalrestsdk.Payment.find(payment_id)
            
            # Execute payment
            payment.execute({
                "payer_id": payer_id
            })
            
            if payment.state == 'approved':
                logger.info(f"PayPal payment executed: {payment_id}")
                return True, payment
            else:
                logger.error(f"PayPal payment execution failed: {payment}")
                return False, payment
                
        except Exception as e:
            logger.error(f"Error executing PayPal payment: {str(e)}")
            return False, f"Error executing PayPal payment: {str(e)}"
    
    def process_invoice_payment(self, invoice, payment_method='razorpay', customer_info=None):
        """Process invoice payment"""
        try:
            # Choose payment method
            if payment_method == 'razorpay':
                return self._process_razorpay_invoice_payment(invoice, customer_info)
            elif payment_method == 'stripe':
                return self._process_stripe_invoice_payment(invoice, customer_info)
            elif payment_method == 'paypal':
                return self._process_paypal_invoice_payment(invoice, customer_info)
            else:
                return self._process_razorpay_invoice_payment(invoice, customer_info)
                
        except Exception as e:
            logger.error(f"Error processing invoice payment: {str(e)}")
            return False, f"Error processing invoice payment: {str(e)}"
    
    def _process_razorpay_invoice_payment(self, invoice, customer_info=None):
        """Process invoice payment with Razorpay"""
        # Create Razorpay order
        result = self.create_razorpay_order(
            amount=invoice.total,
            currency=invoice.currency,
            receipt=f"INV-{invoice.invoice_number}",
            notes={
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'client_id': invoice.client_id
            },
            customer_info=customer_info
        )
        
        if result[0]:
            order = result[1]
            # Save payment record
            from models import db, Payment
            
            payment = Payment(
                invoice_id=invoice.id,
                amount=invoice.total,
                payment_method='razorpay',
                transaction_id=order['id'],
                status='created',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
            db.session.commit()
            
            return True, {
                'payment_id': payment.id,
                'order_id': order['id'],
                'amount': invoice.total,
                'currency': invoice.currency
            }
        
        return result
    
    def _process_stripe_invoice_payment(self, invoice, customer_info=None):
        """Process invoice payment with Stripe"""
        # Create Stripe payment intent
        result = self.create_stripe_payment_intent(
            amount=invoice.total,
            currency=invoice.currency,
            metadata={
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'client_id': invoice.client_id
            },
            customer_email=customer_info.get('email') if customer_info else None
        )
        
        if result[0]:
            intent = result[1]
            # Save payment record
            from models import db, Payment
            
            payment = Payment(
                invoice_id=invoice.id,
                amount=invoice.total,
                payment_method='stripe',
                transaction_id=intent.id,
                status='created',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
            db.session.commit()
            
            return True, {
                'payment_id': payment.id,
                'client_secret': intent.client_secret,
                'amount': invoice.total,
                'currency': invoice.currency
            }
        
        return result
    
    def _process_paypal_invoice_payment(self, invoice, customer_info=None):
        """Process invoice payment with PayPal"""
        # Create PayPal payment
        result = self.create_paypal_payment(
            amount=invoice.total,
            currency=invoice.currency,
            description=f"Invoice {invoice.invoice_number}",
            return_url=f"{self.success_url}?invoice_id={invoice.id}",
            cancel_url=f"{self.failure_url}?invoice_id={invoice.id}"
        )
        
        if result[0]:
            payment = result[1]
            # Save payment record
            from models import db, Payment
            
            payment_record = Payment(
                invoice_id=invoice.id,
                amount=invoice.total,
                payment_method='paypal',
                transaction_id=payment.id,
                status='created',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment_record)
            db.session.commit()
            
            return True, {
                'payment_id': payment_record.id,
                'approval_url': payment.links[1].href if payment.links else None,
                'amount': invoice.total,
                'currency': invoice.currency
            }
        
        return result
    
    def verify_webhook_signature(self, payload, signature, provider):
        """Verify webhook signature"""
        try:
            if provider == 'razorpay':
                return self._verify_razorpay_webhook_signature(payload, signature)
            elif provider == 'stripe':
                return self._verify_stripe_webhook_signature(payload, signature)
            elif provider == 'paypal':
                return self._verify_paypal_webhook_signature(payload, signature)
            else:
                return False, "Unsupported provider"
                
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False, f"Error verifying webhook signature: {str(e)}"
    
    def _verify_razorpay_webhook_signature(self, payload, signature):
        """Verify Razorpay webhook signature"""
        if not self.razorpay_webhook_secret:
            logger.warning("Razorpay webhook secret not configured")
            return True  # Allow if secret not configured
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.razorpay_webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if hmac.compare_digest(expected_signature, signature):
                return True
            else:
                logger.warning("Razorpay webhook signature verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying Razorpay webhook signature: {str(e)}")
            return False
    
    def _verify_stripe_webhook_signature(self, payload, signature):
        """Verify Stripe webhook signature"""
        if not self.stripe_webhook_secret:
            logger.warning("Stripe webhook secret not configured")
            return True  # Allow if secret not configured
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.stripe_webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if hmac.compare_digest(expected_signature, signature):
                return True
            else:
                logger.warning("Stripe webhook signature verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying Stripe webhook signature: {str(e)}")
            return False
    
    def _verify_paypal_webhook_signature(self, payload, signature):
        """Verify PayPal webhook signature"""
        if not self.paypal_client_secret:
            logger.warning("PayPal client secret not configured")
            return True  # Allow if secret not configured
        
        try:
            # PayPal uses different signature format
            # This is a simplified verification
            actual = hmac.new(
                self.paypal_client_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(actual, signature):
                return True
            else:
                logger.warning("PayPal webhook signature verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying PayPal webhook signature: {str(e)}")
            return False
    
    def process_payment_webhook(self, payload, provider):
        """Process payment webhook"""
        try:
            if provider == 'razorpay':
                return self._process_razorpay_webhook(payload)
            elif provider == 'stripe':
                return self._process_stripe_webhook(payload)
            elif provider == 'paypal':
                return self._process_paypal_webhook(payload)
            else:
                return False, "Unsupported provider"
                
        except Exception as e:
            logger.error(f"Error processing payment webhook: {str(e)}")
            return False, f"Error processing payment webhook: {str(e)}"
    
    def _process_razorpay_webhook(self, payload):
        """Process Razorpay webhook"""
        try:
            event = payload.get('event')
            
            if event == 'payment.captured':
                payment_id = payload.get('payment', {}).get('id')
                order_id = payload.get('order', {}).get('id')
                amount = payload.get('payment', {}).get('amount') / 100  # Convert from paise to rupees
                currency = payload.get('payment', {}).get('currency')
                
                # Update payment record
                from models import db, Payment
                
                payment = Payment.query.filter_by(transaction_id=order_id).first()
                if payment:
                    payment.status = 'paid'
                    payment.paid_date = datetime.utcnow()
                    db.session.commit()
                    
                    # Update invoice status
                    invoice = payment.invoice
                    if invoice and invoice.status == 'sent':
                        invoice.status = 'paid'
                        invoice.paid_date = datetime.utcnow()
                        db.session.commit()
                
                logger.info(f"Razorpay payment captured: {payment_id}")
                return True, {
                    'event': 'payment.captured',
                    'payment_id': payment_id,
                    'amount': amount,
                    'currency': currency
                }
            
            elif event == 'payment.failed':
                payment_id = payload.get('payment', {}).get('id')
                order_id = payload.get('order', {}).get('id')
                
                # Update payment record
                payment = Payment.query.filter_by(transaction_id=order_id).first()
                if payment:
                    payment.status = 'failed'
                    db.session.commit()
                
                logger.error(f"Razorpay payment failed: {payment_id}")
                return True, {
                    'event': 'payment.failed',
                    'payment_id': payment_id
                }
            
        except Exception as e:
            logger.error(f"Error processing Razorpay webhook: {str(e)}")
            return False, f"Error processing Razorpay webhook: {str(e)}"
    
    def _process_stripe_webhook(self, payload):
        """Process Stripe webhook"""
        try:
            event_type = payload.get('type')
            
            if event_type == 'payment_intent.succeeded':
                payment_intent_id = payload.get('data', {}).get('object', {}).get('id')
                amount = payload.get('data', {}).get('object', {}).get('amount') / 100  # Convert from cents to rupees
                currency = payload.get('data', {}).get('object', {}).get('currency')
                
                # Update payment record
                from models import db, Payment
                
                payment = Payment.query.filter_by(transaction_id=payment_intent_id).first()
                if payment:
                    payment.status = 'paid'
                    payment.paid_date = datetime.utcnow()
                    db.session.commit()
                    
                    # Update invoice status
                    invoice = payment.invoice
                    if invoice and invoice.status == 'sent':
                        invoice.status = 'paid'
                        invoice.paid_date = datetime.utcnow()
                        db.session.commit()
                
                logger.info(f"Stripe payment succeeded: {payment_intent_id}")
                return True, {
                    'event': 'payment.succeeded',
                    'payment_intent_id': payment_intent_id,
                    'amount': amount,
                    'currency': currency
                }
            
            elif event_type == 'payment_intent.payment_failed':
                payment_intent_id = payload.get('data', {}).get('object', {}).get('id')
                
                # Update payment record
                payment = Payment.query.filter_by(transaction_id=payment_intent_id).first()
                if payment:
                    payment.status = 'failed'
                    db.session.commit()
                
                logger.error(f"Stripe payment failed: {payment_intent_id}")
                return True, {
                    'event': 'payment.failed',
                    'payment_intent_id': payment_intent_id
                }
            
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}")
            return False, f"Error processing Stripe webhook: {str(e)}"
    
    def _process_paypal_webhook(self, payload):
        """Process PayPal webhook"""
        try:
            event_type = payload.get('event_type')
            
            if event_type == 'PAYMENT.CAPTURE.COMPLETED':
                payment_id = payload.get('resource', {}).get('id')
                amount = float(payload.get('resource', {}).get('amount', {}).get('total'))
                currency = payload.get('resource', {}).get('amount', {}).get('currency')
                
                # Update payment record
                from models import db, Payment
                
                payment = Payment.query.filter_by(transaction_id=payment_id).first()
                if payment:
                    payment.status = 'paid'
                    payment.paid_date = datetime.utcnow()
                    db.session.commit()
                    
                    # Update invoice status
                    invoice = payment.invoice
                    if invoice and invoice.status == 'sent':
                        invoice.status = 'paid'
                        invoice.paid_date = datetime.utcnow()
                        db.session.commit()
                
                logger.info(f"PayPal payment completed: {payment_id}")
                return True, {
                    'event': 'payment.completed',
                    'payment_id': payment_id,
                    'amount': amount,
                    'currency': currency
                }
            
            elif event_type == 'PAYMENT.CAPTURE.DENIED':
                payment_id = payload.get('resource', {}).get('id')
                
                # Update payment record
                payment = Payment.query.filter_by(transaction_id=payment_id).first()
                if payment:
                    payment.status = 'failed'
                    db.session.commit()
                
                logger.error(f"PayPal payment denied: {payment_id}")
                return True, {
                    'event': 'payment.denied',
                    'payment_id': payment_id
                }
            
        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {str(e)}")
            return False, f"Error processing PayPal webhook: {str(e)}"
    
    def get_payment_status(self, payment_id, provider):
        """Get payment status"""
        try:
            if provider == 'razorpay':
                return self._get_razorpay_payment_status(payment_id)
            elif provider == 'stripe':
                return self._get_stripe_payment_status(payment_id)
            elif provider == 'paypal':
                return self._get_paypal_payment_status(payment_id)
            else:
                return False, "Unsupported provider"
                
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            return False, f"Error getting payment status: {str(e)}"
    
    def _get_razorpay_payment_status(self, payment_id):
        """Get Razorpay payment status"""
        if not RAZORPAY_AVAILABLE:
            return False, "Razorpay library not available"
        
        try:
            if not self.razorpay_key_id or not self.razorpay_key_secret:
                return False, "Razorpay credentials not configured"
            
            client = razorpay.Client(auth=(self.razorpay_key_id, self.razorpay_key_secret))
            
            # Get payment details
            payment = client.payment.fetch(payment_id)
            
            return True, {
                'status': payment.get('status'),
                'amount': payment.get('amount') / 100,
                'currency': payment.get('currency'),
                'method': payment.get('method'),
                'captured': payment.get('captured'),
                'created_at': payment.get('created_at')
            }
            
        except Exception as e:
            logger.error(f"Error getting Razorpay payment status: {str(e)}")
            return False, f"Error getting Razorpay payment status: {str(e)}"
    
    def _get_stripe_payment_status(self, payment_intent_id):
        """Get Stripe payment status"""
        if not STRIPE_AVAILABLE:
            return False, "Stripe library not available"
        
        try:
            if not self.stripe_publishable_key:
                return False, "Stripe publishable key not configured"
            
            stripe.api_key = self.stripe_publishable_key
            
            # Get payment intent
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return True, {
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency,
                'created_at': intent.created,
                'charges': intent.charges.data if hasattr(intent, 'charges') else []
            }
            
        except Exception as e:
            logger.error(f"Error getting Stripe payment status: {str(e)}")
            return False, f"Error getting Stripe payment status: {str(e)}"
    
    def _get_paypal_payment_status(self, payment_id):
        """Get PayPal payment status"""
        if not PAYPAL_AVAILABLE:
            return False, "PayPal library not available"
        
        try:
            # Configure PayPal SDK
            if self.paypal_sandbox:
                paypalrestsdk.configure(
                    mode="sandbox",
                    client_id=self.paypal_client_id,
                    client_secret=self.paypal_client_secret
                )
            else:
                paypalrestsdk.configure(
                    mode="live",
                    client_id=self.paypal_client_id,
                    client_secret=self.paypal_client_secret
                )
            
            # Get payment details
            payment = paypalrestsdk.Payment.find(payment_id)
            
            return True, {
                'status': payment.state,
                'amount': payment.transactions[0].amount.total,
                'currency': payment.transactions[0].amount.currency,
                'created_at': payment.create_time,
                'update_time': payment.update_time
            }
            
        except Exception as e:
            logger.error(f"Error getting PayPal payment status: {str(e)}")
            return False, f"Error getting PayPal payment status: {str(e)}"

# Initialize payment gateway
payment_gateway = PaymentGateway()
