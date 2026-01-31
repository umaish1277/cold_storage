import frappe
from frappe.utils import today

def test_batch_accounting():
    print("Testing Batch Accounting Logic...")
    
    # Prerequisite: Ensure Item and Customer exist
    if not frappe.db.exists("Item", "Test Item Batch"):
        item = frappe.new_doc("Item")
        item.item_code = "Test Item Batch"
        item.item_group = "Products"
        item.is_stock_item = 0
        item.save()
        
    if not frappe.db.exists("Customer", "Test Customer Batch"):
        cust = frappe.new_doc("Customer")
        cust.customer_name = "Test Customer Batch"
        cust.save()
        
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        companies = frappe.get_all("Company", limit=1)
        if companies:
            company = companies[0].name
        else:
            # Create company if none
            c = frappe.new_doc("Company")
            c.company_name = "Cold Storage"
            c.abbr = "CS"
            c.default_currency = "INR"
            c.insert()
            company = c.name

    warehouse_name = "Finished Goods - CS"
    if not frappe.db.exists("Warehouse", warehouse_name):
        wh = frappe.new_doc("Warehouse")
        wh.warehouse_name = "Finished Goods - CS"
        wh.company = company 
        try:
             wh.insert()
             warehouse_name = wh.name
             print(f"Created Warehouse {wh.name}")
        except Exception as e:
             print(f"Failed to create warehouse: {e}")
             # try to find it if it was created with suffix
             existing = frappe.db.get_value("Warehouse", {"warehouse_name": "Finished Goods - CS"}, "name")
             if existing:
                 warehouse_name = existing

    # 1. Create Receipt
    print("Creating Receipt...")
    receipt = frappe.new_doc("Cold Storage Receipt")
    receipt.customer = "Test Customer Batch"
    receipt.receipt_date = today()
    receipt.warehouse = warehouse_name 
    receipt.append("items", {
        "goods_item": "Test Item Batch",
        "bag_type": "Jute Bag",
        "number_of_bags": 100,
        "batch_no": "BATCH-001",
        "rate": 0
    })
    receipt.insert()
    receipt.submit()
    print(f"Receipt {receipt.name} created with BATCH-001 (100 Qty)")
    
    # 2. Test Invalid Batch
    print("\nTest 1: Dispatch Invalid Batch")
    try:
        d1 = frappe.new_doc("Cold Storage Dispatch")
        d1.customer = "Test Customer Batch"
        d1.linked_receipt = receipt.name
        d1.dispatch_date = today()
        d1.billing_type = "Daily"
        d1.append("items", {
             "goods_item": "Test Item Batch",
             "number_of_bags": 10,
             "batch_no": "BATCH-999" # Invalid
        })
        d1.insert() # Should fail on validate
        print("FAIL: Created dispatch with invalid batch")
    except Exception as e:
        print(f"SUCCESS: Caught expected error: {e}")
        
    # 3. Test Excessive Qty
    print("\nTest 2: Dispatch Excessive Qty")
    try:
        d2 = frappe.new_doc("Cold Storage Dispatch")
        d2.customer = "Test Customer Batch"
        d2.linked_receipt = receipt.name
        d2.dispatch_date = today()
        d2.billing_type = "Daily"
        d2.append("items", {
             "goods_item": "Test Item Batch",
             "number_of_bags": 101, # > 100
             "batch_no": "BATCH-001"
        })
        d2.insert()
        print("FAIL: Created dispatch with excessive qty")
    except Exception as e:
        # frappe.throw raises ValidationError usually
        print(f"SUCCESS: Caught expected error: {e}")

    # 4. Test Valid Dispatch
    print("\nTest 3: Valid Dispatch")
    d3 = frappe.new_doc("Cold Storage Dispatch")
    d3.customer = "Test Customer Batch"
    d3.linked_receipt = receipt.name
    d3.dispatch_date = today()
    d3.billing_type = "Daily"
    d3.append("items", {
            "goods_item": "Test Item Batch",
            "number_of_bags": 50,
            "batch_no": "BATCH-001"
    })
    d3.insert()
    d3.submit()
    print(f"SUCCESS: Created valid dispatch {d3.name}")
    
    # 5. Test Remaining Balance
    print("\nTest 4: Exceed Remaining Balance")
    try:
        d4 = frappe.new_doc("Cold Storage Dispatch")
        d4.customer = "Test Customer Batch"
        d4.linked_receipt = receipt.name
        d4.dispatch_date = today()
        d4.billing_type = "Daily"
        d4.append("items", {
             "goods_item": "Test Item Batch",
             "number_of_bags": 51, # 100 - 50 = 50 remaining. 51 should fail.
             "batch_no": "BATCH-001"
        })
        d4.insert()
        print("FAIL: Created dispatch exceeding balance")
    except Exception as e:
        print(f"SUCCESS: Caught expected error: {e}")
        
    # Cleanup (optional, but good practice if repeatable)
    # frappe.db.rollback() if we want to reverse, but here we committed some.
    # We'll just leave them test data.

