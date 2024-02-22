from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login-with-otp/', views.login_with_otp, name='login_with_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),

    #anonymouse side
    path('report_violence/', views.report_violence_view, name='report violence'),
    path('impact-victim-survivor/', views.impact_victim_view, name='impact victim'),
    path('behalf-victim-survivor/', views.behalf_victim_view, name='behalf impact victim'),
    path('add-case/', views.add_case, name='add_case'),

    #super admin side
    path('admin-vawc/dashboard/', views.admin_dashboard_view, name='admin dashboard'),
    path('admin-vawc/graph-report/', views.admin_graph_view, name='admin graph'),

    #barangay admin side
    path('admin-barangay-vawc/dashboard/', views.barangay_dashboard_view, name='barangay dashboard'),
    path('admin-barangay-vawc/settings/', views.barangay_settings_view, name='barangay settings'),

    path('add_status/<int:case_id>/', views.add_status, name='add_status'),
    path('edit_status/<int:status_id>/', views.edit_status, name='edit_status'),
    path('delete_status/<int:status_id>/', views.delete_status, name='delete_status'),
    
    path('admin-barangay-vawc/case/', views.barangay_case_view, name='barangay case'),
    path('admin-barangay-vawc/view-case/<int:case_id>/', views.view_case, name='barangay case view'),

    path('save_victim_data/<int:victim_id>/', views.save_victim_data, name='save_victim_data'),
    path('add_new_victim_data/', views.add_new_victim, name='add_new_victim'),
    path('delete_victim_data/', views.delete_victim, name='delete_victim'),
    path('add_new_perpetrator_data/', views.add_new_perpetrator, name='add_new_perpetrator'),
    path('save_perpetrator_data/<int:perpetrator_id>/', views.save_perpetrator_data, name='save_perpetrator_data'),
    path('delete_perpetrator_data/', views.delete_perpetrator, name='delete_perpetrator'),
    path('process_incident_form/', views.process_incident_form, name='process_incident_form'),
    

    path('admin-barangay-vawc/parent_victim/<int:case_id>/<int:victim_id>/', views.add_parent_view, name='add_parent'),
    path('save_parent_data/<int:parent_id>/', views.save_parent_data, name='save_parent_data'),
    path('add_new_parent_data/', views.add_new_parent_form, name='add_new_parent_form'),
    path('check_parent_count/', views.check_parent_count, name='check_parent_count'),
    path('delete_parent_data/', views.delete_parent, name='delete_parent'),
    
    path('admin-barangay-vawc/parent_perpetrator/<int:case_id>/<int:perp_id>/', views.add_parent_perp_view, name='add_parent_perp'),
    path('add_new_parent_perp_data/', views.add_new_parent_perp_form, name='add_new_parent_perp_form'),
    path('save_parent_perp_data/<int:parent_id>/', views.save_parent_perp_data, name='save_parent_perp_data'),
    path('delete_parent_perp_data/', views.delete_parent_perp, name='delete_parent_perp'),

    path('tite/', views.tite, name='tite')
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)