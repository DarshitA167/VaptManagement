from rest_framework import serializers
from .models import APIScan

class APIScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIScan
        fields = "__all__"
