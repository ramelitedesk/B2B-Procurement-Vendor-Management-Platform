from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        INFO = "INFO", "Information"
        SUCCESS = "SUCCESS", "Success"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"

    class Category(models.TextChoices):
        PROCUREMENT = "PROCUREMENT", "Procurement"
        RFQ = "RFQ", "RFQ"
        QUOTATION = "QUOTATION", "Quotation"
        PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"
        DELIVERY = "DELIVERY", "Delivery"
        INVOICE = "INVOICE", "Invoice"
        PAYMENT = "PAYMENT", "Payment"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.SYSTEM,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    # Optional reference to the business object that caused
    # the notification.
    object_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    object_id = models.PositiveBigIntegerField(
        blank=True,
        null=True,
    )

    action_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()

            self.save(
                update_fields=[
                    "is_read",
                    "read_at",
                    "updated_at",
                ]
            )

    def mark_as_unread(self):
        self.is_read = False
        self.read_at = None

        self.save(
            update_fields=[
                "is_read",
                "read_at",
                "updated_at",
            ]
        )

    @classmethod
    def create_notification(
        cls,
        recipient,
        title,
        message,
        category=Category.SYSTEM,
        notification_type=NotificationType.INFO,
        object_type=None,
        object_id=None,
        action_url=None,
    ):
        return cls.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            category=category,
            notification_type=notification_type,
            object_type=object_type,
            object_id=object_id,
            action_url=action_url,
        )