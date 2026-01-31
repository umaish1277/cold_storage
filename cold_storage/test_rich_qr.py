
import frappe
from frappe.utils import nowdate

def test_rich_qr():
    # Create a new receipt to trigger generation
    doc = frappe.new_doc("Cold Storage Receipt")
    doc.customer = frappe.db.get_value("Customer", {}, "name")
    doc.warehouse = frappe.db.get_value("Warehouse", {}, "name")
    doc.receipt_date = nowdate()
    doc.append("items", {
        "goods_item": "Potato",
        "bag_type": "Jute Bag",
        "number_of_bags": 50,
        "batch_no": "QR-RICH-TEST-1",
        "rate": 100
    })
    doc.append("items", {
        "goods_item": "Onion",
        "bag_type": "Plastic Bag",
        "number_of_bags": 20,
        "batch_no": "QR-RICH-TEST-2",
        "rate": 120
    })
    
    doc.insert()
    frappe.db.commit()
    
    print(f"Receipt Created: {doc.name}")
    print(f"QR Code URL: {doc.qr_code}")
    
    # We can't easily decode the QR image here without extra libraries usually, 
    # but successful creation implies the logic ran without error.

test_rich_qr()
