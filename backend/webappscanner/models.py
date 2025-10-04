from django.db import models

class WebAppScanResult(models.Model):
    scan_id = models.CharField(max_length=100, unique=True)
    target = models.URLField()
    alert = models.CharField(max_length=255)
    risk = models.CharField(max_length=50)
    confidence = models.CharField(max_length=50, blank=True, null=True)
    url = models.TextField()
    param = models.CharField(max_length=255, blank=True, null=True)
    cweid = models.CharField(max_length=50, blank=True, null=True)
    wascid = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    solution = models.TextField(blank=True, null=True)
    reference = models.TextField(blank=True, null=True)
    evidence = models.TextField(blank=True, null=True)
    suggestion = models.TextField(blank=True, null=True)  # ✅ New column

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scan_id} - {self.alert}"
    