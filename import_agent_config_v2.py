"""
Sellcruiting Agent Configuration Importer - Version 2
Nutzt die richtige API-Methode
"""
import sys
import io
from elevenlabs import ElevenLabs
from config import Config
import json

# Fix Windows Terminal Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

AGENT_ID = "agent_2101kab7rs5tefesz0gm66418aw1"

def import_agent_config():
    """Importiert die Konfiguration vom ElevenLabs Agent"""
    
    client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
    
    try:
        print("🔄 Lade Agent-Konfiguration...")
        print(f"   Agent ID: {AGENT_ID}\n")
        
        # Nutze die agents API
        agent = client.conversational_ai.agents.get(agent_id=AGENT_ID)
        
        print("="*70)
        print("🤖 SELLCRUITING AGENT - KONFIGURATION ERFOLGREICH GELADEN!")
        print("="*70 + "\n")
        
        # Debug: Zeige alle Attribute
        print("📊 Verfügbare Agent-Attribute:")
        attrs = [a for a in dir(agent) if not a.startswith('_')]
        print(f"   {', '.join(attrs[:10])}...")
        
        # Extrahiere Konfiguration
        config = {
            "agent_id": AGENT_ID,
            "agent_name": getattr(agent, 'name', 'Sellcruiting Agent'),
            "language": getattr(agent, 'language', 'de'),
        }
        
        # System Prompt
        if hasattr(agent, 'prompt'):
            prompt_obj = agent.prompt
            if hasattr(prompt_obj, 'prompt'):
                config['system_prompt'] = prompt_obj.prompt
            elif isinstance(prompt_obj, str):
                config['system_prompt'] = prompt_obj
            else:
                config['system_prompt'] = str(prompt_obj)
        
        # Conversation Config
        if hasattr(agent, 'conversation_config'):
            conv = agent.conversation_config
            if hasattr(conv, 'first_message'):
                config['first_message'] = conv.first_message
        
        # LLM Settings
        if hasattr(agent, 'llm'):
            llm = agent.llm
            config['llm'] = {
                "model": getattr(llm, 'model', 'gpt-4'),
                "temperature": getattr(llm, 'temperature', 0.7),
                "max_tokens": getattr(llm, 'max_tokens', 1000),
            }
        
        # Voice Settings
        if hasattr(agent, 'tts'):
            tts = agent.tts
            config['voice'] = {
                "voice_id": getattr(tts, 'voice_id', ''),
                "model_id": getattr(tts, 'model_id', 'eleven_multilingual_v2'),
                "stability": getattr(getattr(tts, 'voice_settings', None), 'stability', 0.5) if hasattr(tts, 'voice_settings') else 0.5,
                "similarity_boost": getattr(getattr(tts, 'voice_settings', None), 'similarity_boost', 0.75) if hasattr(tts, 'voice_settings') else 0.75,
            }
        
        # Ausgabe
        print(f"📝 Agent Name: {config.get('agent_name')}")
        print(f"🆔 Agent ID: {config['agent_id']}")
        print(f"🌍 Sprache: {config.get('language', 'de')}")
        
        if 'llm' in config:
            print(f"\n🧠 LLM Settings:")
            print(f"   Model: {config['llm']['model']}")
            print(f"   Temperature: {config['llm']['temperature']}")
            print(f"   Max Tokens: {config['llm']['max_tokens']}")
        
        if 'voice' in config:
            print(f"\n🎙️ Voice Settings:")
            print(f"   Voice ID: {config['voice'].get('voice_id', 'N/A')}")
            print(f"   Model: {config['voice'].get('model_id', 'N/A')}")
            print(f"   Stability: {config['voice']['stability']}")
            print(f"   Similarity Boost: {config['voice']['similarity_boost']}")
        
        if config.get('first_message'):
            print(f"\n💬 Erste Nachricht:")
            print(f"   '{config['first_message']}'")
        
        if config.get('system_prompt'):
            print(f"\n📋 System Prompt (erste 200 Zeichen):")
            print("─" * 70)
            prompt_preview = config['system_prompt'][:200]
            print(prompt_preview + "..." if len(config['system_prompt']) > 200 else prompt_preview)
            print("─" * 70)
        
        # Speichere als JSON
        with open('sellcruiting_agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Konfiguration gespeichert: sellcruiting_agent_config.json")
        
        # Erstelle agent_config.py
        agent_config_code = f'''"""
Sellcruiting Agent Configuration
Automatisch importiert von ElevenLabs Agent: {config.get('agent_name')}
"""

class AgentConfig:
    """Konfiguration für den Sellcruiting Voice-Agent"""
    
    # Agent Details
    AGENT_ID = "{config['agent_id']}"
    AGENT_NAME = "{config.get('agent_name', 'Sellcruiting Agent')}"
    LANGUAGE = "{config.get('language', 'de')}"
    
    # System Prompt
    SYSTEM_PROMPT = """{config.get('system_prompt', 'Du bist ein hilfreicher Assistent.')}"""
    
    # Erste Nachricht
    FIRST_MESSAGE = """{config.get('first_message', 'Hallo! Wie kann ich dir helfen?')}"""
    
    # LLM Einstellungen
    LLM_MODEL = "{config.get('llm', {}).get('model', 'gpt-4')}"
    TEMPERATURE = {config.get('llm', {}).get('temperature', 0.7)}
    MAX_TOKENS = {config.get('llm', {}).get('max_tokens', 1000)}
    
    # Voice Einstellungen
    VOICE_ID = "{config.get('voice', {}).get('voice_id', '')}"
    VOICE_MODEL = "{config.get('voice', {}).get('model_id', 'eleven_multilingual_v2')}"
    VOICE_STABILITY = {config.get('voice', {}).get('stability', 0.5)}
    VOICE_SIMILARITY_BOOST = {config.get('voice', {}).get('similarity_boost', 0.75)}
    
    # Conversation Settings
    MAX_DURATION_SECONDS = 600
'''
        
        with open('agent_config.py', 'w', encoding='utf-8') as f:
            f.write(agent_config_code)
        
        print(f"✅ agent_config.py erstellt!")
        
        print(f"\n{'='*70}")
        print("✨ ERFOLGREICH IMPORTIERT!")
        print("="*70)
        
        return config
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        print(f"\n💡 Debug-Info:")
        print(f"   Exception Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import_agent_config()

