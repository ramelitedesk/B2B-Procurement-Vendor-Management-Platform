from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "company",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "company",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
        "company__name",
    )

    ordering = (
        "-created_at",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "sku",
        "name",
        "company",
        "category",
        "item_type",
        "unit",
        "estimated_price",
        "tax_rate",
        "status",
        "created_at",
    )

    list_filter = (
        "item_type",
        "status",
        "category",
        "company",
        "created_at",
    )

    search_fields = (
        "sku",
        "name",
        "description",
        "category__name",
        "company__name",
    )

    ordering = (
        "-created_at",
    )    