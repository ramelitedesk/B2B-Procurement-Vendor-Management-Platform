from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
    'username',
    'email',
    'first_name',
    'last_name',
    'role',
    'company',
    'is_active',
    'is_staff',
)

    list_filter = (
        'role',
        'is_active',
        'is_staff',
    )

    fieldsets = UserAdmin.fieldsets + (
    (
        'Additional Information',
        {
            'fields': (
                'role',
                'company',
                'phone',
                'profile_image',
            )
        },
    ),
)

    add_fieldsets = UserAdmin.add_fieldsets + (
    (
        'Additional Information',
        {
            'fields': (
                'role',
                'company',
                'phone',
                'profile_image',
            )
        },
    ),
)