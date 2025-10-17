# backend/webappscanner/urls.py

from django.urls import path
from .views import run_zap_scan, scan_status, download_pdf_report, scan_history

urlpatterns = [
    path("scan/", run_zap_scan, name="webapp-scan"),
    path("status/<str:scan_id>/", scan_status, name="webapp-scan-status"),
    path("download-pdf/<str:scan_id>/", download_pdf_report, name="webapp-download-pdf"),
    path("history/", scan_history, name="webapp-scan-history"),
]
