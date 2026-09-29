from django.db import models

from accounts.models import User
from companies.models import Company
from products.models import Product


class PurchaseRequisition(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="purchase_requisitions",
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="purchase_requisitions",
    )

    requisition_number = models.CharField(
        max_length=50,
        unique=True,
    )

    required_date = models.DateField()

    reason = models.TextField()

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
        return self.requisition_number

    def submit_for_approval(self):
        if self.status != self.Status.DRAFT:
            raise ValueError(
                "Only draft requisitions can be submitted for approval."
            )

        previous_status = self.status

        self.status = self.Status.PENDING_APPROVAL

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=self.requested_by,
            company=self.company,
            action="SUBMIT",
            description=(
                f"Purchase requisition "
                f"{self.requisition_number} was submitted "
                f"for approval."
            ),
            object_type="PurchaseRequisition",
            object_id=self.id,
            previous_status=previous_status,
            new_status=self.status,
        )

    def approve(self, approver, comments=""):

        # Check approver role
        if approver.role != User.Role.PROCUREMENT_MANAGER:
            raise PermissionError(
                "Only Procurement Managers can approve requisitions."
            )

        # Check company
        if approver.company_id != self.company_id:
            raise PermissionError(
                "You cannot approve a requisition from another company."
            )

        # Check requisition status
        if self.status != self.Status.PENDING_APPROVAL:
            raise ValueError(
                "Only requisitions pending approval can be approved."
            )

        previous_status = self.status

        self.status = self.Status.APPROVED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # Create approval history
        RequisitionApproval.objects.create(
            requisition=self,
            approver=approver,
            action=RequisitionApproval.Action.APPROVED,
            comments=comments,
            previous_status=previous_status,
            new_status=self.status,
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=approver,
            company=self.company,
            action="APPROVE",
            description=(
                f"Purchase requisition "
                f"{self.requisition_number} was approved."
            ),
            object_type="PurchaseRequisition",
            object_id=self.id,
            previous_status=previous_status,
            new_status=self.status,
        )

    def reject(self, approver, comments=""):

        # Check approver role
        if approver.role != User.Role.PROCUREMENT_MANAGER:
            raise PermissionError(
                "Only Procurement Managers can reject requisitions."
            )

        # Check company
        if approver.company_id != self.company_id:
            raise PermissionError(
                "You cannot reject a requisition from another company."
            )

        # Check requisition status
        if self.status != self.Status.PENDING_APPROVAL:
            raise ValueError(
                "Only requisitions pending approval can be rejected."
            )

        previous_status = self.status

        self.status = self.Status.REJECTED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # Create rejection history
        RequisitionApproval.objects.create(
            requisition=self,
            approver=approver,
            action=RequisitionApproval.Action.REJECTED,
            comments=comments,
            previous_status=previous_status,
            new_status=self.status,
        )

        from audit_logs.services import create_audit_log

        create_audit_log(
            user=approver,
            company=self.company,
            action="REJECT",
            description=(
                f"Purchase requisition "
                f"{self.requisition_number} was rejected."
            ),
            object_type="PurchaseRequisition",
            object_id=self.id,
            previous_status=previous_status,
            new_status=self.status,
        )


class PurchaseRequisitionItem(models.Model):

    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="requisition_items",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    estimated_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
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
            f"{self.requisition.requisition_number} - "
            f"{self.product.name}"
        )


class RequisitionApproval(models.Model):

    class Action(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name="approvals",
    )

    approver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="requisition_approvals",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )

    comments = models.TextField(
        blank=True,
        null=True,
    )

    previous_status = models.CharField(
        max_length=30,
    )

    new_status = models.CharField(
        max_length=30,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.requisition.requisition_number} - "
            f"{self.action}"
        )