# backend/webappscanner/models.py

from django.db import models

class WebAppScanResult(models.Model):
    """
    Each row represents a single alert detected by a scan run (or a placeholder row if a run had zero alerts).
    scan_id groups multiple alert rows together for the same run.
    """
    scan_id = models.CharField(max_length=200, db_index=True)
    target = models.URLField()
    alert = models.CharField(max_length=255, null=True, blank=True)
    risk = models.CharField(max_length=100, null=True, blank=True)
    confidence = models.CharField(max_length=100, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    param = models.CharField(max_length=255, null=True, blank=True)
    cweid = models.CharField(max_length=100, null=True, blank=True)
    wascid = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    solution = models.TextField(null=True, blank=True)
    reference = models.TextField(null=True, blank=True)
    evidence = models.TextField(null=True, blank=True)
    suggestion = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["scan_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.scan_id} - {self.alert or 'No alert'}"
