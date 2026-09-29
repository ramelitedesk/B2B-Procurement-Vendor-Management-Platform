from django import forms
from django.contrib import admin

from procurement.models import PurchaseRequisition

from .models import RFQ, RFQItem, RFQVendor


class RFQAdminForm(forms.ModelForm):

    class Meta:
        model = RFQ
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only approved purchase requisitions
        # can be selected for an RFQ.
        self.fields["purchase_requisition"].queryset = (
            PurchaseRequisition.objects.filter(
                status=PurchaseRequisition.Status.APPROVED
            )
        )


@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):

    form = RFQAdminForm

    list_display = (
        "rfq_number",
        "title",
        "company",
        "purchase_requisition",
        "created_by",
        "quotation_deadline",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "company",
        "quotation_deadline",
        "created_at",
    )

    search_fields = (
        "rfq_number",
        "title",
        "description",
        "purchase_requisition__requisition_number",
        "company__name",
    )

    ordering = ("-created_at",)

    actions = ("publish_rfqs",)

    @admin.action(description="Publish selected RFQs")
    def publish_rfqs(self, request, queryset):
        published_count = 0
        failed_count = 0

        for rfq in queryset:
            try:
                rfq.publish()
                published_count += 1

            except ValueError:
                failed_count += 1

        if published_count:
            self.message_user(
                request,
                f"{published_count} RFQ(s) published successfully.",
            )

        if failed_count:
            self.message_user(
                request,
                (
                    f"{failed_count} RFQ(s) could not be published. "
                    "Make sure each RFQ is Draft, has at least one item, "
                    "and has at least one vendor."
                ),
                level="warning",
            )

    def save_model(self, request, obj, form, change):
        is_new = not obj.pk

        # Automatically record the Admin user
        # who created the RFQ.
        if not change:
            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        # Automatically copy Purchase Requisition items
        # into RFQ Items when creating a new RFQ.
        if is_new:
            requisition_items = obj.purchase_requisition.items.all()

            for requisition_item in requisition_items:
                RFQItem.objects.create(
                    rfq=obj,
                    product=requisition_item.product,
                    quantity=requisition_item.quantity,
                    remarks=requisition_item.remarks,
                )


@admin.register(RFQItem)
class RFQItemAdmin(admin.ModelAdmin):

    list_display = (
        "rfq",
        "product",
        "quantity",
        "created_at",
    )

    list_filter = (
        "rfq",
        "product",
        "created_at",
    )

    search_fields = (
        "rfq__rfq_number",
        "product__name",
        "product__sku",
    )

    ordering = (
        "-created_at",
    )


@admin.register(RFQVendor)
class RFQVendorAdmin(admin.ModelAdmin):

    list_display = (
        "rfq",
        "vendor",
        "status",
        "invited_at",
    )

    list_filter = (
        "status",
        "vendor",
        "invited_at",
    )

    search_fields = (
        "rfq__rfq_number",
        "vendor__name",
    )

    ordering = (
        "-invited_at",
    )

    def save_model(self, request, obj, form, change):
        # Every newly added vendor invitation
        # starts with INVITED status.
        if not change:
            obj.status = RFQVendor.Status.INVITED

        super().save_model(
            request,
            obj,
            form,
            change,
        )