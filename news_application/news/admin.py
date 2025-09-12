from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Publisher, Article, Newsletter

# Customize the UserAdmin class to manage our custom user model


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': (
                'role',
                'subscriptions_publishers',
                'subscriptions_journalists'
            )
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )


# Register models with the admin site
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)
