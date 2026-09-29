from django.db import models
from companies.models import Company


class Category(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    name = models.CharField(
        max_length=255,
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name


class Product(models.Model):

    class ItemType(models.TextChoices):
        PRODUCT = "PRODUCT", "Product"
        SERVICE = "SERVICE", "Service"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="products",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )

    sku = models.CharField(
        max_length=100,
    )

    name = models.CharField(
        max_length=255,
    )

    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.PRODUCT,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    unit = models.CharField(
        max_length=50,
        default="Piece",
    )

    estimated_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.sku} - {self.name}"    