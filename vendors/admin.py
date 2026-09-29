from django.contrib import admin

from .models import (
    Vendor,
    VendorContact,
    VendorBankDetails,
    VendorDocument,
    VendorPerformanceHistory,
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "company",
        "registration_number",
        "gst_number",
        "email",
        "phone",
        "status",
        "rating",
        "created_at",
    )

    list_filter = (
        "company",
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "registration_number",
        "gst_number",
        "email",
    )

    ordering = (
        "-created_at",
    )

@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "vendor",
        "designation",
        "email",
        "phone",
        "contact_type",
        "is_primary",
        "created_at",
    )

    list_filter = (
        "contact_type",
        "is_primary",
        "vendor",
    )

    search_fields = (
        "name",
        "email",
        "phone",
        "vendor__name",
    )

    ordering = (
        "-created_at",
    )    

@admin.register(VendorBankDetails)
class VendorBankDetailsAdmin(admin.ModelAdmin):

    list_display = (
        "vendor",
        "bank_name",
        "account_holder_name",
        "ifsc_code",
        "branch_name",
        "account_type",
        "created_at",
    )

    list_filter = (
        "account_type",
        "bank_name",
    )

    search_fields = (
        "vendor__name",
        "bank_name",
        "account_holder_name",
        "ifsc_code",
    )

    ordering = (
        "-created_at",
    )    


@admin.register(VendorDocument)
class VendorDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "vendor",
        "document_type",
        "document_number",
        "expiry_date",
        "status",
        "created_at",
    )

    list_filter = (
        "document_type",
        "status",
        "vendor",
    )

    search_fields = (
        "title",
        "document_number",
        "vendor__name",
    )

    ordering = ("-created_at",)    


@admin.register(VendorPerformanceHistory)
class VendorPerformanceHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "vendor",
        "evaluation_date",
        "delivery_score",
        "quality_score",
        "pricing_score",
        "service_score",
        "overall_score",
        "created_at",
    )

    list_filter = (
        "evaluation_date",
        "vendor",
    )

    search_fields = (
        "vendor__name",
        "comments",
    )

    ordering = (
        "-evaluation_date",
        "-created_at",
    )    