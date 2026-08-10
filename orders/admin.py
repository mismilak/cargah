# orders/admin.py
from django.contrib import admin

from .models import (
    Customer, ServiceType, OrderCodeSequence, Order,
    OrderAttachment, OrderActivity, OrderActivityAttachment,
)


class OrderAttachmentInline(admin.TabularInline):
    model = OrderAttachment
    extra = 0
    fields = ('file', 'title', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class OrderActivityAttachmentInline(admin.TabularInline):
    model = OrderActivityAttachment
    extra = 0
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class OrderActivityInline(admin.TabularInline):
    model = OrderActivity
    extra = 0
    fields = ('service', 'operator', 'duration_value', 'price', 'notes')
    show_change_link = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'workshop', 'customer_workshop_name', 'phone', 'is_legal', 'total_debt', 'created_at')
    list_filter = ('workshop', 'is_legal')
    search_fields = ('name', 'phone', 'customer_workshop_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'workshop', 'machine_name', 'unit', 'base_price', 'created_at')
    list_filter = ('workshop', 'unit')
    search_fields = ('name', 'machine_name')
    readonly_fields = ('created_at',)


@admin.register(OrderCodeSequence)
class OrderCodeSequenceAdmin(admin.ModelAdmin):
    list_display = ('workshop', 'jalali_year', 'last_number')
    list_filter = ('workshop', 'jalali_year')
    ordering = ('-jalali_year',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'customer', 'workshop', 'status', 'created_by', 'created_at', 'updated_at')
    list_filter = ('workshop', 'status', 'created_at')
    search_fields = ('code', 'customer__name', 'customer__phone')
    readonly_fields = ('code', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    inlines = [OrderAttachmentInline, OrderActivityInline]
    autocomplete_fields = ('customer',)


@admin.register(OrderAttachment)
class OrderAttachmentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'order', 'uploaded_by', 'uploaded_at')
    search_fields = ('title', 'order__code')
    readonly_fields = ('uploaded_at',)


@admin.register(OrderActivity)
class OrderActivityAdmin(admin.ModelAdmin):
    list_display = ('order', 'service', 'operator', 'duration_value', 'price', 'created_at')
    list_filter = ('service', 'created_at')
    search_fields = ('order__code', 'notes')
    readonly_fields = ('created_at',)
    inlines = [OrderActivityAttachmentInline]


@admin.register(OrderActivityAttachment)
class OrderActivityAttachmentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'activity', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
