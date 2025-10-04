from rest_framework import serializers

class DiseaseDetectionSerializer(serializers.Serializer):
    symptoms = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    image = serializers.ImageField(required=False)

    def validate(self, data):
        if not data.get('symptoms') and not data.get('image'):
            raise serializers.ValidationError("Provide either symptoms or an image")
        return data


from .models import ScanHistory
from rest_framework import serializers

class ScanHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanHistory
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


from rest_framework import serializers
from .models import PasswordEntry

class PasswordEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordEntry
        fields = '__all__'
        read_only_fields = ['user', 'created_at']
