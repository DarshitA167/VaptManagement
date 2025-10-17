from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.scan_ssl, name="scan_ssl"),  # your main scanner
    path("history/", views.get_scan_history, name="ssl_scan_history"),
]
