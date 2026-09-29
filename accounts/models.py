from django.contrib.auth.models import AbstractUser
from django.db import models

from companies.models import Company


class User(AbstractUser):

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        COMPANY_ADMIN = "COMPANY_ADMIN", "Company Admin"
        PROCUREMENT_MANAGER = "PROCUREMENT_MANAGER", "Procurement Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"
        VENDOR = "VENDOR", "Vendor"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        related_name="users",
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    profile_image = models.ImageField(
        upload_to="users/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"