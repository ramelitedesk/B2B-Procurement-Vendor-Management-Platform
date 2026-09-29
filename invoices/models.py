from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from accounts.models import User
from vendors.models import Vendor
from products.models import Product
from purchase_orders.models import PurchaseOrder, PurchaseOrderItem
from deliveries.models import Delivery


class Invoice(models.Model):

    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        PAID = "PAID", "Paid"

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="uploaded_invoices",
    )

    invoice_number = models.CharField(
        max_length=100,
        unique=True,
    )

    invoice_date = models.DateField()

    due_date = models.DateField()

    invoice_file = models.FileField(
        upload_to="invoices/",
        blank=True,
        null=True,
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    notes = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True,
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="reviewed_invoices",
        blank=True,
        null=True,
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.invoice_number

    def clean(self):

        if not self.purchase_order_id:
            return

        purchase_order = self.purchase_order

        # Invoice vendor must match PO vendor
        if self.vendor_id and self.vendor_id != purchase_order.vendor_id:
            raise ValidationError(
                "Invoice vendor must match the Purchase Order vendor."
            )

        # Invoice should only be created after PO delivery
        if purchase_order.status not in [
            PurchaseOrder.Status.PARTIALLY_DELIVERED,
            PurchaseOrder.Status.DELIVERED,
            PurchaseOrder.Status.CLOSED,
        ]:
            raise ValidationError(
                "Invoice can only be created for a delivered or closed Purchase Order."
            )

        # Due date cannot be before invoice date
        if self.invoice_date and self.due_date:
            if self.due_date < self.invoice_date:
                raise ValidationError(
                    "Invoice due date cannot be before invoice date."
                )

    @classmethod
    def create_for_purchase_order(
        cls,
        purchase_order,
        uploaded_by,
        invoice_number,
        invoice_date,
        due_date,
        invoice_file=None,
        notes="",
    ):

        if purchase_order.status not in [
            PurchaseOrder.Status.PARTIALLY_DELIVERED,
            PurchaseOrder.Status.DELIVERED,
            PurchaseOrder.Status.CLOSED,
        ]:
            raise ValueError(
                "Invoice can only be created for a delivered or closed Purchase Order."
            )

        invoice = cls.objects.create(
            purchase_order=purchase_order,
            vendor=purchase_order.vendor,
            uploaded_by=uploaded_by,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            invoice_file=invoice_file,
            notes=notes,
            status=cls.Status.UPLOADED,
        )

        # Copy PO items into invoice.
        # Quantity starts at zero so the user can invoice
        # only the quantity actually being billed.
        for po_item in purchase_order.items.all():

            InvoiceItem.objects.create(
                invoice=invoice,
                purchase_order_item=po_item,
                product=po_item.product,
                quantity=Decimal("0.00"),
                unit_price=po_item.unit_price,
                tax_rate=po_item.tax_rate,
            )

        return invoice

    def calculate_totals(self):

        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item in self.items.all():

            item.calculate_amounts()

            item.save(
                update_fields=[
                    "tax_amount",
                    "total_amount",
                    "updated_at",
                ]
            )

            subtotal += item.quantity * item.unit_price
            tax_amount += item.tax_amount

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total_amount = subtotal + tax_amount

        return (
            self.subtotal,
            self.tax_amount,
            self.total_amount,
        )

    def get_previously_invoiced_amount(self):

        amount = (
            Invoice.objects.filter(
                purchase_order=self.purchase_order,
                status__in=[
                    self.Status.UPLOADED,
                    self.Status.UNDER_REVIEW,
                    self.Status.APPROVED,
                    self.Status.PAID,
                ],
            )
            .exclude(pk=self.pk)
            .aggregate(
                total=Sum("total_amount")
            )["total"]
        )

        return amount or Decimal("0.00")

    def get_remaining_po_amount(self):

        remaining = (
            self.purchase_order.total_amount
            - self.get_previously_invoiced_amount()
        )

        return max(
            remaining,
            Decimal("0.00"),
        )

    def submit_for_review(self):

        if self.status != self.Status.UPLOADED:
            raise ValueError(
                "Only uploaded invoices can be submitted for review."
            )

        if not self.items.exists():
            raise ValueError(
                "Invoice must contain at least one item."
            )

        self.calculate_totals()

        if self.total_amount <= Decimal("0.00"):
            raise ValueError(
                "Invoice total must be greater than zero."
            )

        remaining_po_amount = self.get_remaining_po_amount()

        if self.total_amount > remaining_po_amount:
            raise ValueError(
                (
                    f"Invoice total ({self.total_amount}) cannot exceed "
                    f"remaining PO amount ({remaining_po_amount})."
                )
            )

        self.status = self.Status.UNDER_REVIEW

        self.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "status",
                "updated_at",
            ]
        )


        from audit_logs.services import create_audit_log

        create_audit_log(
            user=self.uploaded_by,
            company=self.purchase_order.company,
            action="SUBMIT",
            description=(
                f"Invoice {self.invoice_number} "
                f"was submitted for review."
            ),
            object_type="Invoice",
            object_id=self.id,
            previous_status="UPLOADED",
            new_status=self.status,
        )

    def approve(self, reviewer):

        if self.status != self.Status.UNDER_REVIEW:
            raise ValueError(
                "Only invoices under review can be approved."
            )

        if reviewer.company_id != self.purchase_order.company_id:
            raise ValueError(
                "Reviewer must belong to the same company as the Purchase Order."
            )

        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer

        from django.utils import timezone

        self.reviewed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=reviewer,
            company=self.purchase_order.company,
            action="APPROVE",
            description=(
                f"Invoice {self.invoice_number} "
                f"was approved."
            ),
            object_type="Invoice",
            object_id=self.id,
            previous_status="UNDER_REVIEW",
            new_status=self.status,
        )

    def reject(self, reviewer, reason=""):

        if self.status != self.Status.UNDER_REVIEW:
            raise ValueError(
                "Only invoices under review can be rejected."
            )

        if reviewer.company_id != self.purchase_order.company_id:
            raise ValueError(
                "Reviewer must belong to the same company as the Purchase Order."
            )

        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.rejection_reason = reason

        from django.utils import timezone

        self.reviewed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "updated_at",
            ]
        )


        from audit_logs.services import create_audit_log

        create_audit_log(
            user=reviewer,
            company=self.purchase_order.company,
            action="REJECT",
            description=(
                f"Invoice {self.invoice_number} "
                f"was rejected."
            ),
            object_type="Invoice",
            object_id=self.id,
            previous_status="UNDER_REVIEW",
            new_status=self.status,
        )

    def mark_paid(self):

        if self.status != self.Status.APPROVED:
            raise ValueError(
                "Only approved invoices can be marked as paid."
            )
        previous_status = self.status
        self.status = self.Status.PAID

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


        from audit_logs.services import create_audit_log

        create_audit_log(
            user=None,
            company=self.purchase_order.company,
            action="PAYMENT",
            description=(
                f"Invoice {self.invoice_number} "
                f"was marked as paid."
            ),
            object_type="Invoice",
            object_id=self.id,
            previous_status=previous_status,
            new_status=self.status,
        )


class InvoiceItem(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name="invoice_items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="invoice_items",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        return (
            f"{self.invoice.invoice_number} - "
            f"{self.product.name}"
        )

    def get_total_delivered_quantity(self):

        total = (
            Delivery.objects.filter(
                purchase_order=self.invoice.purchase_order,
                status__in=[
                    Delivery.Status.PARTIALLY_DELIVERED,
                    Delivery.Status.DELIVERED,
                ],
                items__purchase_order_item=self.purchase_order_item,
            )
            .aggregate(
                total=Sum(
                    "items__delivered_quantity"
                )
            )["total"]
        )

        return total or Decimal("0.00")

    def get_previously_invoiced_quantity(self):

        total = (
            InvoiceItem.objects.filter(
                purchase_order_item=self.purchase_order_item,
                invoice__status__in=[
                    Invoice.Status.UPLOADED,
                    Invoice.Status.UNDER_REVIEW,
                    Invoice.Status.APPROVED,
                    Invoice.Status.PAID,
                ],
            )
            .exclude(
                invoice=self.invoice
            )
            .aggregate(
                total=Sum("quantity")
            )["total"]
        )

        return total or Decimal("0.00")

    def get_remaining_invoiceable_quantity(self):

        delivered_quantity = (
            self.get_total_delivered_quantity()
        )

        previously_invoiced = (
            self.get_previously_invoiced_quantity()
        )

        remaining = (
            delivered_quantity
            - previously_invoiced
        )

        return max(
            remaining,
            Decimal("0.00"),
        )

    def clean(self):

        if not self.invoice_id or not self.purchase_order_item_id:
            return

        # Invoice item must belong to the same PO
        if (
            self.purchase_order_item.purchase_order_id
            != self.invoice.purchase_order_id
        ):
            raise ValidationError(
                "Invoice item must belong to the same Purchase Order."
            )

        # Product must match PO item
        if (
            self.product_id
            != self.purchase_order_item.product_id
        ):
            raise ValidationError(
                "Invoice product must match the Purchase Order item."
            )

        if self.quantity < 0:
            raise ValidationError(
                "Invoice quantity cannot be negative."
            )

        remaining_quantity = (
            self.get_remaining_invoiceable_quantity()
        )

        if self.quantity > remaining_quantity:
            raise ValidationError(
                (
                    f"Invoice quantity ({self.quantity}) cannot exceed "
                    f"remaining invoiceable quantity "
                    f"({remaining_quantity})."
                )
            )

    def calculate_amounts(self):

        base_amount = (
            self.quantity * self.unit_price
        )

        self.tax_amount = (
            base_amount
            * self.tax_rate
            / Decimal("100")
        )

        self.total_amount = (
            base_amount
            + self.tax_amount
        )

        return (
            self.tax_amount,
            self.total_amount,
        )

    def save(self, *args, **kwargs):

        self.calculate_amounts()

        super().save(*args, **kwargs)