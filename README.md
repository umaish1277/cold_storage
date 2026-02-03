# Cold Storage Management for Frappe

A comprehensive Cold Storage Management application built on the Frappe Framework. This app streamlines the process of managing inward and outward stock of agricultural goods (like Potatoes, Onions) stored in bags, automates billing based on storage duration and item groups, and integrates seamlessly with ERPNext for accounting.

## Features

### 1. Inward & Outward Management
*   **Cold Storage Receipt**: Record incoming stock with details like Customer, Warehouse, Item, **Item Group**, and Batch Number.
*   **Cold Storage Dispatch**: Manage outgoing stock linked to specific receipts. Ensures you cannot dispatch more than the received quantity (Batch-level validation).
*   **QR Code Tracking**: Print Receipts with embedded QR codes for quick scanning and retrieval.

### 2. Automated Billing & Invoicing
*   **Flexible Billing Types**: Support for **Daily**, **Monthly**, and **Seasonal** billing cycles.
*   **Smart Rate Fetching**:
    *   Define Handling and Loading charges per **Item Group** (e.g., Jute Bag = 10).
    *   Override rates for specific **Item + Item Group** combinations (e.g., Potato in Jute Bag = 15).
*   **Loading/Unloading Charges**: Automatically calculates and adds loading charges to the invoice.
*   **GST Integration**: Automatically applies GST on storage and service charges based on your configuration.
*   **Sales Invoice Automation**: Automatically creates and links an ERPNext Sales Invoice upon submission of a Dispatch.

### 3. CRM & Notifications
*   **WhatsApp Integration**: Built-in support for sending WhatsApp notifications using **Twilio**.
*   **Standard Notifications**: Uses Frappe's standard `Notification` doctype.
    *   **Automated Alerts**: Customers receive instant WhatsApp updates for "Goods Received" and "Goods Dispatched".
    *   **Customizable Templates**: Edit message content directly via the Desk UI using Jinja templates.

### 4. Inventory & Reporting
*   **Customer Stock Ledger**: A detailed report showing Inward, Outward, and Balance quantity per Customer and Batch. Includes filters for Date Range, Item, and Item Group.
*   **Dashboard**:
    *   **Inflow Trends**: Charts visualizing incoming stock over time by Item Group.
    *   **Outflow Trends**: Charts visualizing outgoing stock over time by Item Group.
    *   **Total Stock**: Line chart showing stock trends showing the net balance of bags.
    *   **Active Batches**: Number card for quick status updates.

### 5. Customer Portal
*   **Self-Service**: Customers can log in to view their own stock status.
*   **Dashboard**: Interactive charts showing Recent Activity, Inward vs. Outward totals, and Stock by Item Group.

## Configuration

### Cold Storage Settings
Navigate to **Cold Storage > Cold Storage Settings** to configure:

1.  **Rate Configuration**:
    *   Add rows for each **Item Group**.
    *   Set **Handling Charge (Per Bag)** and **Loading Charge**.
    *   *(Optional)* Link a specific **Goods Item** to set a special rate for that item.
2.  **GST Configuration**:
    *   Link the **GST on Services Account** (e.g., "Output Tax GST").

### WhatsApp Configuration
Navigate to **Cold Storage > Cold Storage WhatsApp Settings**:

1.  **Provider**: Select "Twilio".
2.  **Credentials**: Enter your Account SID, Auth Token, and Sender Number (e.g., `whatsapp:+14155238886`).
3.  **Enable**: Toggle "Enabled" to start sending messages.

## Roles and Permissions

The app comes with pre-configured roles to manage access control:

1.  **Cold Storage Manager**
    *   **Access**: Full Admin Access.
    *   **Capabilities**: Can Create, Edit, **Submit**, Cancel, and Amend Receipts and Dispatches. Can configure Settings.

2.  **Cold Storage Accountant**
    *   **Access**: Operational / Accounts.
    *   **Capabilities**: Can Create and Edit documents (Draft state only). Can View Reports. **Cannot Submit** documents.

3.  **Cold Storage User**
    *   **Access**: Customer / External User.
    *   **Capabilities**: View-only access to their **own** entries (documents they created or are owner of).

## Installation

1.  Get the app:
    ```bash
    bench get-app cold_storage https://github.com/your-repo/cold_storage
    ```
2.  Install on site:
    ```bash
    bench --site [site-name] install-app cold_storage
    ```
3.  Migrate database:
    ```bash
    bench --site [site-name] migrate
    ```

## Usage Workflow

1.  **Setup**: Configure `Cold Storage Settings` with your rates and `Cold Storage WhatsApp Settings` with credentials.
2.  **Inward**: Create a `Cold Storage Receipt` when goods arrive. Select the **Item Group** (e.g., Jute Bag).
    *   *Result*: Whatsapp notification sent to customer.
3.  **Outward**: Create a `Cold Storage Dispatch`. Select the `Linked Receipt` and the Batch.
4.  **Billing**: The system calculates Handling + Loading charges based on the quantity, duration, and Item Group rates.
5.  **Invoice**: Upon Submitting the Dispatch, a **Sales Invoice** is generated in ERPNext.
    *   *Result*: Whatsapp notification sent to customer.

## License

MIT
# cold_storage
# cold_storage
