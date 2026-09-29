from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "recipient",
        "category",
        "notification_type",
        "is_read",
        "created_at",
        "read_at",
    )

    list_filter = (
        "category",
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "recipient__username",
        "recipient__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "read_at",
    )

    fieldsets = (
        (
            "Notification",
            {
                "fields": (
                    "recipient",
                    "notification_type",
                    "category",
                    "title",
                    "message",
                    "is_read",
                    "read_at",
                )
            },
        ),

        (
            "Related Object",
            {
                "fields": (
                    "object_type",
                    "object_id",
                    "action_url",
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
        "mark_selected_as_read",
        "mark_selected_as_unread",
    )

    @admin.action(
        description="Mark selected notifications as read"
    )
    def mark_selected_as_read(
        self,
        request,
        queryset,
    ):
        updated_count = 0

        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                updated_count += 1

        self.message_user(
            request,
            f"{updated_count} notification(s) marked as read.",
        )

    @admin.action(
        description="Mark selected notifications as unread"
    )
    def mark_selected_as_unread(
        self,
        request,
        queryset,
    ):
        updated_count = 0

        for notification in queryset:
            if notification.is_read:
                notification.mark_as_unread()
                updated_count += 1

        self.message_user(
            request,
            f"{updated_count} notification(s) marked as unread.",
        )