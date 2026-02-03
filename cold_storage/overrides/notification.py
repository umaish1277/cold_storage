
import frappe
from frappe.email.doctype.notification.notification import Notification
from cold_storage.cold_storage.utils import send_whatsapp

class CustomNotification(Notification):
    def send_notification_by_channel(self, doc, context):
        if self.channel == "WhatsApp":
            self.send_whatsapp_msg(doc, context)
        else:
            super().send_notification_by_channel(doc, context)

    def send_whatsapp_msg(self, doc, context):
        # Render message
        message = frappe.render_template(self.message, context)
        
        # Determine Recipient
        # We use the same get_receiver_list logic but force 'mobile_no'
        receiver_list = self.get_receiver_list(doc, context, "mobile_no", self.get_mobile_no)
        
        if not receiver_list:
            return

        for mobile in receiver_list:
            if mobile:
                try:
                    send_whatsapp(mobile, message)
                    frappe.msgprint(f"WhatsApp sent to {mobile}")
                except Exception as e:
                    self.log_error(f"WhatsApp Failure: {str(e)}")
