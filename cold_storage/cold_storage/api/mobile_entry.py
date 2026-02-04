import frappe
import json

@frappe.whitelist()
def submit_mobile_receipt(data):
    """
    Creates a Cold Storage Receipt from simplified mobile data.
    """
    if isinstance(data, str):
        data = json.loads(data)

    receipt = frappe.new_doc("Cold Storage Receipt")
    receipt.receipt_type = "New Receipt"
    receipt.customer = data.get("customer")
    receipt.warehouse = data.get("warehouse")
    receipt.vehicle_no = data.get("vehicle_no")
    receipt.driver_name = data.get("driver_name")
    receipt.driver_phone = data.get("driver_phone")
    # Set company for naming series
    company = data.get("company")
    if not company:
        company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
    receipt.company = company
    receipt.receipt_date = frappe.utils.nowdate()

    for item in data.get("items", []):
        batch_no = item.get("batch")
        item_code = item.get("item_code")
        
        # Ensure Batch exists or create it
        if batch_no and not frappe.db.exists("Batch", batch_no):
            batch = frappe.new_doc("Batch")
            batch.batch_id = batch_no
            batch.item = item_code
            batch.customer = data.get("customer")
            batch.insert()
            
        receipt.append("items", {
            "goods_item": item_code,
            "number_of_bags": frappe.utils.flt(item.get("qty")),
            "batch_no": batch_no,
            "item_group": item.get("item_group")
        })

    receipt.insert()
    return receipt.name
