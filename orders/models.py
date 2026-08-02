import jdatetime
from django.conf import settings
from django.db import models, transaction


class Customer(models.Model):
    workshop = models.ForeignKey('accounts.Workshop', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    customer_workshop_name = models.CharField(max_length=200, default="None")
    phone = models.CharField(max_length=20, blank=True)
    is_legal = models.BooleanField(default=False)  # حقوقی یا حقیقی
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_debt(self):
        from django.db.models import Sum
        from billing.models import Invoice
        result = Invoice.objects.filter(
            order__customer=self,
            status__in=['unpaid', 'partial']
        ).aggregate(total=Sum('final_amount'))['total'] or Decimal('0')

        paid = Invoice.objects.filter(
            order__customer=self,
            status__in=['unpaid', 'partial']
        ).aggregate(
            total_paid=Sum('payments__amount',
                           filter=models.Q(
                               payments__method__in=['cash', 'transfer']
                           ) | models.Q(
                               payments__method='check',
                               payments__check_status='cleared'
                           )
                           )
        )['total_paid'] or Decimal('0')

        return result - paid

    @property
    def has_debt(self):
        return self.total_debt > 0


class ServiceType(models.Model):
    UNIT_CHOICES = [
        ('day', 'روز'),
        ('hour', 'ساعت'),
        ('minute', 'دقیقه'),
        ('seconds', 'ثانیه'),
        ('ton', 'تن'),
        ('kg', 'کیلوگرم'),
        ('gram', 'گرم'),
        ('count', 'عدد'),
        ('meter', 'متر'),
        ('cmeter', 'سانتی متر'),
        ('mmeter', 'میلی متر'),
        ('sqmeter', 'مترمربع'),
        ('adl', 'عدل'),
        ('mesghal', 'مثقال'),
        ('jin', 'جین'),
    ]
    workshop = models.ForeignKey('accounts.Workshop', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name="نام خدمت/عملیات")
    machine_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, verbose_name="واحد اندازه‌گیری")
    base_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ پایه")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.workshop.name}"


class OrderCodeSequence(models.Model):
    workshop = models.ForeignKey('accounts.Workshop', on_delete=models.CASCADE)
    jalali_year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('workshop', 'jalali_year')

    def __str__(self):
        return f"{self.workshop_id} - {self.jalali_year} - {self.last_number}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('reception', 'پذیرش'),
        ('technical', 'فنی'),
        ('accounting', 'حسابداری'),
        ('management', 'مدیریت'),
        ('payment', 'پرداخت'),
        ('done', 'تکمیل'),
    ]

    workshop = models.ForeignKey('accounts.Workshop', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reception')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name='کد سفارش'
    )

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_order_code()
        super().save(*args, **kwargs)

    def generate_order_code(self):
        jalali_year = jdatetime.date.today().year

        with transaction.atomic():
            sequence, created = OrderCodeSequence.objects.select_for_update().get_or_create(
                workshop=self.workshop,
                jalali_year=jalali_year,
                defaults={'last_number': 0}
            )

            sequence.last_number += 1
            sequence.save(update_fields=['last_number'])

            six_digit_number = str(sequence.last_number).zfill(6)

            return f"{self.workshop_id}{jalali_year}{six_digit_number}"

    def __str__(self):
        return f"{self.code} - {self.customer.name}"


class OrderAttachment(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='orders/attachments/')
    title = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Attachment #{self.pk} for Order #{self.order_id}"


class OrderActivity(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='activities')
    operator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    service = models.ForeignKey(ServiceType, on_delete=models.PROTECT, verbose_name="نوع عملیات")

    duration_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="مقدار/زمان")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ نهایی")  # قیمت در لحظه ثبت

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.price and self.service:
            self.price = self.service.base_price
        super().save(*args, **kwargs)


class OrderActivityAttachment(models.Model):
    activity = models.ForeignKey(
        OrderActivity,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='orders/activities/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
