import os
import json
import datetime
from typing import Dict, Any, List
import google.generativeai as genai

# Try to look for API key in environment
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class ContentEngine:
    """Handles interactions with the AI model."""
    
    def __init__(self, api_key: str = None):
        # Securely load key from secrets.toml
        # To run locally: Ensure .streamlit/secrets.toml exists
        try:
            key = st.secrets["general"]["gemini_api_key"]
        except FileNotFoundError:
            # Fallback for when secrets aren't set up yet (or passed explicitly)
            key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not key:
            st.error("No API Key found! Please set it in .streamlit/secrets.toml")
            return

        genai.configure(api_key=key)
        
        # Fallback to gemini-pro if flash is causing 404s with older SDKs/Keys
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def rate_question(self, question_text: str) -> Dict[str, Any]:
        """
        Rates a user's question on a scale of 1-100 based on depth, creativity, and insight.
        """
        prompt = f"""
        You are the 'Curiosity Judge'. A user is feeding you a question to keep their curiosity pet alive.
        Rate this question: "{question_text}"
        
        Criteria:
        - 1-30: Boring, factual, easy to google (e.g., "What is the capital of France?")
        - 31-60: Interesting but standard (e.g., "Why is the sky blue?")
        - 61-85: Thought-provoking, connects concepts (e.g., "If time is relative, does history exist?")
        - 86-100: Mind-blowing, novel, deep philosophical or scientific insight.
        
        Return JSON ONLY:
        {{
            "score": <int 1-100>,
            "comment": "<Short, witty, slightly judgmental or praising comment in Chinese (Simplified). Max 20 words.>",
            "answer": "<A slightly detailed, interesting answer to the question itself. As if you are a knowledgeable professor answering a student. MUST BE IN CHINESE (Simplified). Max 100 words.>"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Simple clean up to ensure we get JSON
            text = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(text)
            
            # Fallback if 'answer' key missing in older schema
            if "answer" not in result:
                result["answer"] = "AI 正在思考更深层的问题，暂时无法回答。"
                
            return result
        except Exception as e:
            return {
                "score": 10,
                "comment": f"AI 脑子卡住了... ({str(e)})"
            }

class StateManager:
    """Handles local data persistence."""
    
    FILE_PATH = "user_data.json"
    
    DEFAULT_DATA = {
        "pet_health": 80,  # 0-100
        "pet_level": 1,
        "pet_emoji": "🐱", # Default to Cat
        "last_active_date": str(datetime.date.today()),
        "questions_today": 0,
        "history": [] # List of {date, question, score, comment}
    }

    @staticmethod
    def load_data() -> Dict[str, Any]:
        if not os.path.exists(StateManager.FILE_PATH):
            return StateManager.DEFAULT_DATA.copy()
        
        try:
            with open(StateManager.FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for day change and apply decay
            today = str(datetime.date.today())
            if data["last_active_date"] != today:
                # Logic for new day
                days_missed = (datetime.date.today() - datetime.datetime.strptime(data["last_active_date"], "%Y-%m-%d").date()).days
                
                # Decay health heavily for missed days
                decay = days_missed * 20 
                data["pet_health"] = max(0, data["pet_health"] - decay)
                data["questions_today"] = 0
                data["last_active_date"] = today
                
                StateManager.save_data(data)
                
            return data
        except Exception:
            return StateManager.DEFAULT_DATA.copy()

    @staticmethod
    def save_data(data: Dict[str, Any]):
        with open(StateManager.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def add_question(data: Dict[str, Any], question: str, rating: Dict[str, Any]) -> Dict[str, Any]:
        """Updates state with a new question result."""
        score = rating["score"]
        
        # Health Logic: High scores heal more, low scores might even hurt (optional, keep simple for now)
        heal_amount = score // 10
        data["pet_health"] = min(100, data["pet_health"] + heal_amount)
        data["questions_today"] += 1
        
        # Level up logic (simplified)
        if data["pet_health"] == 100:
             data["pet_level"] += 1
             data["pet_health"] = 50 # Reset health but higher level (prestige) - or just keep it 100. Let's keep 100 cap for now.
        
        record = {
            "time": datetime.datetime.now().strftime("%H:%M"),
            "question": question,
            "score": score,
            "comment": rating["comment"]
        }
        # Prepend to history for latest first
        data["history"].insert(0, record)
        
        StateManager.save_data(data)
        return data
