# billing/utils.py
def get_debtors(workshop):
    return Invoice.objects.filter(
        order__workshop=workshop,
        status__in=['unpaid', 'partial'],
        released=True
    ).select_related('order__customer')
