# backend/webappscanner/urls.py
from django.urls import path
from .views import run_zap_scan, scan_status, download_pdf_report

urlpatterns = [
    path("scan/", run_zap_scan, name="webapp-scan"),
    path("status/<str:scan_id>/", scan_status, name="webapp-scan-status"),
    path("download-pdf/<str:scan_id>/", download_pdf_report, name="webapp-download-pdf"),
]
