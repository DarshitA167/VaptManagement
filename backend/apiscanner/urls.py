from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.start_api_scan, name="api-scan-start"),
    path("status/<int:scan_id>/", views.scan_status, name="api-scan-status"),
    path("results/<int:scan_id>/", views.scan_results, name="api-scan-results"),
    path("download-pdf/<int:scan_id>/", views.download_pdf_report, name="api-scan-download-pdf"),
    path("past-scans/", views.past_scans, name="api-past-scans"),
]
