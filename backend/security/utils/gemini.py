import google.generativeai as genai
import os
import logging

# Optional but helpful: Set up logging
logger = logging.getLogger(__name__)

# Make sure you have this set in your environment or .env file
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
else:
    raise ValueError("🚨 Gemini API key not found! Please set GENAI_API_KEY in your environment.")

# This function sends a prompt to Gemini and gets the response
def get_gemini_analysis(prompt):
    try:
        logger.info("get_gemini_analysis(): Sending prompt to Gemini...")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        if response.text:
            logger.info("get_gemini_analysis(): Response received from Gemini.")
            return response.text.strip()
        else:
            logger.warning("get_gemini_analysis(): Empty response from Gemini.")
            return "Sorry, I couldn't analyze your responses right now. Please try again later."

    except Exception as e:
        logger.error(f"get_gemini_analysis(): Gemini API call failed ❌ - {e}")
        return "An error occurred while analyzing your responses. Please try again later."
