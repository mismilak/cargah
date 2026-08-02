from django.urls import path

from .views import (
    register_view,
    login_view,
    logout_view,
    otp_request_view,
    otp_verify_view,
    dashboard_index, edit_workshop_view, send_workshop_deactivation_code_view, confirm_workshop_deactivation_view
)

app_name = 'accounts'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('otp/request/', otp_request_view, name='otp_request'),
    path('otp/verify/', otp_verify_view, name='otp_verify'),
    path('dashboard/', dashboard_index, name='dashboard'),

    path('workshops/<int:workshop_id>/edit/', edit_workshop_view, name='edit_workshop'),
    path('workshops/<int:workshop_id>/deactivate/send-code/', send_workshop_deactivation_code_view,
         name='send_workshop_deactivation_code'),
    path('workshops/<int:workshop_id>/deactivate/confirm/', confirm_workshop_deactivation_view,
         name='confirm_workshop_deactivation'),

]
