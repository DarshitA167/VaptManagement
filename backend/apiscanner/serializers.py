from rest_framework import serializers
from .models import APIScan

class APIScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIScan
        fields = "__all__"
        read_only_fields = ("id", "status", "progress", "results", "created_at", "finished_at", "error")
