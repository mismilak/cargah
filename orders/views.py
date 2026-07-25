# orders/views.py
from django.shortcuts import render


def home(request):
    return render(request, 'home.html')


def orders_page(request):
    return render(request, "dashboard/orders.html", {"active_tab": "orders"})


def processes_page(request):
    return render(request, "dashboard/processes.html", {"active_tab": "processes"})


def settlement_page(request):
    return render(request, "dashboard/settlement.html", {"active_tab": "settlement"})


def reports_page(request):
    return render(request, "dashboard/reports.html", {"active_tab": "reports"})


def settings_page(request):
    return render(request, "dashboard/settings.html", {"active_tab": "settings"})
