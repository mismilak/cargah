# orders/views.py
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from accounts.models import Workshop, WorkshopMembership
from billing.models import Payment, Invoice
from .forms import ReceptionForm, CustomerCreateForm
from .models import Customer, Order, OrderRelease
from .models import OrderAttachment
from django.db.models import Prefetch
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


def home(request):
    return render(request, 'home.html')


ROLE_TAB_ACCESS = {
    'owner': ['reception', 'technical', 'accounting', 'delivery', 'management'],
    'management': ['reception', 'technical', 'accounting', 'delivery', 'management'],
    'technical': ['technical'],
    'accounting': ['accounting'],
    'reception': ['reception'],
    'delivery': ['delivery'],
    'operator': ['technical'],
}


def _get_workshop_and_membership(request, workshop_id, required_tab):
    """
    فقط permission check. هیچ کوئری‌ای روی Order اینجا زده نمی‌شود.
    """
    workshop = get_object_or_404(Workshop, pk=workshop_id)
    membership = get_object_or_404(
        WorkshopMembership,
        workshop=workshop,
        user=request.user,
        is_active=True
    )
    allowed_tabs = ROLE_TAB_ACCESS.get(membership.role, [])
    if required_tab not in allowed_tabs:
        raise Http404("دسترسی به این تب مجاز نیست")
    return workshop, membership, allowed_tabs


def _base_context(workshop, membership, allowed_tabs, active_tab):
    return {
        'workshop': workshop,
        'membership': membership,
        'allowed_tabs': allowed_tabs,
        'active_tab': active_tab,
    }


@login_required
def dashboard_redirect(request, workshop_id):
    """
    ورودی اصلی داشبورد. کاربر را به اولین تب مجازش هدایت می‌کند.
    هیچ کوئری Order اینجا نیست.
    """
    workshop = get_object_or_404(Workshop, pk=workshop_id)
    membership = get_object_or_404(
        WorkshopMembership,
        workshop=workshop,
        user=request.user,
        is_active=True
    )
    allowed_tabs = ROLE_TAB_ACCESS.get(membership.role, [])
    if not allowed_tabs:
        raise Http404("دسترسی به هیچ تبی ندارید")

    return redirect('orders:tab_' + allowed_tabs[0], workshop_id=workshop_id)


# management tab

from django.template.defaultfilters import register


@register.filter
def intcomma_fa(value):
    """اضافه کردن جداکننده هزارگان فارسی"""
    try:
        value = int(value)
        return f"{value:,}".replace(',', '،')
    except (ValueError, TypeError):
        return value


@login_required
def management_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'management'
    )

    if request.method == 'POST':
        from .forms import ServiceTypeForm
        form = ServiceTypeForm(request.POST)
        if form.is_valid():
            svc = form.save(commit=False)
            svc.workshop = workshop
            svc.save()
            return redirect('orders:management', workshop_id=workshop_id)
    else:
        from .forms import ServiceTypeForm
        form = ServiceTypeForm()

    status_counts = dict(
        Order.objects.filter(workshop=workshop)
        .values_list('status')
        .annotate(c=Count('id'))
    )
    total_orders = sum(status_counts.values())
    total_customers = Customer.objects.filter(workshop=workshop).count()
    service_types = ServiceType.objects.filter(workshop=workshop).order_by('-created_at')
    orders_list = (
        Order.objects.filter(
            workshop=workshop,
            status__in=['management', 'done'],
            is_archived=False,
            is_stopped=False,
        ).select_related('customer').order_by('-created_at')
    )
    archived_orders = (
        Order.objects.filter(workshop=workshop, is_archived=True)
        .select_related('customer').order_by('-created_at')
    )
    stopped_orders = (
        Order.objects.filter(workshop=workshop, is_stopped=True, is_archived=False)
        .select_related('customer').order_by('-created_at')
    )
    context = _base_context(workshop, membership, allowed_tabs, 'management')
    context.update({
        'form': form,
        'workshop_id': workshop.id,
        'status_counts': status_counts,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'service_types': service_types,
        'orders_list': orders_list,
        'archived_orders': archived_orders,
        'stopped_orders': stopped_orders,
    })
    return render(request, 'orders/management_tab.html', context)


@login_required
@require_POST
def service_edit(request, workshop_id, service_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'management')
    svc = get_object_or_404(ServiceType, pk=service_id, workshop=workshop)
    from .forms import ServiceTypeForm
    form = ServiceTypeForm(request.POST, instance=svc)
    if form.is_valid():
        form.save()
        return redirect('orders:management', workshop_id=workshop_id)
    return redirect('orders:management', workshop_id=workshop_id)


@login_required
@require_POST
def service_delete(request, workshop_id, service_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'management')
    svc = get_object_or_404(ServiceType, pk=service_id, workshop=workshop)
    svc.delete()
    return redirect('orders:management', workshop_id=workshop_id)


@login_required
def order_detail(request, workshop_id, order_id):
    order = get_object_or_404(Order, id=order_id, workshop_id=workshop_id)

    activities = list(order.activities.select_related('service').values(
        'id',
        'service__name',
        'service__machine_name',
        'duration_value',
        'service__unit',
        'price',
        'notes',
        'created_at'
    ))

    unit_dict = dict(ServiceType.UNIT_CHOICES)
    for act in activities:
        act['service__unit'] = unit_dict.get(act['service__unit'], act['service__unit'])
        act['created_at'] = act['created_at'].strftime('%Y/%m/%d') if act['created_at'] else ''

    attachments = []
    for att in order.attachments.all():
        name = att.file.name
        ext = name.split('.')[-1].lower()

        if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            kind = 'image'
        elif ext == 'pdf':
            kind = 'pdf'
        else:
            kind = 'file'

        attachments.append({
            'name': name,
            'url': att.file.url,
            'kind': kind,
        })

    invoices = Invoice.objects.filter(order=order)
    payments_qs = Payment.objects.filter(invoice__in=invoices).order_by('-created_at')

    payments_data = []
    total_paid = 0

    for p in payments_qs:
        amount_int = int(p.amount)
        total_paid += amount_int

        payments_data.append({
            'amount': f"{amount_int:,}",
            'amount_raw': amount_int,
            'method': p.get_method_display(),
            'paid_at': p.paid_at.strftime('%Y/%m/%d') if p.paid_at else '',
            'check_status': p.get_check_status_display() if p.method == 'check' and p.check_status else None,
        })

    total_activities_amount = sum(int(act['price']) * int(act['duration_value']) for act in activities)
    balance = total_activities_amount - total_paid

    if balance > 0:
        debt_status = 'بدهکار'
    elif balance < 0:
        debt_status = 'بستانکار'
    else:
        debt_status = 'تسویه'

    return JsonResponse({
        'code': order.code,
        'customer_name': order.customer.name,
        'customer_phone': order.customer.phone,
        'customer_workshop_name': order.customer.customer_workshop_name,
        'status': order.get_status_display(),
        'created_at': order.created_at.strftime('%Y/%m/%d'),
        'created_by': str(order.created_by) if order.created_by else '—',
        'description': order.description,
        'activities': activities,
        'attachments': attachments,
        'is_stopped': order.is_stopped,
        'is_archived': order.is_archived,
        'payments': payments_data,
        'financial_summary': {
            'total_amount': f"{total_activities_amount:,}",
            'total_paid': f"{total_paid:,}",
            'balance': f"{abs(balance):,}",
            'balance_raw': balance,
            'debt_status': debt_status,
        }
    })


@require_POST
@login_required
def order_action(request, workshop_id, order_id):
    order = get_object_or_404(Order, id=order_id, workshop_id=workshop_id)
    action = request.POST.get('action')
    status_actions = {'reception', 'technical', 'accounting', 'done', 'release'}
    if action in status_actions:
        order.status = action
        order.is_stopped = False
        order.is_archived = False
        order.save(update_fields=['status', 'is_stopped', 'is_archived', 'updated_at'])
    elif action == 'stop':
        order.is_stopped = True
        order.is_archived = False
        order.save(update_fields=['is_stopped', 'is_archived', 'updated_at'])
    elif action == 'archive':
        order.is_archived = True
        order.is_stopped = False
        order.save(update_fields=['is_archived', 'is_stopped', 'updated_at'])

    return redirect('orders:management', workshop_id=workshop_id)



@login_required
def edit_activities_bulk(request, workshop_id, order_id):
    if request.method != 'POST':
        return redirect('orders:management', workshop_id)

    order = get_object_or_404(Order, id=order_id, workshop_id=workshop_id)

    activity_ids = request.POST.getlist('activity_id')
    activities = {
        str(act.id): act
        for act in OrderActivity.objects.filter(
            order=order,
            id__in=activity_ids
        )
    }

    for activity_id in activity_ids:
        act = activities.get(str(activity_id))
        if not act:
            continue

        duration = request.POST.get(f'duration_value_{activity_id}')
        price = request.POST.get(f'price_{activity_id}')

        if duration not in (None, ''):
            try:
                act.duration_value = Decimal(duration)
            except (InvalidOperation, TypeError):
                pass

        if price not in (None, ''):
            try:
                act.price = Decimal(price)
            except (InvalidOperation, TypeError):
                pass

        act.save()

    return redirect('orders:management', workshop_id)


# ---------------------------------------------------------------
# تب پذیرش — تنها ویویی که کوئری Order می‌زند + فرم ثبت پذیرش
# ---------------------------------------------------------------
@login_required
def reception_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'reception'
    )

    if request.method == 'POST':
        form = ReceptionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            customer = get_object_or_404(Customer, pk=cd['customer_id'], workshop=workshop)
            order = Order.objects.create(
                workshop=workshop,
                customer=customer,
                created_by=request.user,
                description=cd['description'],
                count_request=cd['count_request'],
                status='reception',
                created_by_id=request.user.id
            )

            for f in request.FILES.getlist('attachments'):
                OrderAttachment.objects.create(
                    order=order, file=f, title=f.name, uploaded_by=request.user
                )
            return redirect(request.path + '?success=1')

    orders = (
        Order.objects
        .filter(workshop=workshop, status='reception')
        .select_related('customer', 'created_by')
        .prefetch_related('attachments')
        .order_by('-created_at')
    )
    context = _base_context(workshop, membership, allowed_tabs, 'reception')
    context.update({'orders': orders, 'show_success': request.GET.get('success') == '1'})
    return render(request, 'orders/reception_tab.html', context)


@login_required
@require_GET
def customer_list(request, workshop_id):
    workshop = get_object_or_404(Workshop, pk=workshop_id)
    get_object_or_404(WorkshopMembership, workshop=workshop, user=request.user, is_active=True)
    q = request.GET.get('q', '')
    qs = Customer.objects.filter(workshop=workshop)
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(phone__icontains=q)
    data = list(qs.values('id', 'name', 'customer_workshop_name', 'phone', 'is_legal')[:50])
    return JsonResponse({'customers': data})


@login_required
@require_POST
def customer_create(request, workshop_id):
    workshop = get_object_or_404(Workshop, pk=workshop_id)
    get_object_or_404(WorkshopMembership, workshop=workshop, user=request.user, is_active=True)
    form = CustomerCreateForm(request.POST)
    if form.is_valid():
        customer = form.save(commit=False)
        customer.workshop = workshop
        customer.save()
        return JsonResponse({
            'id': customer.id,
            'name': customer.name,
            'customer_workshop_name': customer.customer_workshop_name,
            'phone': customer.phone,
            'is_legal': customer.is_legal,
        })
    return JsonResponse({'errors': form.errors}, status=400)


@login_required
@require_POST
def order_edit(request, workshop_id, order_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'reception')
    order = get_object_or_404(Order, pk=order_id, workshop=workshop, status='reception')
    order.description = request.POST.get('description', order.description)
    order.save(update_fields=['description'])
    for f in request.FILES.getlist('attachments'):
        OrderAttachment.objects.create(order=order, file=f, title=f.name, uploaded_by=request.user)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def order_delete(request, workshop_id, order_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'reception')
    order = get_object_or_404(Order, pk=order_id, workshop=workshop, status='reception')
    order.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def order_refer(request, workshop_id, order_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'reception')
    order = get_object_or_404(Order, pk=order_id, workshop=workshop, status='reception')
    unit = request.POST.get('unit')
    allowed = {'technical', 'accounting', 'delivery', 'management'}
    if unit not in allowed:
        return JsonResponse({'error': 'واحد نامعتبر'}, status=400)
    order.status = unit
    order.is_stopped = False
    order.is_archived = False
    order.save()
    order.save(update_fields=['status'])
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------
@login_required
def technical_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'technical'
    )

    orders = (
        Order.objects
        .filter(workshop=workshop, status='technical')
        .select_related('customer', 'created_by')
        .order_by('-created_at')
    )

    context = _base_context(workshop, membership, allowed_tabs, 'technical')
    context['orders'] = orders
    return render(request, 'orders/technical_tab.html', context)


from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Order, OrderActivity, ServiceType


@login_required
def order_activities_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, workshop__memberships__user=request.user)
    activities = order.activities.select_related('service').values(
        'id', 'service__id', 'service__name', 'duration_value', 'notes', 'price'  # اضافه شد: price
    )
    services = ServiceType.objects.filter(workshop=order.workshop)
    return JsonResponse({
        'order_code': order.code,
        'workshop_name': order.workshop.name,  # اضافه شد
        'order_info': {
            'code': order.code,
            'customer': order.customer.name,
            'phone': order.customer.phone,
            'created_by': str(order.created_by),
            'created_at': order.created_at.strftime('%Y/%m/%d'),
            'status': order.get_status_display(),
            'description': order.description or '—',
            'count_request': order.count_request,
            'prev_debt': str(order.customer.prev_debt) if hasattr(order.customer, 'prev_debt') else '0',
        },
        'activities': [
            {
                'id': a['id'],
                'service_id': a['service__id'],
                'service_name': a['service__name'],
                'duration_value': str(a['duration_value']),
                'price': str(a['price']),  # اضافه شد
                'notes': a['notes'],
            } for a in activities
        ],
        'services': list(services.values('id', 'name', 'unit'))
    })


@login_required
@require_http_methods(['POST'])
def activity_add_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, workshop__memberships__user=request.user)
    data = json.loads(request.body)
    service = get_object_or_404(ServiceType, id=data['service'], workshop=order.workshop)
    OrderActivity.objects.create(
        order=order,
        operator=request.user,
        service=service,
        duration_value=data.get('duration_value', 0),
        price=service.base_price,
        notes=data.get('notes', ''),
    )
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(['PUT'])
def activity_update_api(request, activity_id):
    activity = get_object_or_404(
        OrderActivity, id=activity_id,
        order__workshop__memberships__user=request.user
    )
    data = json.loads(request.body)
    if 'service' in data:
        service = get_object_or_404(ServiceType, id=data['service'], workshop=activity.order.workshop)
        activity.service = service
        activity.price = service.base_price
    activity.duration_value = data.get('duration_value', activity.duration_value)
    activity.notes = data.get('notes', activity.notes)
    activity.save()
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(['DELETE'])
def activity_delete_api(request, activity_id):
    activity = get_object_or_404(
        OrderActivity, id=activity_id,
        order__workshop__memberships__user=request.user
    )
    membership = activity.order.workshop.memberships.get(user=request.user)
    if membership.role not in ('owner', 'management'):
        return JsonResponse({'ok': False, 'error': 'دسترسی حذف ندارید.'}, status=403)

    activity.delete()
    return JsonResponse({'ok': True})


# order in modal
from django.conf import settings


@login_required
def order_attachments_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, workshop__memberships__user=request.user)
    attachments = order.attachments.select_related('uploaded_by').values(
        'id', 'file', 'title', 'uploaded_at', 'uploaded_by__username'
    )
    return JsonResponse({
        'attachments': [
            {
                'id': a['id'],
                'file_url': settings.MEDIA_URL + a['file'] if a['file'] else '',
                'title': a['title'] or (a['file'].split('/')[-1] if a['file'] else ''),
                'uploaded_at': a['uploaded_at'].strftime('%Y-%m-%d %H:%M'),
                'uploaded_by': a['uploaded_by__username'] or '-',
            } for a in attachments
        ]
    })


@login_required
def order_attachment_add_api(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    order = get_object_or_404(Order, id=order_id, workshop__memberships__user=request.user)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'فایلی ارسال نشده'}, status=400)
    attachment = OrderAttachment.objects.create(
        order=order,
        file=file,
        title=request.POST.get('title', ''),
        uploaded_by=request.user
    )
    return JsonResponse({'ok': True, 'id': attachment.id})


@login_required
def order_attachment_delete_api(request, attachment_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    attachment = get_object_or_404(
        OrderAttachment, id=attachment_id, order__workshop__memberships__user=request.user
    )
    membership = WorkshopMembership.objects.filter(
        user=request.user, workshop=attachment.order.workshop, is_active=True
    ).first()
    if not membership or membership.role not in ('owner', 'management'):
        return JsonResponse({'error': 'دسترسی ندارید'}, status=403)
    attachment.file.delete(save=False)
    attachment.delete()
    return JsonResponse({'ok': True})


def refer_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    target = request.POST.get('target_unit')
    if not target:
        return JsonResponse({'ok': False, 'error': 'واحد مقصد مشخص نشده'}, status=400)
    order.status = target
    order.is_stopped = False
    order.is_archived = False
    order.save()
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------
# در orders/views.py — آپدیت accounting_tab
@login_required
def accounting_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'accounting'
    )

    referred_orders = (
        Order.objects
        .filter(workshop=workshop, status='accounting')
        .select_related('customer', 'created_by')
        .order_by('-created_at')
    )

    manager_approved_orders = (
        Order.objects
        .filter(workshop=workshop, status='payment')
        .select_related('customer', 'created_by')
        .order_by('-created_at')
    )

    context = _base_context(workshop, membership, allowed_tabs, 'accounting')
    context['orders'] = referred_orders
    context['manager_approved_orders'] = manager_approved_orders
    return render(request, 'orders/accounting_tab.html', context)


# ---------------------------------------------------------------
@login_required
def delivery_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(request, workshop_id, 'delivery')

    # فیلترهای تب چهارم (لیست برگه ها)
    release_list = OrderRelease.objects.filter(order__workshop=workshop).select_related('order', 'order__customer')
    customer_id = request.GET.get('customer')
    order_code = request.GET.get('order_code')
    rel_num = request.GET.get('rel_num')

    if customer_id: release_list = release_list.filter(order__customer_id=customer_id)
    if order_code: release_list = release_list.filter(order__code__icontains=order_code)
    if rel_num: release_list = release_list.filter(release_number__icontains=rel_num)

    all_orders = Order.objects.filter(workshop=workshop, status='release')
    print(all_orders)
    ready_orders = []  # بدون بدهی، بدون ترخیص قبلی
    partial_orders = []  # بدون بدهی، دارای مانده
    manager_orders = []  # بدهکار ولی دارای تاییدیه manager_release_allowed

    for o in all_orders:
        debt = o.customer.total_debt
        released = o.total_released_count

        if debt > 0:
            if o.manager_release_allowed and o.manager_release_count > 0:
                manager_orders.append(o)
        else:
            if released == 0:
                ready_orders.append(o)
            elif o.remaining_release_count > 0:
                partial_orders.append(o)

    context = _base_context(workshop, membership, allowed_tabs, 'delivery')
    print(manager_orders)
    print(ready_orders)
    print(partial_orders)
    context.update({
        'ready_orders': ready_orders,
        'partial_orders': partial_orders,
        'manager_orders': manager_orders,
        'releases': release_list,
        'customers': Customer.objects.filter(workshop=workshop)
    })
    return render(request, 'orders/delivery_tab.html', context)



@require_POST
@login_required
@transaction.atomic
def process_release(request, workshop_id, order_id):
    order = get_object_or_404(Order, id=order_id, workshop_id=workshop_id)
    count = int(request.POST.get('count', 0))
    is_manager_path = request.POST.get('is_manager') == 'true'

    # چک کردن بدهی (مگر اینکه از مسیر مدیر تایید شده باشد)
    if order.customer.total_debt > 0 and not is_manager_path:
        messages.error(request, "مشتری بدهکار است. ترخیص فقط با دستور مدیر ممکن است.")
        return redirect('orders:delivery_tab', workshop_id)

    # چک کردن تعداد مجاز
    limit = order.manager_release_count if is_manager_path else order.remaining_release_count
    if count > limit or count <= 0:
        messages.error(request, f"تعداد نامعتبر (حداکثر مجاز: {limit})")
        return redirect('orders:delivery_tab', workshop_id)

    # ثبت ترخیص
    OrderRelease.objects.create(
        order=order,
        count=count,
        released_by=request.user,
        is_manager_ordered=is_manager_path
    )

    # ریست کردن وضعیت مدیر در صورت استفاده
    if is_manager_path:
        order.manager_release_allowed = False
        order.manager_release_count = 0
        order.save()

    messages.success(request, "برگه ترخیص صادر شد.")
    return redirect('orders:delivery_tab', workshop_id)
