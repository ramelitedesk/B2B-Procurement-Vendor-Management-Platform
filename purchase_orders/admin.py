from django import forms
from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem
from quotations.models import Quotation


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0

    fields = (
        "product",
        "quantity",
        "unit_price",
        "tax_rate",
        "tax_amount",
        "total_amount",
        "delivery_time",
        "remarks",
    )

    readonly_fields = (
        "tax_amount",
        "total_amount",
    )


class PurchaseOrderAdminForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrder
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["quotation"].queryset = (
            Quotation.objects.filter(
                status=Quotation.Status.ACCEPTED
            )
            .select_related("rfq", "vendor")
        )

    def clean(self):
        cleaned_data = super().clean()

        quotation = cleaned_data.get("quotation")

        if quotation:
            # Automatically set company and vendor
            self.instance.company = quotation.rfq.company
            self.instance.vendor = quotation.vendor

            cleaned_data["company"] = quotation.rfq.company
            cleaned_data["vendor"] = quotation.vendor

        return cleaned_data


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):

    form = PurchaseOrderAdminForm

    list_display = (
        "po_number",
        "quotation",
        "vendor",
        "company",
        "po_date",
        "expected_delivery_date",
        "subtotal",
        "tax_amount",
        "total_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "company",
        "vendor",
        "po_date",
        "expected_delivery_date",
        "created_at",
    )

    search_fields = (
        "po_number",
        "quotation__quotation_number",
        "vendor__name",
        "company__name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "company",
        "vendor",
        "subtotal",
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Purchase Order Information",
            {
                "fields": (
                    "po_number",
                    "quotation",
                    "company",
                    "vendor",
                    "created_by",
                    "po_date",
                    "expected_delivery_date",
                    "status",
                )
            },
        ),
        (
            "Payment & Notes",
            {
                "fields": (
                    "payment_terms",
                    "notes",
                )
            },
        ),
        (
            "Order Amount",
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "total_amount",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = [PurchaseOrderItemInline]

    actions = (
        "send_purchase_orders",
        "acknowledge_purchase_orders",
        "cancel_purchase_orders",
    )

    def save_model(self, request, obj, form, change):

        is_new = not obj.pk

        if not change:
            obj.created_by = request.user

            if obj.quotation_id:
                obj.company = obj.quotation.rfq.company
                obj.vendor = obj.quotation.vendor

        super().save_model(request, obj, form, change)

        # Automatically copy quotation items into Purchase Order
        if is_new and obj.quotation_id and not obj.items.exists():

            for quotation_item in obj.quotation.items.all():

                PurchaseOrderItem.objects.create(
                    purchase_order=obj,
                    product=quotation_item.product,
                    quantity=quotation_item.quantity,
                    unit_price=quotation_item.unit_price,
                    tax_rate=quotation_item.tax_rate,
                    tax_amount=quotation_item.tax_amount,
                    total_amount=quotation_item.total_amount,
                    delivery_time=quotation_item.delivery_time,
                    remarks=quotation_item.remarks,
                )

            obj.calculate_totals()

            obj.save(
                update_fields=[
                    "subtotal",
                    "tax_amount",
                    "total_amount",
                    "updated_at",
                ]
            )

    def save_formset(self, request, form, formset, change):

        instances = formset.save()

        for instance in instances:
            instance.calculate_amounts()

            instance.save(
                update_fields=[
                    "tax_amount",
                    "total_amount",
                    "updated_at",
                ]
            )

        purchase_order = form.instance

        purchase_order.calculate_totals()

        purchase_order.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

    @admin.action(description="Send selected Purchase Orders")
    def send_purchase_orders(self, request, queryset):

        sent_count = 0
        failed_count = 0

        for purchase_order in queryset:

            try:
                purchase_order.send()
                sent_count += 1

            except ValueError:
                failed_count += 1

        if sent_count:
            self.message_user(
                request,
                f"{sent_count} Purchase Order(s) sent successfully."
            )

        if failed_count:
            self.message_user(
                request,
                (
                    f"{failed_count} Purchase Order(s) could not be sent. "
                    f"Make sure they are Draft and contain at least one item."
                ),
                level="warning",
            )

    @admin.action(description="Acknowledge selected Purchase Orders")
    def acknowledge_purchase_orders(self, request, queryset):

        acknowledged_count = 0
        failed_count = 0

        for purchase_order in queryset:

            try:
                purchase_order.acknowledge()
                acknowledged_count += 1

            except ValueError:
                failed_count += 1

        if acknowledged_count:
            self.message_user(
                request,
                f"{acknowledged_count} Purchase Order(s) acknowledged successfully."
            )

        if failed_count:
            self.message_user(
                request,
                (
                    f"{failed_count} Purchase Order(s) could not be acknowledged. "
                    f"Only Sent Purchase Orders can be acknowledged."
                ),
                level="warning",
            )

    @admin.action(description="Cancel selected Purchase Orders")
    def cancel_purchase_orders(self, request, queryset):

        cancelled_count = 0
        failed_count = 0

        for purchase_order in queryset:

            try:
                purchase_order.cancel()
                cancelled_count += 1

            except ValueError:
                failed_count += 1

        if cancelled_count:
            self.message_user(
                request,
                f"{cancelled_count} Purchase Order(s) cancelled successfully."
            )

        if failed_count:
            self.message_user(
                request,
                f"{failed_count} Purchase Order(s) could not be cancelled.",
                level="warning",
            )


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "purchase_order",
        "product",
        "quantity",
        "unit_price",
        "tax_rate",
        "tax_amount",
        "total_amount",
        "delivery_time",
        "created_at",
    )

    list_filter = (
        "product",
        "created_at",
    )

    search_fields = (
        "purchase_order__po_number",
        "product__name",
        "product__sku",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):

        obj.calculate_amounts()

        super().save_model(request, obj, form, change)