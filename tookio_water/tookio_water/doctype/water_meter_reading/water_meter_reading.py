# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe

from frappe.model.document import Document

class WaterMeterReading(Document):

    def validate(self):
        # Calculate units used
        self.units_used = self.current_water_reading - (self.previous_water_reading or 0)
        
        # Calculate billed amount
        self.billed_amount = self.units_used * (self.rate_per_unit or 0)
        
        # Determine payment status automatically
        paid_amount = self.actual_paid_amount or 0
        if paid_amount >= self.billed_amount and self.billed_amount > 0:
            self.status = 'Paid'
        elif paid_amount > 0 and paid_amount < self.billed_amount:
            self.status = 'Partially Paid'
        else:
            self.status = 'Unpaid'
    
    def on_submit(self):
        # Update customer balance when submitted
        self.update_customer_balance()
    
    def on_cancel(self):
        # Reverse customer balance when cancelled
        self.update_customer_balance(reverse=True)
    
    def update_customer_balance(self, reverse=False):
        if not self.customer:
            return
        
        customer = frappe.get_doc('Water Customer', self.customer)
        current_balance = customer.current_balance or 0
        
        # Calculate the net change to balance
        billed = self.billed_amount or 0
        paid = self.actual_paid_amount or 0
        net_change = billed - paid
        
        if reverse:
            # Reverse the transaction
            customer.current_balance = current_balance - net_change
        else:
            # Apply the transaction
            customer.current_balance = current_balance + net_change
        
        customer.save(ignore_permissions=True)

@frappe.whitelist()
def send_billing_reminder(docname):
    doc = frappe.get_doc('Water Meter Reading', docname)
    if not doc.customer:
        return "No customer selected"
    
    customer = frappe.get_doc('Water Customer', doc.customer)
    if not customer.phone:
        return "No phone number for customer"
    
    # Get current balance from customer record
    balance = customer.current_balance or 0
    message = f"Dear {customer.customer_name}, your current outstanding water bill balance is KES {balance:,.2f}. Please pay promptly. Thank you."
    
    try:
        from frappe.core.doctype.sms_settings.sms_settings import send_sms
        send_sms([customer.phone], message)
        doc.notification_status = 'Sent'
        doc.save(ignore_permissions=True)
        return "SMS sent successfully"
    except Exception as e:
        doc.notification_status = 'Failed'
        doc.save(ignore_permissions=True)
        return f"Failed to send SMS: {str(e)}"

@frappe.whitelist()
def get_previous_reading(customer):
    last_reading = frappe.db.get_value('Water Meter Reading', {'customer': customer}, 'current_water_reading', order_by='date desc')
    return last_reading or 0