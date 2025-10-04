from django.urls import path
from .views import scan_domain

urlpatterns = [
    path("scan/", scan_domain, name="scan_domain"),
]
