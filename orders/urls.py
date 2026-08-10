# orders/urls.py
from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.home, name='home'),
    path('workshop/<int:workshop_id>/', views.dashboard_redirect, name='dashboard'),
    path('workshop/<int:workshop_id>/reception/', views.reception_tab, name='tab_reception'),
    path('workshop/<int:workshop_id>/technical/', views.technical_tab, name='tab_technical'),
    path('workshop/<int:workshop_id>/accounting/', views.accounting_tab, name='tab_accounting'),
    path('workshop/<int:workshop_id>/delivery/', views.delivery_tab, name='tab_delivery'),
    path('workshop/<int:workshop_id>/customers/', views.customer_list, name='customer_list'),
    path('workshop/<int:workshop_id>/customers/create/', views.customer_create, name='customer_create'),

    path('<int:workshop_id>/orders/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('<int:workshop_id>/orders/<int:order_id>/delete/', views.order_delete, name='order_delete'),
    path('<int:workshop_id>/orders/<int:order_id>/refer/', views.order_refer, name='order_refer'),
    path('<int:workshop_id>/orders/<int:order_id>/detail/', views.order_detail, name='order_detail'),

    path('<int:workshop_id>/management/', views.management_tab, name='management'),
    path('<int:workshop_id>/tab/management/', views.management_tab, name='tab_management'),
    path('orders/<int:workshop_id>/management/delete/<int:service_id>/', views.service_delete, name='service_delete'),
    path('orders/<int:workshop_id>/management/edit/<int:service_id>/', views.service_edit, name='service_edit'),
    path('orders/<int:workshop_id>/order/detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:workshop_id>/order/action/<int:order_id>/', views.order_action, name='order_action'),
    path('<int:workshop_id>/order/<int:order_id>/activities/edit/',
         views.edit_activities_bulk, name='edit_activities_bulk'),

    path('orders/api/order/<int:order_id>/activities/', views.order_activities_api, name='order-activities-api'),
    path('orders/api/order/<int:order_id>/activity/add/', views.activity_add_api, name='activity-add-api'),
    path('orders/api/activity/<int:activity_id>/update/', views.activity_update_api, name='activity-update-api'),
    path('orders/api/activity/<int:activity_id>/delete/', views.activity_delete_api, name='activity-delete-api'),
    #     order in modal technical section
    path('orders/api/order/<int:order_id>/attachments/', views.order_attachments_api, name='order_attachments_api'),
    path('orders/api/order/<int:order_id>/attachment/add/', views.order_attachment_add_api,
         name='order_attachment_add_api'),
    path('orders/api/attachment/<int:attachment_id>/delete/', views.order_attachment_delete_api,
         name='order_attachment_delete_api'),
    path('orders/api/order/<int:order_id>/refer/', views.refer_order, name='refer_order'),

]
