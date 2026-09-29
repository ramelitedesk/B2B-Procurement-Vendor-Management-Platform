from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from accounts.models import User
from companies.models import Company
from vendors.models import Vendor
from invoices.models import Invoice


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        NEFT = "NEFT", "NEFT"
        RTGS = "RTGS", "RTGS"
        IMPS = "IMPS", "IMPS"
        UPI = "UPI", "UPI"
        CHEQUE = "CHEQUE", "Cheque"
        CASH = "CASH", "Cash"
        OTHER = "OTHER", "Other"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="recorded_payments",
    )

    payment_number = models.CharField(
        max_length=50,
        unique=True,
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    notes = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.payment_number

    # ============================================================
    # VALIDATION
    # ============================================================

    def clean(self):

        if not self.invoice_id:
            return

        invoice = self.invoice

        # Payment can only be made against approved or paid invoices
        if invoice.status not in [
            Invoice.Status.APPROVED,
            Invoice.Status.PAID,
        ]:
            raise ValidationError(
                "Payment can only be recorded for an approved invoice."
            )

        # Automatically validate vendor
        if self.vendor_id and self.vendor_id != invoice.vendor_id:
            raise ValidationError(
                "Payment vendor must match the Invoice vendor."
            )

        # Automatically validate company
        if self.company_id and self.company_id != invoice.purchase_order.company_id:
            raise ValidationError(
                "Payment company must match the Purchase Order company."
            )

        if self.amount is not None and self.amount <= Decimal("0.00"):
            raise ValidationError(
                "Payment amount must be greater than zero."
            )

    # ============================================================
    # TOTAL PAYMENTS AGAINST INVOICE
    # ============================================================

    def get_previous_paid_amount(self):

        total = Payment.objects.filter(
            invoice=self.invoice,
            status__in=[
                Payment.Status.PENDING,
                Payment.Status.PARTIALLY_PAID,
                Payment.Status.PAID,
            ],
        ).exclude(
            pk=self.pk
        ).aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")

    # ============================================================
    # REMAINING INVOICE AMOUNT
    # ============================================================

    def get_remaining_amount(self):

        previous_paid = self.get_previous_paid_amount()

        remaining = (
            self.invoice.total_amount
            - previous_paid
        )

        return max(
            remaining,
            Decimal("0.00"),
        )

    # ============================================================
    # RECORD PAYMENT
    # ============================================================

    def record_payment(self):

        if self.status == self.Status.CANCELLED:
            raise ValueError(
                "Cancelled payments cannot be processed."
            )

        if self.amount <= Decimal("0.00"):
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        remaining_amount = self.get_remaining_amount()

        if self.amount > remaining_amount:
            raise ValueError(
                f"Payment amount ({self.amount}) cannot exceed "
                f"remaining invoice amount ({remaining_amount})."
            )
        previous_status = self.status
        new_total_paid = (
            self.get_previous_paid_amount()
            + self.amount
        )

        invoice_total = self.invoice.total_amount

        if new_total_paid >= invoice_total:

            self.status = self.Status.PAID

            self.invoice.status = Invoice.Status.PAID

            self.invoice.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        else:

            self.status = self.Status.PARTIALLY_PAID

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


        from audit_logs.services import create_audit_log

        create_audit_log(
            user=self.recorded_by,
            company=self.company,
            action="PAYMENT",
            description=(
                f"Payment {self.payment_number} "
                f"of ₹{self.amount} was recorded "
                f"against invoice {self.invoice.invoice_number}."
            ),
            object_type="Payment",
            object_id=self.id,
            previous_status=previous_status,
            new_status=self.status,
        )

    # ============================================================
    # CANCEL PAYMENT
    # ============================================================

    def cancel(self):

        if self.status == self.Status.CANCELLED:
            raise ValueError(
                "Payment is already cancelled."
            )

        if self.status == self.Status.PAID:
            raise ValueError(
                "Completed payments cannot be cancelled."
            )

        self.status = self.Status.CANCELLED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )