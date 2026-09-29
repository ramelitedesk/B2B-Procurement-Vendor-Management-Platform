from django import forms
from django.contrib import admin

from .models import Payment
from invoices.models import Invoice


# ============================================================
# PAYMENT ADMIN FORM
# ============================================================

class PaymentAdminForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = "__all__"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Payments are allowed only for approved or paid invoices
        self.fields["invoice"].queryset = (
            Invoice.objects
            .filter(
                status__in=[
                    Invoice.Status.APPROVED,
                    Invoice.Status.PAID,
                ]
            )
            .select_related(
                "vendor",
                "purchase_order",
                "purchase_order__company",
            )
            .order_by("-created_at")
        )

    def clean(self):

        cleaned_data = super().clean()

        invoice = cleaned_data.get("invoice")

        if invoice:

            self.instance.company = (
                invoice.purchase_order.company
            )

            self.instance.vendor = invoice.vendor

        return cleaned_data


# ============================================================
# PAYMENT ADMIN
# ============================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    form = PaymentAdminForm

    list_display = (
        "payment_number",
        "invoice",
        "vendor",
        "payment_date",
        "amount",
        "payment_method",
        "transaction_reference",
        "status",
        "recorded_by",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
        "vendor",
        "payment_date",
        "created_at",
    )

    search_fields = (
        "payment_number",
        "invoice__invoice_number",
        "invoice__purchase_order__po_number",
        "vendor__name",
        "transaction_reference",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "company",
        "vendor",
        "recorded_by",
        "status",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Payment Information",
            {
                "fields": (
                    "payment_number",
                    "invoice",
                    "company",
                    "vendor",
                    "recorded_by",
                    "payment_date",
                    "amount",
                    "payment_method",
                    "transaction_reference",
                    "status",
                )
            },
        ),

        (
            "Additional Information",
            {
                "fields": (
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

    actions = (
        "record_selected_payments",
        "cancel_selected_payments",
    )

    # ========================================================
    # SAVE PAYMENT
    # ========================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if not change:

            obj.recorded_by = request.user

            if obj.invoice_id:

                obj.company = (
                    obj.invoice.purchase_order.company
                )

                obj.vendor = (
                    obj.invoice.vendor
                )

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    # ========================================================
    # RECORD PAYMENT
    # ========================================================

    @admin.action(
        description="Record selected payments"
    )
    def record_selected_payments(
        self,
        request,
        queryset,
    ):

        success_count = 0
        failed_count = 0

        for payment in queryset:

            try:

                payment.record_payment()

                success_count += 1

            except Exception:

                failed_count += 1

        if success_count:

            self.message_user(
                request,
                f"{success_count} payment(s) recorded successfully.",
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} payment(s) could not be recorded. "
                    "Check invoice status, amount, and remaining balance."
                ),
                level="warning",
            )

    # ========================================================
    # CANCEL PAYMENT
    # ========================================================

    @admin.action(
        description="Cancel selected payments"
    )
    def cancel_selected_payments(
        self,
        request,
        queryset,
    ):

        success_count = 0
        failed_count = 0

        for payment in queryset:

            try:

                payment.cancel()

                success_count += 1

            except Exception:

                failed_count += 1

        if success_count:

            self.message_user(
                request,
                f"{success_count} payment(s) cancelled successfully.",
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} payment(s) could not be cancelled."
                ),
                level="warning",
            )