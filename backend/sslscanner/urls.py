from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.scan_ssl, name="scan_ssl"),
]
