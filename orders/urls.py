# orders/urls.py
from django.urls import path
from .views import (
    orders_page,
    processes_page,
    settlement_page,
    reports_page,
    settings_page,
    home,
)

urlpatterns = [
    path('', home, name='home'),
    path("dashboard/orders/", orders_page, name="orders_page"),
    path("dashboard/processes/", processes_page, name="processes_page"),
    path("dashboard/settlement/", settlement_page, name="settlement_page"),
    path("dashboard/reports/", reports_page, name="reports_page"),
    path("dashboard/settings/", settings_page, name="settings_page"),
]
