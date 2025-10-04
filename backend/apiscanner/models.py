import uuid
from django.db import models

class APIScan(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("finished", "Finished"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress = models.JSONField(default=list, blank=True)   # list of {"stage": "...", "status":"..."}
    results = models.JSONField(default=list, blank=True)    # list of vulnerability dicts
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"APIScan {self.id} - {self.target} - {self.status}"
