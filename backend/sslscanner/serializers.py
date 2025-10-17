from rest_framework import serializers
from .models import SSLScan

class SSLScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SSLScan
        fields = '__all__'  # returns result_json + pdf_report + other fields
