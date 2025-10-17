from django.db import models

class APIScan(models.Model):
    target = models.URLField()
    name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=50, default="pending")
    results = models.JSONField(default=list, blank=True)
    progress = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name or str(self.id)
