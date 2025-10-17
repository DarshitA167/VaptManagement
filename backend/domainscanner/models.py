from django.db import models

class DomainScan(models.Model):
    domain = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    results = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.domain} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
