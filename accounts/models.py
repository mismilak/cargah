import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


def generate_workshop_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=7))
        if not Workshop.objects.filter(code=code).exists():
            return code


class Workshop(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    national_code = models.CharField(max_length=30, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_workshop_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WorkshopMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'مالک'),
        ('management', 'مدیریت'),
        ('technical', 'فنی'),
        ('accounting', 'حسابداری'),
        ('reception', 'پذیرش'),
        ('delivery', 'ترخیص'),
        ('operator', 'اپراتور'),
    ]

    workshop = models.ForeignKey(
        Workshop,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='workshop_memberships'
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='management')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workshop', 'user')

    def __str__(self):
        return f"{self.user} - {self.workshop} - {self.role}"


class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(unique=True)

    class Meta:
        swappable = 'AUTH_USER_MODEL'


class OTPCode(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate(cls, phone):
        cls.objects.filter(phone=phone, is_used=False).delete()
        code = str(random.randint(100000, 999999))
        return cls.objects.create(phone=phone, code=code)

    def __str__(self):
        return f"{self.phone} - {self.code}"
