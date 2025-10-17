from django.db import models

class NetworkScan(models.Model):
    ip = models.CharField(max_length=255)
    ports = models.CharField(max_length=50)
    results = models.JSONField(default=list)  # or alerts = models.JSONField(default=list)
    url = models.URLField(default="")  # <- Set default here
    status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
