from django.urls import path

from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('business/', views.business_form, name='business_form'),
    path('business/page/', views.business_page_form, name='business_page_form'),
    path('business/whatsapp/', views.whatsapp_settings, name='whatsapp_settings'),
    path('business/whatsapp/validate/', views.whatsapp_validate, name='whatsapp_validate'),
    path('services/', views.service_list, name='service_list'),
    path('services/new/', views.service_form, name='service_create'),
    path('services/<int:service_id>/edit/', views.service_form, name='service_edit'),
    path('services/<int:service_id>/toggle/', views.service_toggle, name='service_toggle'),
    path('working-hours/', views.working_hours, name='working_hours'),
    path('book/<slug:slug>/', views.public_booking, name='public_services'),
    path('book/<slug:slug>/service/<int:service_id>/', views.public_booking, name='public_booking'),
    path('appointments/cancel/<uuid:token>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:appointment_id>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    path('appointments/<int:appointment_id>/status/<str:status>/', views.appointment_update_status, name='appointment_update_status'),
    path('signup/', views.signup, name='signup'),
]