"""
Sellcruiting Agent Configuration Importer
Liest alle Einstellungen von deinem ElevenLabs Agent aus und bereitet sie für voice_agent.py vor
"""
import sys
import io
from elevenlabs import ElevenLabs
from config import Config
import json

# Fix Windows Terminal Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Deine Agent-ID
AGENT_ID = "agent_2101kab7rs5tefesz0gm66418aw1"

def import_agent_config():
    """Importiert die Konfiguration vom ElevenLabs Agent"""
    
    client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
    
    try:
        print("🔄 Lade Agent-Konfiguration...")
        
        # Hole Agent-Details - API nutzt direkt conversational_ai für Agents
        # Versuche verschiedene API-Methoden
        try:
            # Methode 1: Direkt über conversational_ai
            response = client.conversational_ai.get(f"/agents/{AGENT_ID}")
            agent = response
        except:
            # Methode 2: Über direkte HTTP-Anfrage (Fallback)
            import httpx
            headers = {"xi-api-key": Config.ELEVENLABS_API_KEY}
            response = httpx.get(
                f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}",
                headers=headers
            )
            response.raise_for_status()
            agent = response.json()
        
        print("\n" + "="*70)
        print("🤖 SELLCRUITING AGENT - KONFIGURATION")
        print("="*70 + "\n")
        
        # Extrahiere alle relevanten Einstellungen (agent kann dict oder object sein)
        def get_value(obj, *keys, default=''):
            """Hilfsfunktion um Werte aus dict oder object zu holen"""
            for key in keys:
                if isinstance(obj, dict):
                    obj = obj.get(key, default)
                else:
                    obj = getattr(obj, key, default)
                if obj == default:
                    return default
            return obj
        
        config = {
            "agent_id": AGENT_ID,
            "agent_name": get_value(agent, 'name', default='Sellcruiting Agent'),
            "system_prompt": get_value(agent, 'prompt', 'prompt', default=''),
            "first_message": get_value(agent, 'conversation_config', 'first_message', default=''),
            "language": get_value(agent, 'language', default='de'),
        }
        
        # LLM Settings
        llm = get_value(agent, 'llm')
        if llm and llm != '':
            config['llm'] = {
                "model": get_value(llm, 'model', default='gpt-4'),
                "temperature": get_value(llm, 'temperature', default=0.7),
                "max_tokens": get_value(llm, 'max_tokens', default=1000),
            }
        
        # Voice Settings  
        voice = get_value(agent, 'voice_settings')
        if voice and voice != '':
            config['voice'] = {
                "voice_id": get_value(voice, 'voice_id', default=''),
                "voice_name": get_value(voice, 'voice_name', default=''),
                "stability": get_value(voice, 'stability', default=0.5),
                "similarity_boost": get_value(voice, 'similarity_boost', default=0.75),
            }
        
        # Conversation Config
        conv = get_value(agent, 'conversation_config')
        if conv and conv != '':
            config['conversation'] = {
                "first_message": get_value(conv, 'first_message', default=''),
                "max_duration": get_value(conv, 'max_duration_seconds', default=600),
            }
        
        # Zeige Konfiguration im Terminal
        print(f"📝 Agent Name: {config['agent_name']}")
        print(f"🆔 Agent ID: {config['agent_id']}")
        print(f"🌍 Sprache: {config.get('language', 'de')}")
        
        if 'voice' in config:
            print(f"\n🎙️ Voice: {config['voice'].get('voice_name', 'N/A')}")
            print(f"   Stability: {config['voice']['stability']}")
            print(f"   Similarity Boost: {config['voice']['similarity_boost']}")
        
        if 'llm' in config:
            print(f"\n🧠 LLM Model: {config['llm']['model']}")
            print(f"🌡️  Temperature: {config['llm']['temperature']}")
            print(f"📏 Max Tokens: {config['llm']['max_tokens']}")
        
        if config.get('first_message'):
            print(f"\n💬 Erste Nachricht:")
            print(f"   '{config['first_message']}'")
        
        print(f"\n📋 System Prompt:")
        print("─" * 70)
        print(config.get('system_prompt', 'N/A'))
        print("─" * 70)
        
        # Speichere als JSON
        with open('sellcruiting_agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Konfiguration gespeichert in: sellcruiting_agent_config.json")
        
        # Generiere Code für agent_config.py
        print(f"\n📝 Erstelle agent_config.py...")
        
        agent_config_code = f'''"""
Sellcruiting Agent Configuration
Automatisch importiert von ElevenLabs Agent
"""

class AgentConfig:
    """Konfiguration für den Sellcruiting Voice-Agent"""
    
    # Agent Details
    AGENT_ID = "{config['agent_id']}"
    AGENT_NAME = "{config['agent_name']}"
    LANGUAGE = "{config.get('language', 'de')}"
    
    # System Prompt (aus deinem ElevenLabs Agent)
    SYSTEM_PROMPT = """{config.get('system_prompt', '')}"""
    
    # Erste Nachricht
    FIRST_MESSAGE = """{config.get('first_message', 'Hallo! Wie kann ich dir helfen?')}"""
    
    # LLM Einstellungen
    LLM_MODEL = "{config.get('llm', {}).get('model', 'gpt-4')}"
    TEMPERATURE = {config.get('llm', {}).get('temperature', 0.7)}
    MAX_TOKENS = {config.get('llm', {}).get('max_tokens', 1000)}
    
    # Voice Einstellungen
    VOICE_ID = "{config.get('voice', {}).get('voice_id', '')}"
    VOICE_NAME = "{config.get('voice', {}).get('voice_name', 'Bella')}"
    VOICE_STABILITY = {config.get('voice', {}).get('stability', 0.5)}
    VOICE_SIMILARITY_BOOST = {config.get('voice', {}).get('similarity_boost', 0.75)}
    
    # Conversation Settings
    MAX_DURATION_SECONDS = {config.get('conversation', {}).get('max_duration', 600)}
'''
        
        with open('agent_config.py', 'w', encoding='utf-8') as f:
            f.write(agent_config_code)
        
        print(f"✅ agent_config.py erstellt!")
        
        print(f"\n{'='*70}")
        print("✨ ERFOLGREICH! Nächste Schritte:")
        print("─" * 70)
        print("1. Prüfe die agent_config.py Datei")
        print("2. Integriere sie in voice_agent.py")
        print("3. Teste den Agent mit: python voice_agent.py")
        print("=" * 70)
        
        return config
        
    except Exception as e:
        print(f"\n❌ Fehler beim Importieren: {e}")
        print(f"\n💡 Tipps:")
        print("   - Stelle sicher, dass ELEVENLABS_API_KEY in der .env korrekt ist")
        print("   - Überprüfe, ob du Zugriff auf diesen Agent hast")
        print(f"   - Agent ID: {AGENT_ID}")
        return None

if __name__ == "__main__":
    import_agent_config()

