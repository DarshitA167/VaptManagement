from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.scan_domain, name="scan_domain"),
    path("past/", views.past_scans, name="past_scans"),
]
