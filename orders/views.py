# orders/views.py

import os

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from accounts.models import Workshop, WorkshopMembership
from .forms import ReceptionForm, CustomerCreateForm
from .models import OrderAttachment


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


from django.db.models import Count
from .models import Customer


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
            return redirect(request.path + '?created=1')
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

    context = _base_context(workshop, membership, allowed_tabs, 'management')
    context.update({
        'form': form,
        'status_counts': status_counts,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'service_types': service_types,
        'show_created': request.GET.get('created') == '1',
    })
    return render(request, 'orders/management_tab.html', context)


@login_required
@require_POST
def service_edit(request, workshop_id, service_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'management')
    svc = get_object_or_404(ServiceType, pk=service_id, workshop=workshop)
    svc.name = request.POST.get('name')
    svc.machine_name = request.POST.get('machine_name')
    svc.unit = request.POST.get('unit')
    svc.base_price = request.POST.get('base_price')
    svc.save()
    return JsonResponse({
        'id': svc.id,
        'name': svc.name,
        'machine_name': svc.machine_name,
        'unit': svc.unit,
        'unit_display': svc.get_unit_display(),
        'base_price': int(svc.base_price),
        'created_at': svc.created_at.strftime('%Y/%m/%d')
    })


@login_required
@require_POST
def service_delete(request, workshop_id, service_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'management')
    svc = get_object_or_404(ServiceType, pk=service_id, workshop=workshop)
    svc.delete()
    return JsonResponse({'ok': True})


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
    allowed = {'technical', 'accounting', 'delivery'}
    if unit not in allowed:
        return JsonResponse({'error': 'واحد نامعتبر'}, status=400)
    order.status = unit
    order.save(update_fields=['status'])
    return JsonResponse({'ok': True})


@login_required
@require_GET
def order_detail(request, workshop_id, order_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'reception'
    )
    order = get_object_or_404(
        Order.objects.select_related('customer', 'created_by'),
        pk=order_id, workshop=workshop
    )

    attachments = []
    for att in order.attachments.all():
        ext = os.path.splitext(att.file.name)[1].lower().lstrip('.')
        if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            kind = 'image'
        elif ext == 'pdf':
            kind = 'pdf'
        else:
            kind = 'other'
        attachments.append({
            'url': att.file.url,
            'name': att.title or os.path.basename(att.file.name),
            'ext': ext,
            'kind': kind,
        })

    return JsonResponse({
        'code': order.code,
        'customer_name': order.customer.name,
        'customer_phone': order.customer.phone,
        'created_at': order.created_at.strftime('%Y/%m/%d %H:%M'),
        'created_by': str(order.created_by) if order.created_by else '—',
        'status': order.get_status_display(),
        'description': order.description or '—',
        'attachments': attachments,
    })


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


import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Order, OrderActivity, ServiceType


@login_required
def order_activities_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, workshop__memberships__user=request.user)
    activities = order.activities.select_related('service').values(
        'id', 'service__id', 'service__name', 'duration_value', 'notes'
    )
    services = ServiceType.objects.filter(workshop=order.workshop)
    return JsonResponse({
        'order_code': order.code,
        'activities': [
            {
                'id': a['id'],
                'service_id': a['service__id'],
                'service_name': a['service__name'],
                'duration_value': str(a['duration_value']),
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


# ---------------------------------------------------------------
@login_required
def accounting_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'accounting'
    )

    orders = (
        Order.objects
        .filter(workshop=workshop, status='accounting')
        .select_related('customer', 'created_by')
        .order_by('-created_at')
    )

    context = _base_context(workshop, membership, allowed_tabs, 'accounting')
    context['orders'] = orders
    return render(request, 'orders/accounting_tab.html', context)


# ---------------------------------------------------------------
@login_required
def delivery_tab(request, workshop_id):
    workshop, membership, allowed_tabs = _get_workshop_and_membership(
        request, workshop_id, 'delivery'
    )

    orders = (
        Order.objects
        .filter(workshop=workshop, status='done')
        .select_related('customer', 'created_by')
        .order_by('-updated_at')
    )

    context = _base_context(workshop, membership, allowed_tabs, 'delivery')
    context['orders'] = orders
    return render(request, 'orders/delivery_tab.html', context)
