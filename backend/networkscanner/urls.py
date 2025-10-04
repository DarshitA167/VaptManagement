from django.urls import path
from .views import scan_network, download_pdf_report

urlpatterns = [
    path("scan/", scan_network, name="scan_network"),
    path("download-pdf/", download_pdf_report, name="download_pdf_report"),
]
