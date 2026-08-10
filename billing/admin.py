from django.contrib import admin
from django.utils.html import format_html
from .models import SubscriptionPlan, Subscription, Invoice, Payment


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'period', 'price', 'is_active')
    list_filter = ('period', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)
    actions = ['make_active', 'make_inactive']

    @admin.action(description='فعال کردن پلن‌های انتخاب‌شده')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='غیرفعال کردن پلن‌های انتخاب‌شده')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'workshop',
        'plan',
        'status',
        'start_date',
        'end_date',
        'confirmed_by',
        'created_at',
        'receipt_preview',
    )
    list_filter = ('status', 'plan__period', 'plan', 'created_at', 'start_date', 'end_date')
    search_fields = ('workshop__name', 'receipt_text')
    autocomplete_fields = ('workshop', 'plan', 'confirmed_by')
    readonly_fields = ('created_at', 'receipt_preview')
    actions = ['mark_pending', 'mark_active', 'mark_expired']

    fieldsets = (
        ('اطلاعات اشتراک', {
            'fields': ('workshop', 'plan', 'status')
        }),
        ('رسید', {
            'fields': ('receipt_image', 'receipt_preview', 'receipt_text')
        }),
        ('تایید و بازه زمانی', {
            'fields': ('confirmed_by', 'start_date', 'end_date')
        }),
        ('سیستمی', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description='پیش‌نمایش رسید')
    def receipt_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height:60px; border-radius:6px;" /></a>',
                obj.receipt_image.url
            )
        return '-'

    @admin.action(description='تغییر وضعیت به در انتظار تایید')
    def mark_pending(self, request, queryset):
        queryset.update(status='pending')

    @admin.action(description='تغییر وضعیت به فعال')
    def mark_active(self, request, queryset):
        queryset.update(status='active')

    @admin.action(description='تغییر وضعیت به منقضی')
    def mark_expired(self, request, queryset):
        queryset.update(status='expired')


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = (
        'method',
        'amount',
        'paid_at',
        'recorded_by',
        'notes',
        'check_number',
        'check_bank',
        'check_due_date',
        'check_status',
        'created_at',
    )
    readonly_fields = ('created_at',)
    autocomplete_fields = ('recorded_by',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'total_amount',
        'discount',
        'final_amount',
        'paid_amount_display',
        'remaining_amount_display',
        'status',
        'released',
        'confirmed_by_manager',
        'created_at',
    )
    list_filter = (
        'status',
        'released',
        'confirmed_by_manager',
        'created_at',
        'released_at',
        'confirmed_by_manager_date_time',
    )
    search_fields = ('order__id',)
    autocomplete_fields = ('order', 'released_by')
    readonly_fields = (
        'created_at',
        'paid_amount_display',
        'remaining_amount_display',
    )
    inlines = [PaymentInline]

    fieldsets = (
        ('اطلاعات فاکتور', {
            'fields': (
                'order',
                'total_amount',
                'discount',
                'final_amount',
                'status',
            )
        }),
        ('وضعیت پرداخت', {
            'fields': (
                'paid_amount_display',
                'remaining_amount_display',
            )
        }),
        ('ترخیص', {
            'fields': (
                'released',
                'released_by',
                'released_at',
                'release_note',
            )
        }),
        ('تایید مدیریت', {
            'fields': (
                'confirmed_by_manager',
                'confirmed_by_manager_date_time',
            )
        }),
        ('سیستمی', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description='مبلغ پرداخت‌شده')
    def paid_amount_display(self, obj):
        return obj.paid_amount

    @admin.display(description='مانده')
    def remaining_amount_display(self, obj):
        return obj.remaining_amount


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'invoice',
        'method',
        'amount',
        'paid_at',
        'check_status',
        'recorded_by',
        'created_at',
    )
    list_filter = ('method', 'check_status', 'paid_at', 'created_at')
    search_fields = (
        'invoice__order__id',
        'check_number',
        'check_bank',
        'notes',
    )
    autocomplete_fields = ('invoice', 'recorded_by')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('اطلاعات پرداخت', {
            'fields': (
                'invoice',
                'method',
                'amount',
                'paid_at',
                'recorded_by',
                'notes',
            )
        }),
        ('اطلاعات چک', {
            'fields': (
                'check_number',
                'check_bank',
                'check_due_date',
                'check_status',
            )
        }),
        ('سیستمی', {
            'fields': ('created_at',)
        }),
    )
