# billing/urls.py
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('<int:workshop_id>/order/<int:order_id>/manager-approve/', views.manager_approve_invoice,
         name='manager_approve_invoice'),
    path('<int:workshop_id>/order/<int:order_id>/invoice-detail/', views.order_invoice_detail,
         name='order_invoice_detail'),
    path('<int:workshop_id>/invoice/<int:invoice_id>/payment/', views.create_payment, name='create_payment'),
    path('<int:workshop_id>/payment/<int:payment_id>/check-status/', views.update_check_status,
         name='update_check_status'),
]
