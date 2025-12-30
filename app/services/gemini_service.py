from google import genai
from google.genai import types
from app.config import Config
from app.models.sql_models import AppConfig
import re

class GeminiService:
    def __init__(self):
        self.client = None
        if Config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        else:
            print("Warning: GEMINI_API_KEY not set.")

    def get_model_name(self):
        # Fetch dynamic model name from DB or use default
        config = AppConfig.query.filter_by(key="gemini_model").first()
        return config.value if config else "gemini-2.5-flash"

    def generate_response(self, chat_history, user_input, persona):
        if not self.client:
            return "Error: API Key not configured."

        model_name = self.get_model_name()
        
        contents = []
        for msg in chat_history:
             contents.append(msg)
             
        contents.append({"role": "user", "parts": [{"text": user_input}]})

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=persona,
                    temperature=0.7,
                    tools=[types.Tool(google_search=types.GoogleSearch())] # Search Grounding
                )
            )
            
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            return "No response generated."
            
        except Exception as e:
            error_str = str(e)
            print(f"Gemini API Error: {error_str}")
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                return "The Ley Lines are overflowing with elemental energy (Quota Exceeded). Please wait a moment before consulting the stars again, Traveler."
            return "Hmm, the stars are cloudy today... I couldn't reach Teyvat. (Error communicating with AI)"

    def generate_quiz(self, topic):
        if not self.client:
            return None
            
        model_name = self.get_model_name()
        prompt = (
            f"Create a fun multiple-choice quiz question themed around Genshin Impact. "
            f"Topic: '{topic}'. include 4 choices A) B) C) D). "
            f"Format:\n**Question:** <question>\n**A)** <choice>\n...\n**Correct Answer:** <answer>"
        )

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                     temperature=0.7,
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                raw_text = response.candidates[0].content.parts[0].text
                return self.parse_quiz(raw_text)
                
        except Exception as e:
            print(f"Quiz Gen Error: {e}")
            
        return None

    def parse_quiz(self, text):
        """
        Parses the raw text from Gemini into a structured dictionary.
        """
        lines = text.split('\n')
        question = ""
        choices = []
        correct_answer = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple Regex parsing
            if line.startswith("**Question:**"):
                question = line.replace("**Question:**", "").strip()
            elif line.startswith("**A)**") or line.startswith("**B)**") or line.startswith("**C)**") or line.startswith("**D)**"):
                # Extract Choice
                choice = line.replace("**", "").strip() # Remove bold markers
                choices.append(choice)
            elif line.startswith("**Correct Answer:**"):
                correct_answer = line.replace("**Correct Answer:**", "").strip()
            elif not question: 
                # If first line doesn't match but assuming it might be question continuation
                pass 
                
        # Fallback if structure is slightly off (e.g. no bold) - Logic from old wanderer.py
        if not question:
             # Try stricter regex from original file if needed, but for now returned structure:
             pass

        return {
            "question": question,
            "choices": choices,
            "correct_answer": correct_answer,
            "raw_text": text # Keep raw just in case
        }

gemini_service = GeminiService()
