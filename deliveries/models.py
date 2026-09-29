from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from accounts.models import User
from vendors.models import Vendor
from purchase_orders.models import PurchaseOrder, PurchaseOrderItem


class Delivery(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED", "Partially Delivered"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name="deliveries",
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="deliveries",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_deliveries",
    )

    delivery_number = models.CharField(
        max_length=50,
        unique=True,
    )

    shipment_date = models.DateField()

    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
    )

    actual_delivery_date = models.DateField(
        blank=True,
        null=True,
    )

    courier_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    notes = models.TextField(
        blank=True,
        null=True,
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
        return self.delivery_number

    def clean(self):
        if not self.purchase_order_id:
            return

        purchase_order = self.purchase_order

        # Delivery must belong to the same vendor as the PO
        if self.vendor_id and self.vendor_id != purchase_order.vendor_id:
            raise ValidationError(
                "Delivery vendor must match the Purchase Order vendor."
            )

        # Delivery can only be created for active PO states
        if purchase_order.status in [
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.SENT,
            PurchaseOrder.Status.CANCELLED,
            PurchaseOrder.Status.CLOSED,
        ]:
            raise ValidationError(
                "Delivery can only be created for an acknowledged or partially delivered Purchase Order."
            )

        # A fully delivered PO cannot receive another delivery
        if (
            purchase_order.status == PurchaseOrder.Status.DELIVERED
            and self.status == self.Status.DRAFT
        ):
            raise ValidationError(
                "This Purchase Order has already been fully delivered."
            )

    @classmethod
    def create_for_purchase_order(
        cls,
        purchase_order,
        created_by,
        delivery_number,
        shipment_date,
        expected_delivery_date=None,
        courier_name="",
        tracking_number="",
        notes="",
    ):
        if purchase_order.status not in [
            PurchaseOrder.Status.ACKNOWLEDGED,
            PurchaseOrder.Status.PARTIALLY_DELIVERED,
        ]:
            raise ValueError(
                "Delivery can only be created for an acknowledged or partially delivered Purchase Order."
            )

        if purchase_order.status == PurchaseOrder.Status.DELIVERED:
            raise ValueError(
                "This Purchase Order has already been fully delivered."
            )

        delivery = cls.objects.create(
            purchase_order=purchase_order,
            vendor=purchase_order.vendor,
            created_by=created_by,
            delivery_number=delivery_number,
            shipment_date=shipment_date,
            expected_delivery_date=expected_delivery_date,
            courier_name=courier_name,
            tracking_number=tracking_number,
            notes=notes,
            status=cls.Status.DRAFT,
        )

        # Automatically copy PO items
        for po_item in purchase_order.items.all():

            DeliveryItem.objects.create(
                delivery=delivery,
                purchase_order_item=po_item,
                ordered_quantity=po_item.quantity,
                delivered_quantity=Decimal("0.00"),
            )

        return delivery

    def calculate_delivery_status(self):
        """
        Determine whether this delivery is:
        - Partial
        - Fully delivered
        """

        total_ordered = Decimal("0.00")
        total_delivered = Decimal("0.00")

        for item in self.items.all():

            total_ordered += item.ordered_quantity
            total_delivered += item.delivered_quantity

        if total_delivered <= 0:
            return self.Status.IN_TRANSIT

        if total_delivered < total_ordered:
            return self.Status.PARTIALLY_DELIVERED

        return self.Status.DELIVERED

    def confirm_delivery(self, actual_delivery_date=None):

        if self.status == self.Status.CANCELLED:
            raise ValueError(
                "Cancelled deliveries cannot be confirmed."
            )

        if self.status in [
            self.Status.PARTIALLY_DELIVERED,
            self.Status.DELIVERED,
        ]:
            raise ValueError(
                "This delivery has already been confirmed."
            )

        if not self.items.exists():
            raise ValueError(
                "Delivery must contain at least one item."
            )

        # Validate all delivered quantities
        for item in self.items.all():
            item.validate_delivery_quantity()

        delivery_status = self.calculate_delivery_status()

        if delivery_status == self.Status.IN_TRANSIT:
            raise ValueError(
                "At least one quantity must be delivered before confirming the delivery."
            )

        self.status = delivery_status

        if actual_delivery_date:
            self.actual_delivery_date = actual_delivery_date

        self.save(
            update_fields=[
                "status",
                "actual_delivery_date",
                "updated_at",
            ]
        )

        # Update Purchase Order status
        self.purchase_order.update_delivery_status()


        from audit_logs.services import create_audit_log

        create_audit_log(
            user=self.created_by,
            company=self.purchase_order.company,
            action="CONFIRM",
            description=(
                f"Delivery {self.delivery_number} "
                f"was confirmed for purchase order "
                f"{self.purchase_order.po_number}."
            ),
            object_type="Delivery",
            object_id=self.id,
            previous_status=self.status,
            new_status=self.status,
        )

    def cancel(self):

        if self.status in [
            self.Status.PARTIALLY_DELIVERED,
            self.Status.DELIVERED,
        ]:
            raise ValueError(
                "A confirmed delivery cannot be cancelled."
            )

        self.status = self.Status.CANCELLED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


class DeliveryItem(models.Model):

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name="items",
    )

    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name="delivery_items",
    )

    ordered_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    delivered_quantity = models.DecimalField(
        max_digits=12,
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
            f"{self.delivery.delivery_number} - "
            f"{self.purchase_order_item.product.name}"
        )

    def clean(self):

        if not self.delivery_id or not self.purchase_order_item_id:
            return

        # Delivery item must belong to the same PO
        if (
            self.purchase_order_item.purchase_order_id
            != self.delivery.purchase_order_id
        ):
            raise ValidationError(
                "Delivery item must belong to the same Purchase Order."
            )

        # Ordered quantity must match PO item quantity
        if self.ordered_quantity != self.purchase_order_item.quantity:
            raise ValidationError(
                "Ordered quantity must match the Purchase Order item quantity."
            )

        if self.delivered_quantity < 0:
            raise ValidationError(
                "Delivered quantity cannot be negative."
            )

    def get_previous_delivered_quantity(self):

        previous_quantity = (
            DeliveryItem.objects.filter(
                purchase_order_item=self.purchase_order_item,
                delivery__status__in=[
                    Delivery.Status.PARTIALLY_DELIVERED,
                    Delivery.Status.DELIVERED,
                ],
            )
            .exclude(pk=self.pk)
            .aggregate(
                total=Sum("delivered_quantity")
            )["total"]
        )

        return previous_quantity or Decimal("0.00")

    def get_remaining_quantity(self):

        total_delivered = (
            DeliveryItem.objects.filter(
                purchase_order_item=self.purchase_order_item,
                delivery__status__in=[
                    Delivery.Status.PARTIALLY_DELIVERED,
                    Delivery.Status.DELIVERED,
                ],
            )
            .aggregate(
                total=Sum("delivered_quantity")
            )["total"]
        )

        total_delivered = total_delivered or Decimal("0.00")

        remaining_quantity = (
            self.purchase_order_item.quantity
            - total_delivered
        )

        return max(
            remaining_quantity,
            Decimal("0.00"),
        )

    def validate_delivery_quantity(self):

        if self.delivered_quantity < 0:
            raise ValidationError(
                "Delivered quantity cannot be negative."
            )

        remaining_quantity = self.get_remaining_quantity()

        if self.delivered_quantity > remaining_quantity:
            raise ValidationError(
                (
                    f"Delivered quantity ({self.delivered_quantity}) "
                    f"cannot exceed remaining quantity "
                    f"({remaining_quantity})."
                )
            )

    def save(self, *args, **kwargs):

        self.validate_delivery_quantity()

        super().save(*args, **kwargs)