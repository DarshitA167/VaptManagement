from django.urls import path
from .views import scan_network, download_pdf_report, get_scan_history, past_network_scans

urlpatterns = [
    path("scan/", scan_network, name="scan_network"),
    path("download-pdf/<int:scan_id>/", download_pdf_report, name="download_pdf_report"),  # require scan_id
    path("history/", get_scan_history, name="get_scan_history"),
    path("past/", past_network_scans, name="past_network_scans"),
]

