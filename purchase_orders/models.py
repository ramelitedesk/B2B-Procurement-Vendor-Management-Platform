from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from accounts.models import User
from companies.models import Company
from vendors.models import Vendor
from products.models import Product
from quotations.models import Quotation


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED", "Partially Delivered"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        CLOSED = "CLOSED", "Closed"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    quotation = models.OneToOneField(
        Quotation,
        on_delete=models.PROTECT,
        related_name="purchase_order",
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_purchase_orders",
    )

    po_number = models.CharField(
        max_length=50,
        unique=True,
    )

    po_date = models.DateField()

    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
    )

    payment_terms = models.TextField(
        blank=True,
        null=True,
    )

    notes = models.TextField(
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

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.po_number

    def clean(self):
        if not self.quotation_id:
            return

        # Purchase Order must come from an accepted quotation.
        if self.quotation.status != Quotation.Status.ACCEPTED:
            raise ValidationError(
                "Purchase Order can only be created from an accepted quotation."
            )

        # Company must match quotation RFQ company.
        if self.company_id != self.quotation.rfq.company_id:
            raise ValidationError(
                "Purchase Order company must match the quotation company."
            )

        # Vendor must match quotation vendor.
        if self.vendor_id != self.quotation.vendor_id:
            raise ValidationError(
                "Purchase Order vendor must match the quotation vendor."
            )

    @classmethod
    def create_from_quotation(
        cls,
        quotation,
        created_by,
        po_number,
        po_date,
        expected_delivery_date=None,
        payment_terms="",
        notes="",
    ):
        """
        Create a Purchase Order from an accepted quotation
        and copy all quotation items.
        """

        if quotation.status != Quotation.Status.ACCEPTED:
            raise ValueError(
                "Purchase Order can only be created from an accepted quotation."
            )

        if hasattr(quotation, "purchase_order"):
            raise ValueError(
                "A Purchase Order already exists for this quotation."
            )

        purchase_order = cls.objects.create(
            company=quotation.rfq.company,
            quotation=quotation,
            vendor=quotation.vendor,
            created_by=created_by,
            po_number=po_number,
            po_date=po_date,
            expected_delivery_date=expected_delivery_date,
            payment_terms=payment_terms or quotation.payment_terms,
            notes=notes,
            subtotal=quotation.subtotal,
            tax_amount=quotation.tax_amount,
            total_amount=quotation.total_amount,
            status=cls.Status.DRAFT,
        )

        for quotation_item in quotation.items.all():
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product=quotation_item.product,
                quantity=quotation_item.quantity,
                unit_price=quotation_item.unit_price,
                tax_rate=quotation_item.tax_rate,
                tax_amount=quotation_item.tax_amount,
                total_amount=quotation_item.total_amount,
                delivery_time=quotation_item.delivery_time,
                remarks=quotation_item.remarks,
            )

        return purchase_order

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

    def send(self):
        """
        Send the Purchase Order to the vendor.
        """

        if self.status != self.Status.DRAFT:
            raise ValueError(
                "Only draft Purchase Orders can be sent."
            )

        if not self.items.exists():
            raise ValueError(
                "Purchase Order must have at least one item."
            )

        self.calculate_totals()

        self.status = self.Status.SENT

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
            user=self.created_by,
            company=self.company,
            action="SEND",
            description=(
                f"Purchase order {self.po_number} "
                f"was sent to vendor {self.vendor.name}."
            ),
            object_type="PurchaseOrder",
            object_id=self.id,
            previous_status="DRAFT",
            new_status=self.status,
        )

    def acknowledge(self):
        """
        Vendor acknowledges the Purchase Order.
        """

        if self.status != self.Status.SENT:
            raise ValueError(
                "Only sent Purchase Orders can be acknowledged."
            )

        self.status = self.Status.ACKNOWLEDGED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=None,
            company=self.company,
            action="ACKNOWLEDGE",
            description=(
                f"Purchase order {self.po_number} "
                f"was acknowledged by vendor {self.vendor.name}."
            ),
            object_type="PurchaseOrder",
            object_id=self.id,
            previous_status="SENT",
            new_status=self.status,
        )

    def update_delivery_status(self):
        """
        Automatically update Purchase Order status
        based on confirmed delivery quantities.
        """

        if self.status in [
        self.Status.CANCELLED,
        self.Status.CLOSED,
        ]:
            return

        total_ordered = Decimal("0.00")
        total_delivered = Decimal("0.00")

        for item in self.items.all():

            total_ordered += item.quantity

            delivered = (
                item.delivery_items.filter(
                    delivery__status__in=[
                        "PARTIALLY_DELIVERED",
                        "DELIVERED",
                    ]
                ).aggregate(
                    total=Sum("delivered_quantity")
                )["total"]
            )

            total_delivered += delivered or Decimal("0.00")

        if total_delivered <= Decimal("0.00"):
            new_status = self.Status.ACKNOWLEDGED

        elif total_delivered < total_ordered:
            new_status = self.Status.PARTIALLY_DELIVERED

        else:
            new_status = self.Status.DELIVERED

        if self.status != new_status:

           self.status = new_status

           self.save(
                update_fields=[
                "status",
                "updated_at",
            ]
        )   

    def cancel(self):
        """
        Cancel the Purchase Order.
        """

        if self.status in [
            self.Status.DELIVERED,
            self.Status.CLOSED,
        ]:
            raise ValueError(
                "Delivered or closed Purchase Orders cannot be cancelled."
            )

        self.status = self.Status.CANCELLED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
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

    delivery_time = models.PositiveIntegerField(
        default=0,
        help_text="Delivery time for this item in days.",
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
            f"{self.purchase_order.po_number} - "
            f"{self.product.name}"
        )

    def clean(self):
        if not self.purchase_order_id or not self.product_id:
            return

        if not self.purchase_order.quotation.items.filter(
            product_id=self.product_id
        ).exists():
            raise ValidationError(
                "This product is not part of the original quotation."
            )

    def calculate_amounts(self):
        base_amount = self.quantity * self.unit_price

        self.tax_amount = (
            base_amount * self.tax_rate / Decimal("100")
        )

        self.total_amount = (
            base_amount + self.tax_amount
        )

        return (
            self.tax_amount,
            self.total_amount,
        )