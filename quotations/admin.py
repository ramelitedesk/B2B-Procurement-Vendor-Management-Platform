from django import forms
from django.contrib import admin

from .models import (
    Quotation,
    QuotationItem,
    QuotationComparison,
)


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1

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


class QuotationComparisonAdminForm(forms.ModelForm):
    class Meta:
        model = QuotationComparison
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only submitted or under-review quotations
        # should normally be available for comparison.
        self.fields["quotations"].queryset = (
            Quotation.objects.filter(
                status__in=[
                    Quotation.Status.SUBMITTED,
                    Quotation.Status.UNDER_REVIEW,
                ]
            ).select_related(
                "rfq",
                "vendor",
            )
        )

        self.fields["selected_quotation"].queryset = (
            Quotation.objects.filter(
                status__in=[
                    Quotation.Status.SUBMITTED,
                    Quotation.Status.UNDER_REVIEW,
                ]
            ).select_related(
                "rfq",
                "vendor",
            )
        )


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        "quotation_number",
        "rfq",
        "vendor",
        "quotation_date",
        "valid_until",
        "delivery_time",
        "subtotal",
        "tax_amount",
        "total_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "vendor",
        "rfq",
        "quotation_date",
        "valid_until",
        "created_at",
    )

    search_fields = (
        "quotation_number",
        "rfq__rfq_number",
        "rfq__title",
        "vendor__name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "subtotal",
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Quotation Information",
            {
                "fields": (
                    "rfq",
                    "vendor",
                    "quotation_number",
                    "quotation_date",
                    "valid_until",
                    "status",
                )
            },
        ),
        (
            "Delivery & Payment",
            {
                "fields": (
                    "delivery_time",
                    "payment_terms",
                )
            },
        ),
        (
            "Quotation Amount",
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "total_amount",
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

    inlines = [QuotationItemInline]

    actions = ("submit_quotations",)

    def save_formset(self, request, form, formset, change):
        """
        Calculate quotation item and quotation totals
        whenever quotation items are saved.
        """

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

        quotation = form.instance

        quotation.calculate_totals()

        quotation.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

    @admin.action(description="Submit selected quotations")
    def submit_quotations(self, request, queryset):
        submitted_count = 0
        failed_count = 0

        for quotation in queryset:
            try:
                quotation.submit()
                submitted_count += 1
            except ValueError:
                failed_count += 1

        if submitted_count:
            self.message_user(
                request,
                f"{submitted_count} quotation(s) submitted successfully.",
            )

        if failed_count:
            self.message_user(
                request,
                (
                    f"{failed_count} quotation(s) could not be submitted. "
                    "Make sure the quotation is Draft, its RFQ is Published, "
                    "and it has at least one item."
                ),
                level="warning",
            )


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = (
        "quotation",
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
        "quotation__quotation_number",
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
        """
        Automatically calculate item tax and total.
        """

        obj.calculate_amounts()

        super().save_model(
            request,
            obj,
            form,
            change,
        )


@admin.register(QuotationComparison)
class QuotationComparisonAdmin(admin.ModelAdmin):
    form = QuotationComparisonAdminForm

    list_display = (
        "id",
        "rfq",
        "created_by",
        "selected_quotation",
        "comparison_status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "rfq",
        "created_by",
        "created_at",
    )

    search_fields = (
        "rfq__rfq_number",
        "rfq__title",
        "created_by__username",
        "selected_quotation__quotation_number",
        "selected_quotation__vendor__name",
    )

    ordering = ("-created_at",)

    filter_horizontal = (
        "quotations",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Comparison Information",
            {
                "fields": (
                    "rfq",
                    "created_by",
                    "status",
                    "remarks",
                )
            },
        ),
        (
            "Quotations",
            {
                "fields": (
                    "quotations",
                    "selected_quotation",
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
        "complete_comparisons",
    )

    def comparison_status(self, obj):
        return obj.get_status_display()

    comparison_status.short_description = "Status"

    def save_model(self, request, obj, form, change):
        """
        Automatically assign the logged-in admin user
        when creating a quotation comparison.
        """

        if not change:
            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    @admin.action(description="Complete selected comparisons")
    def complete_comparisons(self, request, queryset):
        completed_count = 0
        failed_count = 0

        for comparison in queryset:

            if not comparison.selected_quotation:
                failed_count += 1
                continue

            try:
                comparison.complete_comparison(
                    comparison.selected_quotation
                )

                completed_count += 1

            except ValueError:
                failed_count += 1

        if completed_count:
            self.message_user(
                request,
                (
                    f"{completed_count} comparison(s) completed "
                    "successfully."
                ),
            )

        if failed_count:
            self.message_user(
                request,
                (
                    f"{failed_count} comparison(s) could not be completed. "
                    "Make sure a valid submitted quotation is selected."
                ),
                level="warning",
            )