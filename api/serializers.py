from rest_framework import serializers

from accounts.models import User
from companies.models import Company
from vendors.models import (
    Vendor,
    VendorContact,
    VendorBankDetails,
    VendorDocument,
    VendorPerformanceHistory,
)
from products.models import Category, Product

from procurement.models import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RequisitionApproval,
)

from rfq.models import (
    RFQ,
    RFQItem,
    RFQVendor,
)

from quotations.models import (
    Quotation,
    QuotationItem,
    QuotationComparison,
)

from purchase_orders.models import (
    PurchaseOrder,
    PurchaseOrderItem,
)

from deliveries.models import (
    Delivery,
    DeliveryItem,
)

from invoices.models import (
    Invoice,
    InvoiceItem,
)

from payments.models import Payment

from notifications.models import Notification

from audit_logs.models import AuditLog


# ============================================================
# USER / AUTHENTICATION
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password", None)

        user = User(**validated_data)

        if password:
            user.set_password(password)

        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance


# ============================================================
# COMPANY
# ============================================================

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


# ============================================================
# VENDOR
# ============================================================

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class VendorContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorContact
        fields = "__all__"


class VendorBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorBankDetails
        fields = "__all__"


class VendorDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorDocument
        fields = "__all__"


class VendorPerformanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPerformanceHistory
        fields = "__all__"


# ============================================================
# PRODUCT / CATEGORY
# ============================================================

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


# ============================================================
# PURCHASE REQUISITION
# ============================================================

class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        fields = "__all__"


class PurchaseRequisitionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisitionItem
        fields = "__all__"


class RequisitionApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitionApproval
        fields = "__all__"


# ============================================================
# RFQ
# ============================================================

class RFQSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQ
        fields = "__all__"


class RFQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQItem
        fields = "__all__"


class RFQVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQVendor
        fields = "__all__"


# ============================================================
# QUOTATION
# ============================================================

class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = "__all__"


class QuotationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationItem
        fields = "__all__"


class QuotationComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationComparison
        fields = "__all__"


# ============================================================
# PURCHASE ORDER
# ============================================================

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = "__all__"


# ============================================================
# DELIVERY
# ============================================================

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"


class DeliveryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryItem
        fields = "__all__"


# ============================================================
# INVOICE
# ============================================================

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


# ============================================================
# PAYMENT
# ============================================================

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = (
            "created_at",
        )