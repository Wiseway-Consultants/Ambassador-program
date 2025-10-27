from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class EmailUserAdmin(UserAdmin):

    readonly_fields = ('id', 'referral_code')

    fieldsets = (
        (None, {'fields': ('id', 'referral_code', 'email', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name',
            'last_name',
            'is_accepted_terms',
            'currency'
        )}),
        (_('Referral info'), {'fields': (
            'referral_qr_code_id',
            'invited_by_user',
            'is_prospect',
            'qr_code_bundles'
        )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


admin.site.register(User, EmailUserAdmin)
