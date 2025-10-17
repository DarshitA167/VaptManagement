from rest_framework import serializers
from .models import NetworkScan

class NetworkScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkScan
        fields = ["id", "ip", "ports", "results", "status", "created_at"]  # include id
