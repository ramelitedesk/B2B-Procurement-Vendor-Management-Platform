# B2B Procurement & Vendor Management Platform

A full-stack B2B Procurement and Vendor Management Platform developed using Django to manage procurement operations, vendors, products, purchase requisitions, RFQs, quotations, purchase orders, deliveries, invoices, payments, notifications, reports, and audit logs.

---

## 🚀 Project Overview

This platform is designed to digitize and manage the complete procurement lifecycle between companies, procurement teams, and vendors.

### Procurement Workflow

Employee
→ Purchase Requisition
→ Manager Approval
→ RFQ
→ Vendor Quotations
→ Quotation Comparison
→ Vendor Selection
→ Purchase Order
→ Delivery
→ Invoice
→ Payment

---

## ✨ Features

### 🔐 Authentication & Role-Based Access

- Custom Django User Model
- Role-Based Access Control (RBAC)
- Super Admin
- Company Admin
- Procurement Manager
- Employee / Requester
- Vendor
- User profile management
- Account status management

---

### 🏢 Company Management

- Company profile management
- Registration details
- GST information
- Contact details
- Company status
- Employee management

---

### 🏪 Vendor Management

- Vendor profiles
- Vendor contacts
- Vendor bank details
- Vendor documents
- GST and registration information
- Vendor status management
- Vendor ratings
- Vendor performance history

---

### 📦 Product & Category Management

- Product management
- Service management
- Product categories
- SKU management
- Unit management
- Estimated pricing
- Tax configuration
- Product status management

---

### 📝 Purchase Requisition

- Create purchase requisitions
- Add multiple products
- Quantity management
- Required date
- Request reason
- Requisition status tracking
- Draft and submission workflow

### Requisition Workflow

```text
Draft
  ↓
Submitted
  ↓
Pending Approval
  ↓
Approved / Rejected
