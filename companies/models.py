from django.db import models


class Company(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(
        max_length=255
    )

    registration_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    gst_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    address = models.TextField(
        blank=True,
        null=True,
    )

    website = models.URLField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name