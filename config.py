"""
ElevenLabs Voice Agent Configuration
Zentrale Konfiguration für den Voice-Agent
"""
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class Config:
    """Zentrale Konfigurationsklasse"""
    
    # API Keys
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    CURSOR_API_KEY = os.getenv("CURSOR_API_KEY")
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Für AI-basierte Variable-Extraktion
    
    # HIRINGS API Configuration (von HOC)
    HIRINGS_API_URL = os.getenv("HIRINGS_API_URL")
    HIRINGS_API_TOKEN = os.getenv("HIRINGS_API_TOKEN")
    
    # Webhook API Key (für HOC Authentifizierung)
    WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # ElevenLabs Phone Number ID
    ELEVENLABS_AGENT_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_AGENT_PHONE_NUMBER_ID")
    
    # ElevenLabs API URL (EU Region für Data Residency Keys)
    # Für EU Data Residency Keys muss die EU-spezifische Base URL verwendet werden
    ELEVENLABS_API_URL = "https://api.elevenlabs.io"  # SDK handled das automatisch mit dem _eu Key
    
    # Voice Settings
    VOICE_NAME = os.getenv("VOICE_NAME", "Bella")
    VOICE_MODEL = os.getenv("VOICE_MODEL", "eleven_multilingual_v2")
    VOICE_STABILITY = float(os.getenv("VOICE_STABILITY", "0.5"))
    VOICE_SIMILARITY_BOOST = float(os.getenv("VOICE_SIMILARITY_BOOST", "0.75"))
    
    # Cursor Settings
    CURSOR_MODEL = os.getenv("CURSOR_MODEL", "cursor-small")
    CURSOR_API_URL = "https://api.cursor.sh/v1/chat/completions"
    
    # Validierung
    @classmethod
    def validate(cls):
        """Prüft, ob alle erforderlichen Konfigurationen gesetzt sind"""
        errors = []
        
        if not cls.ELEVENLABS_API_KEY:
            errors.append("ELEVENLABS_API_KEY fehlt in der .env Datei")
        
        # CURSOR_API_KEY wird nicht mehr benötigt - LLM kommt aus Dashboard
        # if not cls.CURSOR_API_KEY:
        #     errors.append("CURSOR_API_KEY fehlt in der .env Datei")
        
        # HIRINGS API Token ist optional für Tests, aber empfohlen
        if not cls.HIRINGS_API_TOKEN:
            print("⚠️  Warnung: HIRINGS_API_TOKEN fehlt - Questionnaire-Abruf wird nicht funktionieren")
        
        if errors:
            raise ValueError(
                "Konfigurationsfehler:\n" + "\n".join(f"- {e}" for e in errors)
            )
        
        return True

