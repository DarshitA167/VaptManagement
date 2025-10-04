import requests
import os

def openrouter_chatbot(messages):
    api_key = os.getenv("COHERE_API_KEY")  # 🔐 Load from .env

    conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    url = "https://api.cohere.ai/v1/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "message": conversation,
        "model": "command-r-plus",
        "temperature": 0.7,
        "chat_history": []
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("text", "No response from Cohere.")
        else:
            print("Cohere API error:", response.text)
            return "Cohere API error occurred."
    except Exception as e:
        return f"Error: {str(e)}"
