# Cold Storage Management for Frappe

A comprehensive Cold Storage Management application built on the Frappe Framework. This app streamlines the process of managing inward and outward stock of agricultural goods (like Potatoes, Onions) stored in bags, automates billing based on storage duration and item groups, and integrates seamlessly with ERPNext for accounting.

## Features

### 1. Inward & Outward Management
*   **Cold Storage Receipt**: Record incoming stock with details like Customer, Warehouse, Item, **Item Group**, and Batch Number. Supports full-width UI for large data tables.
*   **Cold Storage Dispatch**: Manage outgoing stock linked to specific receipts. Ensures you cannot dispatch more than the received quantity (Batch-level validation).
*   **QR Code Tracking**: Print Receipts with embedded QR codes for quick scanning and retrieval.

### 2. Rate Card Management
*   **Seasons**: Define time-bound business seasons (e.g., Summer 2026) for differentiated pricing.
*   **Customer Tiers**: Categorize customers (e.g., VIP, Gold, Standard) to offer tiered storage rates.
*   **Prioritized Rates**: Define specific rate cards for combinations of Item Group, Season, and Tier. The system automatically fetches the most specific rate with a fallback to global settings.

### 3. Automated Billing & Invoicing
*   **Flexible Billing Types**: Support for **Daily**, **Monthly**, and **Seasonal** billing cycles.
*   **Smart Rate Fetching**: Automatically calculates Handling, Loading, and Storage charges based on **Item Group**, **Customer Tier**, and **Active Season**.
*   **ERPNext Integration**: Automatically creates and links an ERPNext Sales Invoice upon submission of a Dispatch.

### 4. Customer Portal & Financial Transparency
*   **Stock Statements**: Customers can download a PDF/XLSX stock statement.
*   **Financial Summary**: Includes Total Outstanding, Recent Invoices, and Payment History directly in the PDF.
*   **Stock Visualization**: Interactive charts for inventory trends and batch-wise distribution.
*   **Urdu Support**: Full Right-to-Left (RTL) support and high-quality Urdu typography for all portal reports.

### 5. Mobile Entry System
... (rest of the content)
*   **Simplified UI**: A dedicated page for fast, mobile-friendly receipt entry.
*   **Smart Defaults**: Automatically pulls the Default Company from settings and filters warehouses accordingly.
*   **Pro Driver Tracking**: Driver name and phone fields with a searchable country code selector (Defaults to Pakistan +92).
*   **Fault Tolerance**: Preserves all form data if a submission fails, allowing for quick correction and retry.

### 4. Advanced Reporting & Audit
*   **Audit Trail Report**: A detailed log of **who changed what and when**, tracking field-level changes (Old vs. New values) across core documents.
*   **Warehouse Heatmaps**: Visual reports for warehouse utilization and occupancy trends.
*   **Customer Stock Ledger**: Real-time visibility into customer-wise and batch-wise stock levels.

### 5. Notifications & Approvals
*   **Approval System**: Automated manager notifications for arrivals and dispatches requiring approval.
*   **Smart Persistence**: Popup notifications stay dismissed across logins and automatically suppress themselves on relevant list views.
*   **WhatsApp Integration**: Instant customer alerts for "Goods Received" and "Goods Dispatched" via Twilio.

## Configuration

### Cold Storage Settings
Navigate to **Cold Storage > Cold Storage Settings** to configure global defaults:
1.  **Default Company**: Primary company for auto-naming and mobile entry.
2.  **Item Group Rates**: Set Handling and Loading charges per bag type.
3.  **Transfer Rates**: Configure inter and intra-warehouse loading rates.

## Roles and Permissions
1.  **Cold Storage Manager**: Full administrative access, including system configuration and document submission.
2.  **Cold Storage Accountant**: Created/Edit draft documents and view all finance reports.
3.  **Cold Storage User**: Restricted access to view own stock and activity.

## Installation

```bash
bench get-app cold_storage [repo-url]
bench --site [site-name] install-app cold_storage
bench --site [site-name] migrate
```

## Usage Workflow

1.  **Setup**: Configure rates and default company in `Cold Storage Settings`.
2.  **Inward**: Create a `Receipt` (Desktop or Mobile).
3.  **Approve**: Manager approves the inward movement.
4.  **Outward**: Create a `Dispatch` linked to the receipt.
5.  **Invoicing**: Submission automatically generates the Sales Invoice in ERPNext.

## License
MIT
