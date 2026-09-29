from django import forms
from django.contrib import admin

from .models import Invoice, InvoiceItem
from purchase_orders.models import PurchaseOrder


# ============================================================
# INVOICE ITEM INLINE
# ============================================================

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0

    fields = (
        "purchase_order_item",
        "product",
        "quantity",
        "unit_price",
        "tax_rate",
        "tax_amount",
        "total_amount",
        "remarks",
    )

    readonly_fields = (
        "product",
        "unit_price",
        "tax_amount",
        "total_amount",
    )


# ============================================================
# INVOICE FORM
# ============================================================

class InvoiceAdminForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only allow invoices against:
        # PARTIALLY_DELIVERED
        # DELIVERED
        # CLOSED
        self.fields["purchase_order"].queryset = (
            PurchaseOrder.objects
            .filter(
                status__in=[
                    PurchaseOrder.Status.PARTIALLY_DELIVERED,
                    PurchaseOrder.Status.DELIVERED,
                    PurchaseOrder.Status.CLOSED,
                ]
            )
            .select_related(
                "vendor",
                "company",
            )
            .order_by("-created_at")
        )

    def clean(self):
        cleaned_data = super().clean()

        purchase_order = cleaned_data.get("purchase_order")

        if purchase_order:
            # Automatically use the PO vendor
            self.instance.vendor = purchase_order.vendor

        return cleaned_data


# ============================================================
# INVOICE ADMIN
# ============================================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):

    form = InvoiceAdminForm

    list_display = (
        "invoice_number",
        "purchase_order",
        "vendor",
        "invoice_date",
        "due_date",
        "subtotal",
        "tax_amount",
        "total_amount",
        "status",
        "uploaded_by",
        "created_at",
    )

    list_filter = (
        "status",
        "vendor",
        "invoice_date",
        "due_date",
        "created_at",
    )

    search_fields = (
        "invoice_number",
        "purchase_order__po_number",
        "vendor__name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "vendor",
        "uploaded_by",
        "subtotal",
        "tax_amount",
        "total_amount",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Invoice Information",
            {
                "fields": (
                    "invoice_number",
                    "purchase_order",
                    "vendor",
                    "uploaded_by",
                    "invoice_date",
                    "due_date",
                    "invoice_file",
                    "status",
                )
            },
        ),

        (
            "Invoice Amount",
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "total_amount",
                )
            },
        ),

        (
            "Review Information",
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                    "rejection_reason",
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

    inlines = [
        InvoiceItemInline,
    ]

    actions = (
        "submit_invoices",
        "approve_invoices",
        "reject_invoices",
        "mark_invoices_paid",
    )

    # ========================================================
    # SAVE INVOICE
    # ========================================================

    def save_model(self, request, obj, form, change):

        if not change:

            # Automatically record the logged-in user
            obj.uploaded_by = request.user

            # Automatically get vendor from Purchase Order
            if obj.purchase_order_id:
                obj.vendor = obj.purchase_order.vendor

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        # ====================================================
        # CREATE INVOICE ITEMS FROM PURCHASE ORDER
        # ====================================================

        if not change and obj.purchase_order_id:

            for po_item in obj.purchase_order.items.all():

                # Avoid duplicate invoice items
                if obj.items.filter(
                    purchase_order_item=po_item
                ).exists():
                    continue

                invoice_item = InvoiceItem(
                    invoice=obj,
                    purchase_order_item=po_item,
                    product=po_item.product,
                    quantity=0,
                    unit_price=po_item.unit_price,
                    tax_rate=po_item.tax_rate,
                )

                # ------------------------------------------------
                # Calculate quantity currently available for invoice
                # ------------------------------------------------

                remaining_quantity = (
                    invoice_item.get_remaining_invoiceable_quantity()
                )

                invoice_item.quantity = remaining_quantity

                # Calculate tax and total
                invoice_item.calculate_amounts()

                invoice_item.save()

        # ====================================================
        # Calculate invoice totals
        # ====================================================

        obj.calculate_totals()

        obj.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

    # ========================================================
    # SAVE INLINE FORMSET
    # ========================================================

    def save_formset(
        self,
        request,
        form,
        formset,
        change,
    ):

        # Save invoice items
        formset.save()

        invoice = form.instance

        # Recalculate invoice totals
        invoice.calculate_totals()

        invoice.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

    # ========================================================
    # SUBMIT INVOICE FOR REVIEW
    # ========================================================

    @admin.action(
        description="Submit selected invoices for review"
    )
    def submit_invoices(
        self,
        request,
        queryset,
    ):

        submitted_count = 0
        failed_count = 0

        for invoice in queryset:

            try:

                invoice.submit_for_review()

                submitted_count += 1

            except Exception:

                failed_count += 1

        if submitted_count:

            self.message_user(
                request,
                f"{submitted_count} invoice(s) submitted for review.",
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} invoice(s) could not be submitted. "
                    "Check invoice items, quantities, and PO amount."
                ),
                level="warning",
            )

    # ========================================================
    # APPROVE INVOICE
    # ========================================================

    @admin.action(
        description="Approve selected invoices"
    )
    def approve_invoices(
        self,
        request,
        queryset,
    ):

        approved_count = 0
        failed_count = 0

        for invoice in queryset:

            try:

                invoice.approve(
                    request.user
                )

                approved_count += 1

            except Exception:

                failed_count += 1

        if approved_count:

            self.message_user(
                request,
                f"{approved_count} invoice(s) approved successfully.",
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} invoice(s) could not be approved. "
                    "Only invoices under review can be approved."
                ),
                level="warning",
            )

    # ========================================================
    # REJECT INVOICE
    # ========================================================

    @admin.action(
        description="Reject selected invoices"
    )
    def reject_invoices(
        self,
        request,
        queryset,
    ):

        rejected_count = 0
        failed_count = 0

        for invoice in queryset:

            try:

                invoice.reject(
                    request.user,
                    reason="Rejected from Django Admin.",
                )

                rejected_count += 1

            except Exception:

                failed_count += 1

        if rejected_count:

            self.message_user(
                request,
                f"{rejected_count} invoice(s) rejected successfully.",
            )

        if failed_count:

            self.message_user(
                request,
                f"{failed_count} invoice(s) could not be rejected.",
                level="warning",
            )

    # ========================================================
    # MARK INVOICE AS PAID
    # ========================================================

    @admin.action(
        description="Mark selected invoices as paid"
    )
    def mark_invoices_paid(
        self,
        request,
        queryset,
    ):

        paid_count = 0
        failed_count = 0

        for invoice in queryset:

            try:

                invoice.mark_paid()

                paid_count += 1

            except Exception:

                failed_count += 1

        if paid_count:

            self.message_user(
                request,
                f"{paid_count} invoice(s) marked as paid.",
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} invoice(s) could not be marked as paid. "
                    "Only approved invoices can be marked as paid."
                ),
                level="warning",
            )


# ============================================================
# INVOICE ITEM ADMIN
# ============================================================

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):

    list_display = (
        "invoice",
        "product",
        "quantity",
        "unit_price",
        "tax_rate",
        "tax_amount",
        "total_amount",
        "created_at",
    )

    list_filter = (
        "product",
        "created_at",
    )

    search_fields = (
        "invoice__invoice_number",
        "invoice__purchase_order__po_number",
        "product__name",
        "product__sku",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "product",
        "unit_price",
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    # ========================================================
    # SAVE INVOICE ITEM
    # ========================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        obj.calculate_amounts()

        super().save_model(
            request,
            obj,
            form,
            change,
        )