from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "registration_number",
        "gst_number",
        "email",
        "phone",
        "status",
        "created_at",
    )

    list_filter = (
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