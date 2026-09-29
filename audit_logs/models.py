from django.conf import settings
from django.db import models


class AuditLog(models.Model):

    class Action(models.TextChoices):
        CREATE = "CREATE", "Created"
        UPDATE = "UPDATE", "Updated"
        DELETE = "DELETE", "Deleted"
        SUBMIT = "SUBMIT", "Submitted"
        APPROVE = "APPROVE", "Approved"
        REJECT = "REJECT", "Rejected"
        SEND = "SEND", "Sent"
        ACKNOWLEDGE = "ACKNOWLEDGE", "Acknowledged"
        PUBLISH = "PUBLISH", "Published"
        ACCEPT = "ACCEPT", "Accepted"
        CANCEL = "CANCEL", "Cancelled"
        CONFIRM = "CONFIRM", "Confirmed"
        PAYMENT = "PAYMENT", "Payment Recorded"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        blank=True,
        null=True,
    )

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        blank=True,
        null=True,
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    object_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    object_id = models.PositiveBigIntegerField(
        blank=True,
        null=True,
    )

    description = models.TextField()

    previous_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    new_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        username = self.user.username if self.user else "System"

        return (
            f"{username} - "
            f"{self.get_action_display()} - "
            f"{self.object_type or 'System'}"
        )

    @classmethod
    def create_log(
        cls,
        *,
        user=None,
        company=None,
        action,
        description,
        object_type=None,
        object_id=None,
        previous_status=None,
        new_status=None,
        ip_address=None,
    ):
        return cls.objects.create(
            user=user,
            company=company,
            action=action,
            description=description,
            object_type=object_type,
            object_id=object_id,
            previous_status=previous_status,
            new_status=new_status,
            ip_address=ip_address,
        )