from django.urls import path
from .views import diagnose_disease
from .views import ScanHistoryListView, ScanHistoryCreateView
from .views import password_entries, password_entry_detail

urlpatterns = [
    path("diagnose/", diagnose_disease, name="diagnose-disease"),
    path('history/', ScanHistoryListView.as_view(), name='scan-history'),
    path('history/create/', ScanHistoryCreateView.as_view(), name='scan-history-create'),
    path('passwords/', password_entries, name='password-list-create'),
    path('passwords/<int:pk>/', password_entry_detail, name='password-edit-delete'),
]
