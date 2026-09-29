from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "created_at",
        "user",
        "company",
        "action",
        "object_type",
        "object_id",
        "previous_status",
        "new_status",
    )

    list_filter = (
        "action",
        "object_type",
        "company",
        "created_at",
    )

    search_fields = (
        "description",
        "object_type",
        "object_id",
        "user__username",
        "user__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        (
            "Audit Information",
            {
                "fields": (
                    "user",
                    "company",
                    "action",
                    "description",
                )
            },
        ),
        (
            "Related Object",
            {
                "fields": (
                    "object_type",
                    "object_id",
                )
            },
        ),
        (
            "Status Change",
            {
                "fields": (
                    "previous_status",
                    "new_status",
                )
            },
        ),
        (
            "Request Information",
            {
                "fields": (
                    "ip_address",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )