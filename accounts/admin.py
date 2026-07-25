from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, OTPCode, Workshop, WorkshopMembership


class WorkshopMembershipInline(admin.TabularInline):
    model = WorkshopMembership
    extra = 1
    autocomplete_fields = ('user',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id', 'username', 'email', 'phone',
        'is_staff', 'is_active', 'date_joined'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات تکمیلی', {'fields': ('phone',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('اطلاعات تکمیلی', {'fields': ('email', 'phone')}),
    )


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'owner', 'is_active',
        'national_code', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'owner__username', 'owner__email', 'national_code')
    ordering = ('-created_at',)
    autocomplete_fields = ('owner',)
    inlines = [WorkshopMembershipInline]


@admin.register(WorkshopMembership)
class WorkshopMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'workshop', 'user', 'role',
        'is_active', 'joined_at'
    )
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = (
        'workshop__name',
        'user__username',
        'user__email',
        'user__phone'
    )
    ordering = ('-joined_at',)
    autocomplete_fields = ('workshop', 'user')


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'code', 'is_used', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('phone', 'code')
    ordering = ('-created_at',)
