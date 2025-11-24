"""
Sellcruiting Agent Configuration
ANLEITUNG: Fülle diese Datei mit den Einstellungen aus deinem ElevenLabs Dashboard aus
"""

class AgentConfig:
    """Konfiguration für den Sellcruiting Voice-Agent"""
    
    # ============================================================================
    # AGENT DETAILS
    # ============================================================================
    AGENT_ID = "agent_2101kab7rs5tefesz0gm66418aw1"
    AGENT_NAME = "Sellcruiting Agent"
    LANGUAGE = "de"
    
    # ============================================================================
    # SYSTEM PROMPT
    # Kopiere den gesamten System-Prompt aus dem ElevenLabs Dashboard hier rein
    # ============================================================================
    SYSTEM_PROMPT = """
Du bist ein professioneller Recruiting-Assistent für [FIRMENNAME].

[FÜGE HIER DEINEN SYSTEM-PROMPT EIN]

Beispiel:
- Deine Aufgabe ist es, potenzielle Kandidaten anzusprechen
- Du stellst relevante Fragen zu ihrer Erfahrung
- Du bist freundlich und professionell
- ...
"""
    
    # ============================================================================
    # ERSTE NACHRICHT / BEGRÜSSUNG
    # Kopiere die First Message aus dem ElevenLabs Dashboard
    # ============================================================================
    FIRST_MESSAGE = "Hallo! Ich bin dein Recruiting-Assistent. Wie kann ich dir heute helfen?"
    
    # ============================================================================
    # LLM EINSTELLUNGEN
    # Kopiere diese Werte aus "LLM Settings" im Dashboard
    # ============================================================================
    LLM_MODEL = "gpt-4"  # oder "gpt-3.5-turbo"
    TEMPERATURE = 0.7    # 0.0 - 1.0 (höher = kreativer)
    MAX_TOKENS = 1000    # Max. Länge der Antworten
    
    # ============================================================================
    # VOICE EINSTELLUNGEN
    # Kopiere diese aus "Voice Settings" im Dashboard
    # ============================================================================
    # Hinweis: Voice IDs findest du unter https://elevenlabs.io/app/voice-library
    VOICE_ID = ""        # z.B. "21m00Tcm4TlvDq8ikWAM" für Rachel
    VOICE_NAME = "Bella" # Name der Stimme
    VOICE_STABILITY = 0.5           # 0.0 - 1.0
    VOICE_SIMILARITY_BOOST = 0.75   # 0.0 - 1.0
    
    # ============================================================================
    # CONVERSATION SETTINGS
    # ============================================================================
    MAX_DURATION_SECONDS = 600  # 10 Minuten


# ============================================================================
# ANLEITUNG ZUM AUSFÜLLEN:
# ============================================================================
"""
1. Öffne deinen Agent im Dashboard:
   https://eu.residency.elevenlabs.io/app/agents/agents/agent_2101kab7rs5tefesz0gm66418aw1

2. Kopiere folgende Bereiche:
   
   📋 SYSTEM PROMPT:
   - Gehe zu "Agent Settings" → "System Prompt"
   - Kopiere den gesamten Text
   - Füge ihn oben bei SYSTEM_PROMPT ein
   
   💬 FIRST MESSAGE:
   - Gehe zu "Conversation Settings" → "First Message"  
   - Kopiere die Begrüßung
   - Füge sie bei FIRST_MESSAGE ein
   
   🧠 LLM SETTINGS:
   - Gehe zu "LLM Settings"
   - Notiere Model, Temperature, Max Tokens
   - Trage sie oben ein
   
   🎙️ VOICE SETTINGS:
   - Gehe zu "Voice Settings"
   - Notiere Voice Name/ID
   - Notiere Stability und Similarity Boost
   - Trage sie oben ein

3. Speichere diese Datei

4. Teste mit: python voice_agent.py
"""

