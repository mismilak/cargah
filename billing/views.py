from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from billing.models import Invoice
from orders.models import Order
from orders.views import _get_workshop_and_membership


@login_required
def manager_approve_invoice(request, workshop_id, order_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method not allowed'}, status=405)

    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'management')
    order = get_object_or_404(Order, id=order_id, workshop=workshop)

    from django.db.models import Sum, F, ExpressionWrapper, DecimalField
    total = order.activities.aggregate(
        total=Sum(ExpressionWrapper(F('duration_value') * F('price'), output_field=DecimalField()))
    )['total'] or Decimal('0')

    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={
            'total_amount': total,
            'final_amount': total,
            'confirmed_by_manager': True,
            'confirmed_by_manager_date_time': timezone.now(),
        }
    )
    if not created:
        invoice.confirmed_by_manager = True
        invoice.confirmed_by_manager_date_time = timezone.now()
        invoice.total_amount = total
        invoice.final_amount = total
        invoice.save(
            update_fields=['confirmed_by_manager', 'confirmed_by_manager_date_time', 'total_amount', 'final_amount']
        )

    order.status = 'payment'
    order.save(update_fields=['status'])

    return JsonResponse({'ok': True})


# billing/views.py

@login_required
def order_invoice_detail(request, workshop_id, order_id):
    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'accounting')
    order = get_object_or_404(Order, id=order_id, workshop=workshop)

    try:
        invoice = order.invoice
    except Invoice.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'فاکتوری برای این سفارش ثبت نشده است'})

    payments = invoice.payments.all().order_by('-paid_at')
    payments_data = [
        {
            'id': p.id,
            'method': p.get_method_display(),
            'amount': str(p.amount),
            'paid_at': p.paid_at.strftime('%Y-%m-%d'),
            'check_status': p.get_check_status_display() if p.method == 'check' else None,
            'notes': p.notes,
        }
        for p in payments
    ]

    return JsonResponse({
        'ok': True,
        'invoice_id': invoice.id,
        'total_amount': str(invoice.total_amount),
        'discount': str(invoice.discount),
        'final_amount': str(invoice.final_amount),
        'paid_amount': str(invoice.paid_amount),
        'remaining_amount': str(invoice.remaining_amount),
        'status': invoice.status,
        'status_display': invoice.get_status_display(),
        'confirmed_by_manager': invoice.confirmed_by_manager,
        'payments': payments_data,
    })


@login_required
def create_payment(request, workshop_id, invoice_id):
    from billing.models import Invoice, Payment
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    workshop, membership, _ = _get_workshop_and_membership(request, workshop_id, 'accounting')
    invoice = get_object_or_404(Invoice, id=invoice_id, order__workshop=workshop)

    method = request.POST.get('method')
    amount = request.POST.get('amount')
    paid_at = request.POST.get('paid_at')
    notes = request.POST.get('notes', '')

    p = Payment(
        invoice=invoice,
        method=method,
        amount=amount,
        paid_at=paid_at,
        recorded_by=request.user,
        notes=notes,
    )
    if method == 'check':
        p.check_number = request.POST.get('check_number', '')
        p.check_bank = request.POST.get('check_bank', '')
        p.check_due_date = request.POST.get('check_due_date') or None
        p.check_status = request.POST.get('check_status', 'pending')
    p.save()

    return JsonResponse({
        'ok': True,
        'paid_amount': str(invoice.paid_amount),
        'remaining_amount': str(invoice.remaining_amount),
        'status': invoice.get_status_display(),
    })
