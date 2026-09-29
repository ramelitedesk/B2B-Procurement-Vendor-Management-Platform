from django.contrib import admin

from .models import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RequisitionApproval,
)


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):

    list_display = (
        "requisition_number",
        "company",
        "requested_by",
        "required_date",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "company",
        "required_date",
        "created_at",
    )

    search_fields = (
        "requisition_number",
        "requested_by__username",
        "requested_by__email",
        "reason",
    )

    ordering = (
        "-created_at",
    )



@admin.register(PurchaseRequisitionItem)
class PurchaseRequisitionItemAdmin(admin.ModelAdmin):

    list_display = (
        "requisition",
        "product",
        "quantity",
        "estimated_unit_price",
        "created_at",
    )

    list_filter = (
        "product",
        "created_at",
    )

    search_fields = (
        "requisition__requisition_number",
        "product__name",
        "product__sku",
    )

    ordering = (
        "-created_at",
    )    



@admin.register(RequisitionApproval)
class RequisitionApprovalAdmin(admin.ModelAdmin):

    list_display = (
        "requisition",
        "approver",
        "action",
        "previous_status",
        "new_status",
        "created_at",
    )

    list_filter = (
        "action",
        "previous_status",
        "new_status",
        "created_at",
    )

    search_fields = (
        "requisition__requisition_number",
        "approver__username",
        "approver__email",
        "comments",
    )

    ordering = (
        "-created_at",
    )    