frappe.ui.form.on('Water Meter Reading', {
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'tookio_water.tookio_water.doctype.water_meter_reading.water_meter_reading.get_previous_reading',
                args: {
                    customer: frm.doc.customer
                },
                callback: function(r) {
                    if (r.message !== undefined) {
                        frm.set_value('previous_water_reading', r.message);
                    }
                }
            });
        }
    },
    previous_water_reading: function(frm) {
        calculate_units_used(frm);
    },
    current_water_reading: function(frm) {
        calculate_units_used(frm);
    },
    rate_per_unit: function(frm) {
        calculate_billed_amount(frm);
    },
    actual_paid_amount: function(frm) {
        update_payment_status(frm);
    },
    refresh: function(frm) {
        // Show customer balance button
        if (frm.doc.customer) {
            frm.add_custom_button(__('Show Customer Balance'), function() {
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Water Customer',
                        filters: { name: frm.doc.customer },
                        fieldname: ['customer_name', 'current_balance']
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __('Customer Balance'),
                                message: __('Customer: {0}<br>Current Balance: <b>{1}</b>', 
                                    [r.message.customer_name, format_currency(r.message.current_balance)]),
                                indicator: r.message.current_balance > 0 ? 'red' : 'green'
                            });
                        }
                    }
                });
            });
        }
        
        // Send billing reminder button (only for submitted docs)
        if (!frm.doc.__islocal && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Send Billing Reminder'), function() {
                frappe.call({
                    method: 'tookio_water.tookio_water.doctype.water_meter_reading.water_meter_reading.send_billing_reminder',
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
    }
});

function calculate_units_used(frm) {
    if (frm.doc.previous_water_reading !== undefined && frm.doc.current_water_reading !== undefined) {
        var units = frm.doc.current_water_reading - frm.doc.previous_water_reading;
        frm.set_value('units_used', units);
        calculate_billed_amount(frm);
    }
}

function calculate_billed_amount(frm) {
    if (frm.doc.units_used !== undefined && frm.doc.rate_per_unit !== undefined) {
        var billed = frm.doc.units_used * frm.doc.rate_per_unit;
        frm.set_value('billed_amount', billed);
        update_payment_status(frm);
    }
}

function update_payment_status(frm) {
    if (frm.doc.billed_amount !== undefined) {
        var paid = frm.doc.actual_paid_amount || 0;
        var billed = frm.doc.billed_amount || 0;
        
        if (paid >= billed && billed > 0) {
            frm.set_value('status', 'Paid');
        } else if (paid > 0 && paid < billed) {
            frm.set_value('status', 'Partially Paid');
        } else {
            frm.set_value('status', 'Unpaid');
        }
    }
}