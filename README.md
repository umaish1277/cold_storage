# Cold Storage Management for Frappe

A comprehensive Cold Storage Management application built on the Frappe Framework. This app streamlines the process of managing inward and outward stock of agricultural goods (like Potatoes, Onions) stored in bags, automates billing based on storage duration, and integrates seamlessly with ERPNext for accounting.

## Features

### 1. Inward & Outward Management
*   **Cold Storage Receipt**: Record incoming stock with details like Customer, Warehouse, Item, Bag Type, and Batch Number.
*   **Cold Storage Dispatch**: Manage outgoing stock linked to specific receipts. Ensures you cannot dispatch more than the received quantity (Batch-level validation).

### 2. Automated Billing & Invoicing
*   **Flexible Billing Types**: Support for **Daily**, **Monthly**, and **Seasonal** billing cycles.
*   **Smart Rate Fetching**:
    *   Define Handling and Loading charges per **Bag Type** (e.g., Jute Bag = ₹10).
    *   Override rates for specific **Item + Bag Type** combinations (e.g., Potato in Jute Bag = ₹15).
*   **Loading/Unloading Charges**: Automatically calculates and adds loading charges to the invoice.
*   **GST Integration**: Automatically applies GST on storage and service charges based on your configuration.
*   **Sales Invoice Automation**: Automatically creates and links an ERPNext Sales Invoice upon submission of a Dispatch.

### 3. Inventory & Reporting
*   **Customer Stock Ledger**: A detailed report showing Inward, Outward, and Balance quantity per Customer and Batch. Includes filters for Date Range, Item, and Bag Type.
*   **Dashboard**:
    *   **Incoming Bags**: Bar chart visualizing inflow trends.
    *   **Outgoing Bags**: Bar chart visualizing outflow trends.
    *   **Active Batches**: Number card for quick status.

## Configuration

### Cold Storage Settings
navigate to **Cold Storage > Cold Storage Settings** to configure:

1.  **Bag Type Rates**:
    *   Add rows for each Bag Type (e.g., "Jute Bag").
    *   Set **Handling Charge (Per Bag)**.
    *   Set **Loading Charge (Per Bag)**.
    *   *(Optional)* Link a specific **Goods Item** to set a special rate for that item. Leave empty to apply to all items using that bag type.
2.  **GST Configuration**:
    *   Link the **GST on Services Account** (e.g., "Output Tax GST").

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

1.  **Setup**: Configure `Cold Storage Settings` with your rates and tax account.
2.  **Inward**: Create a `Cold Storage Receipt` when goods arrive. Status will be *Draft* -> *Submitted*.
3.  **Outward**: Create a `Cold Storage Dispatch`. Select the `Linked Receipt` and the Batch.
4.  **Validation**: The system checks if sufficient balance exists in the batch.
5.  **Billing**: The system calculates Handling + Loading charges based on the quantity and duration (if time-based).
6.  **Invoice**: Upon Submitting the Dispatch, a **Sales Invoice** is generated in ERPNext and linked to the Dispatch.

## License

MIT
