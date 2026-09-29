from django.db import models

from companies.models import Company
from accounts.models import User
from vendors.models import Vendor
from products.models import Product
from procurement.models import PurchaseRequisition


class RFQ(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="rfqs",
    )

    purchase_requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.PROTECT,
        related_name="rfqs",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_rfqs",
    )

    rfq_number = models.CharField(
        max_length=50,
        unique=True,
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    quotation_deadline = models.DateTimeField()

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

    def __str__(self):
        return self.rfq_number

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.purchase_requisition.status
            != PurchaseRequisition.Status.APPROVED
        ):
            raise ValidationError(
                "RFQ can only be created from an approved purchase requisition."
            )

        if self.company_id != self.purchase_requisition.company_id:
            raise ValidationError(
                "RFQ company must match the purchase requisition company."
            )

    @classmethod
    def create_from_requisition(
        cls,
        purchase_requisition,
        created_by,
        rfq_number,
        title,
        quotation_deadline,
        description="",
    ):
        if (
            purchase_requisition.status
            != PurchaseRequisition.Status.APPROVED
        ):
            raise ValueError(
                "RFQ can only be created from an approved purchase requisition."
            )

        rfq = cls.objects.create(
            company=purchase_requisition.company,
            purchase_requisition=purchase_requisition,
            created_by=created_by,
            rfq_number=rfq_number,
            title=title,
            description=description,
            quotation_deadline=quotation_deadline,
            status=cls.Status.DRAFT,
        )

        for requisition_item in purchase_requisition.items.all():
            RFQItem.objects.create(
                rfq=rfq,
                product=requisition_item.product,
                quantity=requisition_item.quantity,
                remarks=requisition_item.remarks,
            )

        return rfq

    def publish(self):
        """
        Publish the RFQ.

        An RFQ can only be published when:
        - Its current status is DRAFT
        - It has at least one item
        - It has at least one invited vendor
        """

        if self.status != self.Status.DRAFT:
            raise ValueError(
                "Only draft RFQs can be published."
            )

        if not self.items.exists():
            raise ValueError(
                "RFQ must have at least one item before publishing."
            )

        if not self.vendors.exists():
            raise ValueError(
                "RFQ must have at least one vendor before publishing."
            )

        previous_status = self.status

        self.status = self.Status.PUBLISHED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=self.created_by,
            company=self.company,
            action="PUBLISH",
            description=(
                f"RFQ {self.rfq_number} was published."
            ),
            object_type="RFQ",
            object_id=self.id,
            previous_status=previous_status,
            new_status=self.status,
        )


class RFQItem(models.Model):

    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="rfq_items",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
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
            f"{self.rfq.rfq_number} - "
            f"{self.product.name}"
        )


class RFQVendor(models.Model):

    class Status(models.TextChoices):
        INVITED = "INVITED", "Invited"
        RESPONDED = "RESPONDED", "Responded"
        DECLINED = "DECLINED", "Declined"

    rfq = models.ForeignKey(
        RFQ,
        on_delete=models.CASCADE,
        related_name="vendors",
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="rfq_invitations",
    )

    invited_at = models.DateTimeField(
        auto_now_add=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INVITED,
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "rfq",
                    "vendor",
                ],
                name="unique_rfq_vendor",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.rfq.company_id != self.vendor.company_id:
            raise ValidationError(
                "Vendor must belong to the same company as the RFQ."
            )

    def __str__(self):
        return (
            f"{self.rfq.rfq_number} - "
            f"{self.vendor.name}"
        )