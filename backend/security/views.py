from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import DiagnosisHistory
from .models import ScanHistory
from .serializers import ScanHistorySerializer
from rest_framework import generics, permissions
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PasswordEntry
from .serializers import PasswordEntrySerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def password_entries(request):
    if request.method == 'GET':
        entries = PasswordEntry.objects.filter(user=request.user)
        serializer = PasswordEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        serializer = PasswordEntrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def password_entry_detail(request, pk):
    try:
        entry = PasswordEntry.objects.get(pk=pk, user=request.user)
    except PasswordEntry.DoesNotExist:
        return Response({"error": "Entry not found"}, status=404)

    if request.method == 'PUT':
        serializer = PasswordEntrySerializer(entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        entry.delete()
        return Response(status=204)


@api_view(['POST'])
@permission_classes([AllowAny])
def diagnose_disease(request):
    symptoms = request.data.get('symptoms', [])
    result = predict_disease(symptoms)

    # Save to DB
    DiagnosisHistory.objects.create(
        user=request.user if request.user.is_authenticated else None,
        symptoms=json.dumps(symptoms),
        result=json.dumps(result)
    )

    return Response(result)


# List all history for the logged-in user
class ScanHistoryListView(generics.ListAPIView):
    serializer_class = ScanHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScanHistory.objects.filter(user=self.request.user).order_by('-created_at')

# Add a new scan history (used internally by each scan function)
class ScanHistoryCreateView(generics.CreateAPIView):
    serializer_class = ScanHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

