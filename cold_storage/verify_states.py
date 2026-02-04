import frappe
from frappe.utils import today

def test():
    print("Starting state verification with valid data...")
    try:
        # Get valid master data dynamically
        company = frappe.db.get_all("Company", limit=1, pluck="name")[0]
        customer = frappe.db.get_all("Customer", limit=1, pluck="name")[0]
        warehouse = frappe.db.get_all("Warehouse", limit=1, pluck="name")[0]
        
        # Get an existing valid item and batch to pass validation
        item_data = frappe.db.sql("SELECT parent, goods_item, item_group, batch_no FROM `tabCold Storage Receipt Item` LIMIT 1", as_dict=True)[0]
        item = item_data.goods_item
        item_group = item_data.item_group
        batch_no = item_data.batch_no
        
        print(f"Using: Company={company}, Customer={customer}, Warehouse={warehouse}, Item={item}, Batch={batch_no}")
        
        # 1. Create and Submit
        receipt = frappe.get_doc({
            'doctype': 'Cold Storage Receipt',
            'customer': customer,
            'warehouse': warehouse,
            'receipt_date': today(),
            'company': company,
            'items': [{'goods_item': item, 'item_group': item_group, 'number_of_bags': 1, 'batch_no': batch_no}]
        })
        receipt.insert()
        receipt.submit()
        se = receipt.stock_entry
        print(f"Original Submitted: Receipt {receipt.name} (docstatus:{receipt.docstatus}), SE {se} (docstatus:{frappe.db.get_value('Stock Entry', se, 'docstatus')})")

        # 2. Cancel
        receipt.cancel()
        print(f"Original Cancelled: Receipt {receipt.name} (docstatus:{receipt.docstatus}), SE {se} (docstatus:{frappe.db.get_value('Stock Entry', se, 'docstatus')})")

        # 3. Amend
        print("Amending...")
        amended = frappe.copy_doc(receipt)
        amended.amended_from = receipt.name
        amended.docstatus = 0
        amended.name = None
        amended.insert()
        print(f"Amended Draft: {amended.name} (docstatus:{amended.docstatus})")

        # 4. Submit Amendment
        amended.submit()
        print(f"Amended Submitted: {amended.name} (docstatus:{amended.docstatus})")

        # 5. Final verification of original
        orig_ds = frappe.db.get_value("Cold Storage Receipt", receipt.name, "docstatus")
        orig_se_ds = frappe.db.get_value("Stock Entry", se, "docstatus")
        print(f"VERIFICATION RESULTS:")
        print(f"Original Receipt {receipt.name} status: {orig_ds} (Expected 2)")
        print(f"Original Stock Entry {se} status: {orig_se_ds} (Expected 2)")

        if orig_ds == 2 and orig_se_ds == 2:
            print("SUCCESS: Original documents remained CANCELLED.")
        else:
            print("FAILURE: State mismatch!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
