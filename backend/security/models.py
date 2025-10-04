from django.db import models
from django.contrib.auth.models import User


class ScanHistory(models.Model):
    SCAN_TYPES = (
        ('mental', 'Mental Health'),
        ('physical', 'Physical Health'),
        ('email', 'Email Breach & Phishing'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPES)
    input_data = models.TextField()  # JSON or string of what was submitted
    result_data = models.TextField()  # JSON or string of the result/response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.scan_type} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class DiagnosisHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    symptoms = models.TextField()
    result = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis by {self.user or 'Anonymous'} at {self.timestamp}"




class PasswordEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    password = models.TextField()  # Encrypt later
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_name}"



class MentalAssessment(models.Model):
    user_id = models.IntegerField()  # Replace with ForeignKey if using user model
    summary = models.TextField()
    recommendations = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mental Assessment for User {self.user_id} on {self.created_at.strftime('%Y-%m-%d')}"
