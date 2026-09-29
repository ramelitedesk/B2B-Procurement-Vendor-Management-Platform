from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User
from vendors.models import Vendor
from products.models import Product
from rfq.models import RFQ


class Quotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.PROTECT,
        related_name="quotations",
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="quotations",
    )

    quotation_number = models.CharField(
        max_length=50,
        unique=True,
    )

    quotation_date = models.DateField()

    valid_until = models.DateField()

    delivery_time = models.PositiveIntegerField(
        help_text="Overall delivery time in days.",
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
        default=0.00,
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rfq", "vendor"],
                name="unique_quotation_per_rfq_vendor",
            )
        ]

    def __str__(self):
        return self.quotation_number

    def clean(self):
        if not self.rfq_id or not self.vendor_id:
            return

        if self.rfq.company_id != self.vendor.company_id:
            raise ValidationError(
                "Vendor must belong to the same company as the RFQ."
            )

        if not self.rfq.vendors.filter(
            vendor_id=self.vendor_id
        ).exists():
            raise ValidationError(
                "This vendor has not been invited to the RFQ."
            )

        if (
            self.status != self.Status.DRAFT
            and self.rfq.status != "PUBLISHED"
        ):
            raise ValidationError(
                "Quotation can only be submitted when the RFQ is published."
            )

        if self.valid_until < self.quotation_date:
            raise ValidationError(
                "Quotation validity date cannot be before quotation date."
            )

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

    def submit(self):
        if self.status != self.Status.DRAFT:
            raise ValueError(
                "Only draft quotations can be submitted."
            )

        if self.rfq.status != "PUBLISHED":
            raise ValueError(
                "Quotation can only be submitted for a published RFQ."
            )

        if not self.items.exists():
            raise ValueError(
                "Quotation must have at least one item before submission."
            )

        self.calculate_totals()

        self.status = self.Status.SUBMITTED

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
            user=None,
            company=self.rfq.company,
            action="SUBMIT",
            description=(
                f"Quotation {self.quotation_number} "
                f"was submitted by vendor {self.vendor.name}."
            ),
            object_type="Quotation",
            object_id=self.id,
            previous_status="DRAFT",
            new_status=self.status,
        )


class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="quotation_items",
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
        default=0.00,
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
    )

    delivery_time = models.PositiveIntegerField(
        help_text="Delivery time for this item in days.",
        default=0,
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
            f"{self.quotation.quotation_number} - "
            f"{self.product.name}"
        )

    def clean(self):
        if not self.quotation_id or not self.product_id:
            return

        if not self.quotation.rfq.items.filter(
            product_id=self.product_id
        ).exists():
            raise ValidationError(
                "This product is not part of the RFQ."
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


class QuotationComparison(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        COMPLETED = "COMPLETED", "Completed"

    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.PROTECT,
        related_name="quotation_comparisons",
    )

    quotations = models.ManyToManyField(
        Quotation,
        related_name="comparisons",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="quotation_comparisons",
    )

    selected_quotation = models.ForeignKey(
        Quotation,
        on_delete=models.PROTECT,
        related_name="selected_comparisons",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
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
        return f"Comparison - {self.rfq.rfq_number}"

    def clean(self):
        if self.selected_quotation_id:
            if self.selected_quotation.rfq_id != self.rfq_id:
                raise ValidationError(
                    "Selected quotation must belong to the same RFQ."
                )

        if self.rfq.status != "PUBLISHED":
            raise ValidationError(
                "Quotation comparison can only be created for a published RFQ."
            )

    def complete_comparison(self, selected_quotation):
        """
        Select the winning quotation and complete the comparison.
        """

        if self.status != self.Status.DRAFT:
            raise ValueError(
                "Only draft comparisons can be completed."
            )

        if selected_quotation.rfq_id != self.rfq_id:
            raise ValueError(
                "Selected quotation must belong to the same RFQ."
            )

        if selected_quotation not in self.quotations.all():
            raise ValueError(
                "Selected quotation must be included in the comparison."
            )

        if selected_quotation.status not in [
            Quotation.Status.SUBMITTED,
            Quotation.Status.UNDER_REVIEW,
        ]:
            raise ValueError(
                "Only submitted or under-review quotations can be selected."
            )

        self.selected_quotation = selected_quotation
        self.status = self.Status.COMPLETED

        self.save(
            update_fields=[
                "selected_quotation",
                "status",
                "updated_at",
            ]
        )

        selected_quotation.status = Quotation.Status.ACCEPTED
        selected_quotation.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=self.created_by,
            company=self.rfq.company,
            action="ACCEPT",
            description=(
                f"Quotation comparison for RFQ "
                f"{self.rfq.rfq_number} was completed. "
                f"Selected quotation: "
                f"{self.selected_quotation.quotation_number}."
            ),
            object_type="QuotationComparison",
            object_id=self.id,
            previous_status="DRAFT",
            new_status=self.status,
        )