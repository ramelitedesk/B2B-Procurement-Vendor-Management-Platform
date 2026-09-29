from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AuthViewSet,

    UserViewSet,
    CompanyViewSet,

    VendorViewSet,
    VendorContactViewSet,
    VendorBankDetailsViewSet,
    VendorDocumentViewSet,
    VendorPerformanceHistoryViewSet,

    CategoryViewSet,
    ProductViewSet,

    PurchaseRequisitionViewSet,
    PurchaseRequisitionItemViewSet,
    RequisitionApprovalViewSet,

    RFQViewSet,
    RFQItemViewSet,
    RFQVendorViewSet,

    QuotationViewSet,
    QuotationItemViewSet,
    QuotationComparisonViewSet,

    PurchaseOrderViewSet,
    PurchaseOrderItemViewSet,

    DeliveryViewSet,
    DeliveryItemViewSet,

    InvoiceViewSet,
    InvoiceItemViewSet,

    PaymentViewSet,

    NotificationViewSet,

    AuditLogViewSet,
)


router = DefaultRouter()


# Authentication
router.register(
    r"auth",
    AuthViewSet,
    basename="auth",
)


# Users
router.register(
    r"users",
    UserViewSet,
    basename="users",
)


# Companies
router.register(
    r"companies",
    CompanyViewSet,
    basename="companies",
)


# Vendors
router.register(
    r"vendors",
    VendorViewSet,
    basename="vendors",
)

router.register(
    r"vendor-contacts",
    VendorContactViewSet,
    basename="vendor-contacts",
)

router.register(
    r"vendor-bank-details",
    VendorBankDetailsViewSet,
    basename="vendor-bank-details",
)

router.register(
    r"vendor-documents",
    VendorDocumentViewSet,
    basename="vendor-documents",
)

router.register(
    r"vendor-performance",
    VendorPerformanceHistoryViewSet,
    basename="vendor-performance",
)


# Products
router.register(
    r"categories",
    CategoryViewSet,
    basename="categories",
)

router.register(
    r"products",
    ProductViewSet,
    basename="products",
)


# Procurement
router.register(
    r"purchase-requisitions",
    PurchaseRequisitionViewSet,
    basename="purchase-requisitions",
)

router.register(
    r"purchase-requisition-items",
    PurchaseRequisitionItemViewSet,
    basename="purchase-requisition-items",
)

router.register(
    r"requisition-approvals",
    RequisitionApprovalViewSet,
    basename="requisition-approvals",
)


# RFQ
router.register(
    r"rfqs",
    RFQViewSet,
    basename="rfqs",
)

router.register(
    r"rfq-items",
    RFQItemViewSet,
    basename="rfq-items",
)

router.register(
    r"rfq-vendors",
    RFQVendorViewSet,
    basename="rfq-vendors",
)


# Quotations
router.register(
    r"quotations",
    QuotationViewSet,
    basename="quotations",
)

router.register(
    r"quotation-items",
    QuotationItemViewSet,
    basename="quotation-items",
)

router.register(
    r"quotation-comparisons",
    QuotationComparisonViewSet,
    basename="quotation-comparisons",
)


# Purchase Orders
router.register(
    r"purchase-orders",
    PurchaseOrderViewSet,
    basename="purchase-orders",
)

router.register(
    r"purchase-order-items",
    PurchaseOrderItemViewSet,
    basename="purchase-order-items",
)


# Deliveries
router.register(
    r"deliveries",
    DeliveryViewSet,
    basename="deliveries",
)

router.register(
    r"delivery-items",
    DeliveryItemViewSet,
    basename="delivery-items",
)


# Invoices
router.register(
    r"invoices",
    InvoiceViewSet,
    basename="invoices",
)

router.register(
    r"invoice-items",
    InvoiceItemViewSet,
    basename="invoice-items",
)


# Payments
router.register(
    r"payments",
    PaymentViewSet,
    basename="payments",
)


# Notifications
router.register(
    r"notifications",
    NotificationViewSet,
    basename="notifications",
)


# Audit Logs
router.register(
    r"audit-logs",
    AuditLogViewSet,
    basename="audit-logs",
)


urlpatterns = [
    path("", include(router.urls)),
]