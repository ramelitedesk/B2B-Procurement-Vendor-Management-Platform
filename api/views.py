from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

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

from rfq.models import RFQ, RFQItem, RFQVendor

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

from .serializers import (
    UserSerializer,
    CompanySerializer,

    VendorSerializer,
    VendorContactSerializer,
    VendorBankDetailsSerializer,
    VendorDocumentSerializer,
    VendorPerformanceHistorySerializer,

    CategorySerializer,
    ProductSerializer,

    PurchaseRequisitionSerializer,
    PurchaseRequisitionItemSerializer,
    RequisitionApprovalSerializer,

    RFQSerializer,
    RFQItemSerializer,
    RFQVendorSerializer,

    QuotationSerializer,
    QuotationItemSerializer,
    QuotationComparisonSerializer,

    PurchaseOrderSerializer,
    PurchaseOrderItemSerializer,

    DeliverySerializer,
    DeliveryItemSerializer,

    InvoiceSerializer,
    InvoiceItemSerializer,

    PaymentSerializer,

    NotificationSerializer,

    AuditLogSerializer,
)


# ============================================================
# AUTHENTICATION
# ============================================================

class AuthViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]

    @action(
        detail=False,
        methods=["post"],
        url_path="login",
    )
    def login(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {
                    "detail": "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:

            return Response(
                {
                    "detail": "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:

            return Response(
                {
                    "detail": "This account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
        )


    @action(
        detail=False,
        methods=["post"],
        url_path="refresh",
    )
    def refresh(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:

            return Response(
                {
                    "detail": "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            refresh = RefreshToken(refresh_token)

            return Response(
                {
                    "access": str(refresh.access_token)
                }
            )

        except Exception:

            return Response(
                {
                    "detail": "Invalid refresh token."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


    @action(
        detail=False,
        methods=["get"],
        url_path="profile",
        permission_classes=[IsAuthenticated],
    )
    def profile(self, request):

        return Response(
            UserSerializer(request.user).data
        )


    @action(
        detail=False,
        methods=["post"],
        url_path="change-password",
        permission_classes=[IsAuthenticated],
    )
    def change_password(self, request):

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:

            return Response(
                {
                    "detail": "Old password and new password are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password(
            old_password,
            request.user.password,
        ):

            return Response(
                {
                    "detail": "Old password is incorrect."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:

            return Response(
                {
                    "detail": "New password must contain at least 8 characters."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()

        return Response(
            {
                "detail": "Password changed successfully."
            }
        )


# ============================================================
# GENERIC MODEL VIEWSET
# ============================================================

class BaseModelViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        user = self.request.user

        if hasattr(serializer.Meta.model, "company"):

            if serializer.validated_data.get("company") is None:
                serializer.save(company=user.company)
                return

        serializer.save()


# ============================================================
# USERS
# ============================================================

class UserViewSet(BaseModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return User.objects.all()

        return User.objects.filter(
            company=user.company
        )


# ============================================================
# COMPANIES
# ============================================================

class CompanyViewSet(BaseModelViewSet):

    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return Company.objects.all()

        return Company.objects.filter(
            id=user.company_id
        )


# ============================================================
# VENDORS
# ============================================================

class VendorViewSet(BaseModelViewSet):

    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return Vendor.objects.all()

        return Vendor.objects.filter(
            company=user.company
        )


class VendorContactViewSet(BaseModelViewSet):

    queryset = VendorContact.objects.all()
    serializer_class = VendorContactSerializer


class VendorBankDetailsViewSet(BaseModelViewSet):

    queryset = VendorBankDetails.objects.all()
    serializer_class = VendorBankDetailsSerializer


class VendorDocumentViewSet(BaseModelViewSet):

    queryset = VendorDocument.objects.all()
    serializer_class = VendorDocumentSerializer


class VendorPerformanceHistoryViewSet(BaseModelViewSet):

    queryset = VendorPerformanceHistory.objects.all()
    serializer_class = VendorPerformanceHistorySerializer


# ============================================================
# PRODUCTS
# ============================================================

class CategoryViewSet(BaseModelViewSet):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return Category.objects.all()

        return Category.objects.filter(
            company=user.company
        )


class ProductViewSet(BaseModelViewSet):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return Product.objects.all()

        return Product.objects.filter(
            company=user.company
        )


# ============================================================
# PURCHASE REQUISITIONS
# ============================================================

class PurchaseRequisitionViewSet(BaseModelViewSet):

    queryset = PurchaseRequisition.objects.all()
    serializer_class = PurchaseRequisitionSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return PurchaseRequisition.objects.all()

        return PurchaseRequisition.objects.filter(
            company=user.company
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="submit",
    )
    def submit(self, request, pk=None):

        requisition = self.get_object()

        try:

            requisition.submit_for_approval()

            return Response(
                PurchaseRequisitionSerializer(
                    requisition
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):

        requisition = self.get_object()

        try:

            requisition.approve(
                request.user,
                request.data.get("comments", ""),
            )

            return Response(
                PurchaseRequisitionSerializer(
                    requisition
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(self, request, pk=None):

        requisition = self.get_object()

        try:

            requisition.reject(
                request.user,
                request.data.get("comments", ""),
            )

            return Response(
                PurchaseRequisitionSerializer(
                    requisition
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PurchaseRequisitionItemViewSet(BaseModelViewSet):

    queryset = PurchaseRequisitionItem.objects.all()
    serializer_class = PurchaseRequisitionItemSerializer


class RequisitionApprovalViewSet(BaseModelViewSet):

    queryset = RequisitionApproval.objects.all()
    serializer_class = RequisitionApprovalSerializer


# ============================================================
# RFQ
# ============================================================

class RFQViewSet(BaseModelViewSet):

    queryset = RFQ.objects.all()
    serializer_class = RFQSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return RFQ.objects.all()

        return RFQ.objects.filter(
            company=user.company
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="publish",
    )
    def publish(self, request, pk=None):

        rfq = self.get_object()

        try:

            rfq.publish()

            return Response(
                RFQSerializer(rfq).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RFQItemViewSet(BaseModelViewSet):

    queryset = RFQItem.objects.all()
    serializer_class = RFQItemSerializer


class RFQVendorViewSet(BaseModelViewSet):

    queryset = RFQVendor.objects.all()
    serializer_class = RFQVendorSerializer


# ============================================================
# QUOTATIONS
# ============================================================

class QuotationViewSet(BaseModelViewSet):

    queryset = Quotation.objects.all()
    serializer_class = QuotationSerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="submit",
    )
    def submit(self, request, pk=None):

        quotation = self.get_object()

        try:

            quotation.submit()

            return Response(
                QuotationSerializer(
                    quotation
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class QuotationItemViewSet(BaseModelViewSet):

    queryset = QuotationItem.objects.all()
    serializer_class = QuotationItemSerializer


class QuotationComparisonViewSet(BaseModelViewSet):

    queryset = QuotationComparison.objects.all()
    serializer_class = QuotationComparisonSerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="complete",
    )
    def complete(self, request, pk=None):

        comparison = self.get_object()

        quotation_id = request.data.get(
            "selected_quotation"
        )

        if not quotation_id:

            return Response(
                {
                    "detail": "selected_quotation is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            quotation = Quotation.objects.get(
                id=quotation_id
            )

            comparison.selected_quotation = quotation

            comparison.complete_comparison()

            return Response(
                QuotationComparisonSerializer(
                    comparison
                ).data
            )

        except (
            Quotation.DoesNotExist
        ):

            return Response(
                {
                    "detail": "Quotation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# PURCHASE ORDERS
# ============================================================

class PurchaseOrderViewSet(BaseModelViewSet):

    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":
            return PurchaseOrder.objects.all()

        return PurchaseOrder.objects.filter(
            company=user.company
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="send",
    )
    def send(self, request, pk=None):

        purchase_order = self.get_object()

        try:

            purchase_order.send()

            return Response(
                PurchaseOrderSerializer(
                    purchase_order
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="acknowledge",
    )
    def acknowledge(self, request, pk=None):

        purchase_order = self.get_object()

        try:

            purchase_order.acknowledge()

            return Response(
                PurchaseOrderSerializer(
                    purchase_order
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):

        purchase_order = self.get_object()

        try:

            purchase_order.cancel()

            return Response(
                PurchaseOrderSerializer(
                    purchase_order
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PurchaseOrderItemViewSet(BaseModelViewSet):

    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer


# ============================================================
# DELIVERY
# ============================================================

class DeliveryViewSet(BaseModelViewSet):

    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="confirm",
    )
    def confirm(self, request, pk=None):

        delivery = self.get_object()

        try:

            delivery.confirm_delivery()

            return Response(
                DeliverySerializer(
                    delivery
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):

        delivery = self.get_object()

        try:

            delivery.cancel()

            return Response(
                DeliverySerializer(
                    delivery
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeliveryItemViewSet(BaseModelViewSet):

    queryset = DeliveryItem.objects.all()
    serializer_class = DeliveryItemSerializer


# ============================================================
# INVOICES
# ============================================================

class InvoiceViewSet(BaseModelViewSet):

    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="submit",
    )
    def submit(self, request, pk=None):

        invoice = self.get_object()

        try:

            invoice.submit_for_review()

            return Response(
                InvoiceSerializer(
                    invoice
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):

        invoice = self.get_object()

        try:

            invoice.approve(
                request.user
            )

            return Response(
                InvoiceSerializer(
                    invoice
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(self, request, pk=None):

        invoice = self.get_object()

        try:

            invoice.reject(
                request.user,
                request.data.get(
                    "rejection_reason",
                    "",
                ),
            )

            return Response(
                InvoiceSerializer(
                    invoice
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @action(
        detail=True,
        methods=["post"],
        url_path="mark-paid",
    )
    def mark_paid(self, request, pk=None):

        invoice = self.get_object()

        try:

            invoice.mark_paid()

            return Response(
                InvoiceSerializer(
                    invoice
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InvoiceItemViewSet(BaseModelViewSet):

    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer


# ============================================================
# PAYMENTS
# ============================================================

class PaymentViewSet(BaseModelViewSet):

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="record",
    )
    def record(self, request, pk=None):

        payment = self.get_object()

        try:

            payment.record_payment()

            return Response(
                PaymentSerializer(
                    payment
                ).data
            )

        except ValueError as e:

            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationViewSet(BaseModelViewSet):

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):

        return Notification.objects.filter(
            recipient=self.request.user
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="read",
    )
    def read(self, request, pk=None):

        notification = self.get_object()

        notification.mark_as_read()

        return Response(
            NotificationSerializer(
                notification
            ).data
        )


    @action(
        detail=True,
        methods=["post"],
        url_path="unread",
    )
    def unread(self, request, pk=None):

        notification = self.get_object()

        notification.mark_as_unread()

        return Response(
            NotificationSerializer(
                notification
            ).data
        )


# ============================================================
# AUDIT LOGS
# ============================================================

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPER_ADMIN":

            return AuditLog.objects.all()

        return AuditLog.objects.filter(
            company=user.company
        )