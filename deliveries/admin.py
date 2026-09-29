from django import forms
from django.contrib import admin

from .models import Delivery, DeliveryItem
from purchase_orders.models import PurchaseOrder


class DeliveryItemInline(admin.TabularInline):

    model = DeliveryItem

    extra = 0

    fields = (
        "purchase_order_item",
        "ordered_quantity",
        "delivered_quantity",
        "remarks",
    )

    readonly_fields = (
        "ordered_quantity",
    )


class DeliveryAdminForm(forms.ModelForm):

    class Meta:
        model = Delivery
        fields = "__all__"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["purchase_order"].queryset = (
            PurchaseOrder.objects.filter(
                status__in=[
                    PurchaseOrder.Status.ACKNOWLEDGED,
                    PurchaseOrder.Status.PARTIALLY_DELIVERED,
                ]
            ).select_related(
                "vendor",
                "company",
            )
        )

    def clean(self):

        cleaned_data = super().clean()

        purchase_order = cleaned_data.get("purchase_order")

        if purchase_order:

            self.instance.vendor = purchase_order.vendor

        return cleaned_data


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):

    form = DeliveryAdminForm

    list_display = (
        "delivery_number",
        "purchase_order",
        "vendor",
        "shipment_date",
        "expected_delivery_date",
        "actual_delivery_date",
        "courier_name",
        "tracking_number",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "vendor",
        "shipment_date",
        "expected_delivery_date",
        "actual_delivery_date",
        "created_at",
    )

    search_fields = (
        "delivery_number",
        "purchase_order__po_number",
        "vendor__name",
        "tracking_number",
        "courier_name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "vendor",
        "created_by",
        "actual_delivery_date",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Delivery Information",
            {
                "fields": (
                    "delivery_number",
                    "purchase_order",
                    "vendor",
                    "created_by",
                    "shipment_date",
                    "expected_delivery_date",
                    "actual_delivery_date",
                    "status",
                )
            },
        ),
        (
            "Shipment Information",
            {
                "fields": (
                    "courier_name",
                    "tracking_number",
                    "notes",
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

    inlines = [
        DeliveryItemInline,
    ]

    actions = (
        "confirm_deliveries",
        "cancel_deliveries",
    )

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if not change:

            obj.created_by = request.user

            if obj.purchase_order_id:
                obj.vendor = obj.purchase_order.vendor

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        # Automatically copy PO items for a new delivery
        if not change and obj.purchase_order_id:

            for po_item in obj.purchase_order.items.all():

                if not obj.items.filter(
                    purchase_order_item=po_item
                ).exists():

                    DeliveryItem.objects.create(
                        delivery=obj,
                        purchase_order_item=po_item,
                        ordered_quantity=po_item.quantity,
                        delivered_quantity=0,
                    )

    def save_formset(
        self,
        request,
        form,
        formset,
        change,
    ):

        instances = formset.save()

        for instance in instances:

            instance.ordered_quantity = (
                instance.purchase_order_item.quantity
            )

            instance.save()

    @admin.action(description="Confirm selected deliveries")
    def confirm_deliveries(
        self,
        request,
        queryset,
    ):

        confirmed_count = 0
        failed_count = 0

        for delivery in queryset:

            try:

                delivery.confirm_delivery()

                confirmed_count += 1

            except (ValueError, forms.ValidationError):

                failed_count += 1

        if confirmed_count:

            self.message_user(
                request,
                (
                    f"{confirmed_count} delivery(s) "
                    f"confirmed successfully."
                ),
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} delivery(s) "
                    f"could not be confirmed. "
                    f"Check delivery quantities and status."
                ),
                level="warning",
            )

    @admin.action(description="Cancel selected deliveries")
    def cancel_deliveries(
        self,
        request,
        queryset,
    ):

        cancelled_count = 0
        failed_count = 0

        for delivery in queryset:

            try:

                delivery.cancel()

                cancelled_count += 1

            except ValueError:

                failed_count += 1

        if cancelled_count:

            self.message_user(
                request,
                (
                    f"{cancelled_count} delivery(s) "
                    f"cancelled successfully."
                ),
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} delivery(s) "
                    f"could not be cancelled."
                ),
                level="warning",
            )


@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):

    list_display = (
        "delivery",
        "purchase_order_item",
        "ordered_quantity",
        "delivered_quantity",
        "remaining_quantity",
        "created_at",
    )

    list_filter = (
        "delivery__status",
        "created_at",
    )

    search_fields = (
        "delivery__delivery_number",
        "delivery__purchase_order__po_number",
        "purchase_order_item__product__name",
        "purchase_order_item__product__sku",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "ordered_quantity",
        "created_at",
        "updated_at",
    )

    def remaining_quantity(self, obj):

        return obj.get_remaining_quantity()

    remaining_quantity.short_description = "Remaining"