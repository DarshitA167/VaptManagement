from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from chatbot_utils.logic import get_best_answer



@api_view(['POST'])
def chatbot_query(request):
    message = request.data.get("message", "")
    reply = get_best_answer(message)
    return Response({"reply": reply})
