#!/usr/bin/env python3
"""
Recalculate all customer balances from submitted Water Meter Readings.
Run this script to fix balances after the balance tracking system was implemented.

Usage:
    bench --site your-site-name execute tookio_water.tookio_water.doctype.water_meter_reading.recalculate_balances.recalculate_all_balances
"""

import frappe

def recalculate_all_balances():
    """Recalculate balances for all customers based on submitted readings."""
    
    # Reset all customer balances to 0
    customers = frappe.get_all('Water Customer', fields=['name'])
    for customer in customers:
        frappe.db.set_value('Water Customer', customer.name, 'current_balance', 0)
    
    frappe.db.commit()
    print(f"Reset {len(customers)} customer balances to 0")
    
    # Get all submitted water meter readings ordered by date
    readings = frappe.get_all(
        'Water Meter Reading',
        filters={'docstatus': 1},
        fields=['name', 'customer', 'date', 'billed_amount', 'actual_paid_amount'],
        order_by='date asc, creation asc'
    )
    
    print(f"\nProcessing {len(readings)} submitted readings...")
    
    # Process each reading in chronological order
    for reading in readings:
        if not reading.customer:
            continue
            
        customer = frappe.get_doc('Water Customer', reading.customer)
        current_balance = customer.current_balance or 0
        
        billed = reading.billed_amount or 0
        paid = reading.actual_paid_amount or 0
        net_change = billed - paid
        
        new_balance = current_balance + net_change
        
        frappe.db.set_value('Water Customer', reading.customer, 'current_balance', new_balance)
        
        print(f"{reading.name}: {reading.customer} | Old: {current_balance:.2f} | Change: {net_change:.2f} | New: {new_balance:.2f}")
    
    frappe.db.commit()
    print(f"\nRecalculation complete! Updated {len(readings)} readings.")
    
    # Show final balances
    print("\n=== Final Customer Balances ===")
    customers_with_balance = frappe.get_all(
        'Water Customer',
        fields=['name', 'customer_name', 'current_balance'],
        order_by='current_balance desc'
    )
    
    for customer in customers_with_balance:
        if customer.current_balance != 0:
            status = "CREDIT" if customer.current_balance < 0 else "OWES"
            print(f"{customer.customer_name}: {customer.current_balance:.2f} ({status})")
