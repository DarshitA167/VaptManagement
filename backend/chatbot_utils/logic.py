# backend/chatbot_utils/logic.py
def get_best_answer(user_query):
    from chatbot_utils.prompts import KNOWLEDGE_BASE

    for item in KNOWLEDGE_BASE:
        if item["question"].lower() in user_query.lower():
            return item["answer"]
    return "Sorry, I couldn't find an answer to your question."
