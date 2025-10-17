from django.db import models

class SSLScan(models.Model):
    domain = models.CharField(max_length=255)
    scan_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)
    expiry_date = models.CharField(max_length=100, null=True, blank=True)
    issuer = models.CharField(max_length=255, null=True, blank=True)
    tls_version = models.CharField(max_length=100, null=True, blank=True)
    pdf_report = models.TextField(null=True, blank=True)
    result_json = models.JSONField(null=True, blank=True)  # <-- built-in JSONField

    def __str__(self):
        return f"{self.domain} ({self.scan_date.strftime('%Y-%m-%d %H:%M:%S')})"
