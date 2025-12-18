# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe

from frappe.model.document import Document

class WaterMeterReading(Document):

    def validate(self):
        # Calculate units used
        self.units_used = self.current_water_reading - (self.previous_water_reading or 0)
        
        # Get previous balance
        previous_balance = frappe.db.get_value('Water Meter Reading', 
            {'customer': self.customer}, 'remaining_balance', order_by='date desc') or 0
        
        # Calculate remaining balance
        if self.status == 'Paid':
            self.remaining_balance = previous_balance
        else:
            self.remaining_balance = previous_balance + self.billed_amount

@frappe.whitelist()
def send_billing_reminder(docname):
    doc = frappe.get_doc('Water Meter Reading', docname)
    if not doc.customer:
        return "No customer selected"
    
    customer = frappe.get_doc('Water Customer', doc.customer)
    if not customer.phone:
        return "No phone number for customer"
    
    message = f"Dear {customer.customer_name}, your current water billing balance is {doc.remaining_balance}. Please pay promptly."
    
    try:
        from frappe.core.doctype.sms_settings.sms_settings import send_sms
        send_sms([customer.phone], message)
        doc.notification_status = 'Sent'
        doc.save()
        return "SMS sent successfully"
    except Exception as e:
        doc.notification_status = 'Failed'
        doc.save()
        return f"Failed to send SMS: {str(e)}"

@frappe.whitelist()
def get_previous_reading(customer):
    last_reading = frappe.db.get_value('Water Meter Reading', {'customer': customer}, 'current_water_reading', order_by='date desc')
    return last_reading