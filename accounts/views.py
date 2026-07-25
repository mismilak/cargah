from django.contrib.auth import logout, get_user_model

from .forms import UserRegisterForm, UserLoginForm

User = get_user_model()
from datetime import timedelta
from django.contrib.auth import login
from django.utils import timezone

from .models import User, OTPCode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import Workshop, WorkshopMembership


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = UserRegisterForm()

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد.')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'لطفاً اطلاعات را درست وارد کنید.')

    context = {
        'form': form,
        'page': 'register',
        'active_tab': "dashboard",

    }
    return render(request, 'accounts/auth.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return render(request, 'dashboard/index.html')
    form = UserLoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'با موفقیت وارد شدید.')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')

    context = {
        'form': form,
        'page': 'login',
    }
    return render(request, 'accounts/auth.html', context)


def logout_view(request):
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('accounts:login')


def send_otp_sms(phone, code):
    """
    این تابع را بعداً به سرویس پیامک واقعی وصل کن
    فعلاً فقط برای تست
    """
    print(f'OTP for {phone}: {code}')


def otp_request_view(request):
    otp_cooldown = None

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()

        if not phone:
            messages.error(request, 'شماره موبایل را وارد کنید.')
            return render(request, 'accounts/auth.html', {
                'page': 'otp_request',
                'otp_cooldown': otp_cooldown
            })

        user = User.objects.filter(phone=phone).first()
        if not user:
            messages.error(request, 'کاربری با این شماره موبایل یافت نشد.')
            return render(request, 'accounts/auth.html', {
                'page': 'otp_request',
                'otp_cooldown': otp_cooldown
            })

        last_otp = OTPCode.objects.filter(phone=phone).order_by('-created_at').first()
        if last_otp:
            diff = timezone.now() - last_otp.created_at
            cooldown_seconds = 60
            if diff.total_seconds() < cooldown_seconds:
                otp_cooldown = cooldown_seconds - int(diff.total_seconds())
                messages.warning(request, 'لطفاً کمی صبر کنید و دوباره تلاش کنید.')
                return render(request, 'accounts/auth.html', {
                    'page': 'otp_request',
                    'otp_cooldown': otp_cooldown
                })

        otp = OTPCode.generate(phone)
        send_otp_sms(phone, otp.code)

        request.session['otp_phone'] = phone
        messages.success(request, 'کد تأیید ارسال شد.')
        return redirect('accounts:otp_verify')

    return render(request, 'accounts/auth.html', {
        'page': 'otp_request',
        'otp_cooldown': otp_cooldown
    })


def otp_verify_view(request):
    phone = request.session.get('otp_phone')

    if not phone:
        messages.error(request, 'ابتدا درخواست کد بدهید.')
        return redirect('accounts:otp_request')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()

        otp = OTPCode.objects.filter(
            phone=phone,
            code=code,
            is_used=False
        ).order_by('-created_at').first()

        if not otp:
            messages.error(request, 'کد وارد شده نامعتبر است.')
            return render(request, 'accounts/auth.html', {
                'page': 'otp_verify'
            })

        expire_minutes = 2
        if timezone.now() > otp.created_at + timedelta(minutes=expire_minutes):
            messages.error(request, 'کد منقضی شده است.')
            return redirect('accounts:otp_request')

        otp.is_used = True
        otp.save()

        user = User.objects.filter(phone=phone).first()
        if not user:
            messages.error(request, 'کاربر یافت نشد.')
            return redirect('accounts:otp_request')

        login(request, user)
        request.session.pop('otp_phone', None)
        messages.success(request, 'با موفقیت وارد شدید.')
        return redirect('home')

    return render(request, 'accounts/auth.html', {
        'page': 'otp_verify'
    })


@login_required
def dashboard_index(request):
    user = request.user
    active_tab = request.GET.get('tab', 'dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit_profile':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.save()

            messages.success(request, 'مشخصات شما با موفقیت بروزرسانی شد.')
            return redirect(f"{request.path}?tab=dashboard")

        elif action == 'create_workshop':
            name = request.POST.get('name', '').strip()
            national_code = request.POST.get('national_code', '').strip()
            address = request.POST.get('address', '').strip()

            if not name:
                messages.error(request, 'نام ورکشاپ الزامی است.')
                return redirect(f"{request.path}?tab=dashboard")

            workshop = Workshop.objects.create(
                owner=user,
                name=name,
                national_code=national_code if national_code else None,
                address=address if address else None,
            )

            WorkshopMembership.objects.create(
                workshop=workshop,
                user=user,
                role='owner',
                is_active=True
            )

            messages.success(request, f'ورکشاپ "{workshop.name}" با موفقیت ایجاد شد.')
            return redirect(f"{request.path}?tab=dashboard")

    workshop_memberships = (
        WorkshopMembership.objects
        .select_related('workshop')
        .filter(user=user, is_active=True)
        .order_by('-joined_at')
    )

    user_memberships = None

    if active_tab == 'users':
        user_memberships = (
            WorkshopMembership.objects
            .select_related('user', 'workshop')
            .filter(workshop__owner=user)
            .order_by('workshop__name', 'user__first_name', 'user__last_name')
        )

    context = {
        'workshop_memberships': workshop_memberships,
        'user_memberships': user_memberships,
        'active_tab': active_tab,
    }
    return render(request, 'dashboard/index.html', context)
