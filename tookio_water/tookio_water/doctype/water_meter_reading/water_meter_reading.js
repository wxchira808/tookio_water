frappe.ui.form.on('Water Meter Reading', {
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'tookio_water.tookio_water.doctype.water_meter_reading.water_meter_reading.get_previous_reading',
                args: {
                    customer: frm.doc.customer
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('previous_water_reading', r.message);
                    }
                }
            });
        }
    },
    paid: function(frm) {
        frm.set_value('status', frm.doc.paid ? 'Paid' : 'Unpaid');
    },
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
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