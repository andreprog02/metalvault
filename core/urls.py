from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.login_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    # Password Reset
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        success_url="/password-reset/done/",
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html",
    ), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
        success_url="/password-reset/complete/",
    ), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html",
    ), name="password_reset_complete"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("inventory/", views.inventory, name="inventory"),
    # Metals (Joias)
    path("metals/new/", views.metal_create, name="metal_create"),
    path("metals/<uuid:pk>/", views.metal_detail, name="metal_detail"),
    path("metals/<uuid:pk>/edit/", views.metal_edit, name="metal_edit"),
    path("metals/<uuid:pk>/delete/", views.metal_delete, name="metal_delete"),
    # Coins (Moedas)
    path("coins/new/", views.coin_create, name="coin_create"),
    path("coins/<uuid:pk>/", views.coin_detail, name="coin_detail"),
    path("coins/<uuid:pk>/edit/", views.coin_edit, name="coin_edit"),
    path("coins/<uuid:pk>/delete/", views.coin_delete, name="coin_delete"),
    # Banknotes
    path("banknotes/new/", views.banknote_create, name="banknote_create"),
    path("banknotes/<uuid:pk>/edit/", views.banknote_edit, name="banknote_edit"),
    path("banknotes/<uuid:pk>/delete/", views.banknote_delete, name="banknote_delete"),
    # Locations
    path("locations/", views.locations, name="locations"),
    path("locations/new/", views.location_create, name="location_create"),
    path("locations/<uuid:pk>/edit/", views.location_edit, name="location_edit"),
    path("locations/<uuid:pk>/delete/", views.location_delete, name="location_delete"),
    # IRPF
    path("irpf/", views.irpf_report, name="irpf_report"),
    path("irpf/<str:source>/<uuid:pk>/edit/", views.irpf_edit, name="irpf_edit"),
    path("irpf/export-csv/", views.irpf_export_csv, name="irpf_export_csv"),
    # API
    path("api/quotes/", views.api_quotes, name="api_quotes"),
    path("api/valuation/", views.api_valuation, name="api_valuation"),
    path("api/purchase-vs-market/", views.api_purchase_vs_market, name="api_purchase_vs_market"),
    path("api/countries/", views.api_countries, name="api_countries"),
]