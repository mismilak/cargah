from django.db import models
from decimal import Decimal


class SubscriptionPlan(models.Model):
    PERIOD_CHOICES = [('monthly', 'ماهانه'), ('yearly', 'سالانه')]
    name = models.CharField(max_length=100)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    is_active = models.BooleanField(default=True)


class Subscription(models.Model):
    STATUS_CHOICES = [('pending', 'در انتظار تایید'), ('active', 'فعال'), ('expired', 'منقضی')]
    workshop = models.ForeignKey('accounts.Workshop', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    receipt_image = models.ImageField(upload_to='subscriptions/receipts/', blank=True)
    receipt_text = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    confirmed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'پرداخت‌نشده'),
        ('partial', 'پرداخت جزئی / بدهکار'),
        ('paid', 'تسویه شده'),
    ]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='invoice')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0)
    discount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')

    released = models.BooleanField(default=False)
    released_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='released_invoices'
    )
    released_at = models.DateTimeField(null=True, blank=True)
    release_note = models.TextField(blank=True)  # دلیل ترخیص بدون تسویه

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_by_manager = models.BooleanField(default=False)
    confirmed_by_manager_date_time = models.DateTimeField(null=True,blank=True)

    @property
    def paid_amount(self):
        from django.db.models import Q, Sum
        result = self.payments.filter(
            Q(method__in=['cash', 'transfer']) |
            Q(method='check', check_status='cleared')
        ).aggregate(total=Sum('amount'))['total']
        return result or Decimal('0')

    @property
    def remaining_amount(self):
        return self.final_amount - self.paid_amount

    def refresh_status(self):
        remaining = self.remaining_amount
        if remaining <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        else:
            self.status = 'unpaid'
        self.save(update_fields=['status'])


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'نقد'),
        ('transfer', 'کارت به کارت / شبا'),
        ('check', 'چک'),
    ]
    CHECK_STATUS_CHOICES = [
        ('pending', 'در جریان وصول'),
        ('cleared', 'وصول شده'),
        ('bounced', 'برگشتی'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    paid_at = models.DateField()
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    # فیلدهای مخصوص چک
    check_number = models.CharField(max_length=50, blank=True)
    check_bank = models.CharField(max_length=100, blank=True)
    check_due_date = models.DateField(null=True, blank=True)
    check_status = models.CharField(max_length=10, choices=CHECK_STATUS_CHOICES, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.refresh_status()

    def __str__(self):
        return f"{self.get_method_display()} - {self.amount}"
