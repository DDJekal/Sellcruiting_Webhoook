"""
ElevenLabs Voice Agent mit Cursor API Integration
Ein interaktiver Voice-Agent, der Cursor für Text-Generation und ElevenLabs für Sprache nutzt
"""
import sys
import requests
from elevenlabs import ElevenLabs, VoiceSettings
from elevenlabs.environment import ElevenLabsEnvironment
from config import Config
from colorama import init, Fore, Style

# Initialisiere colorama für farbige Terminal-Ausgabe
init()

class VoiceAgent:
    """Hauptklasse für den Voice-Agent"""
    
    def __init__(self):
        """Initialisiert den Voice-Agent"""
        print(f"{Fore.CYAN}🤖 Voice-Agent wird initialisiert...{Style.RESET_ALL}")
        
        # Validiere Konfiguration
        try:
            Config.validate()
        except ValueError as e:
            print(f"{Fore.RED}❌ {e}{Style.RESET_ALL}")
            sys.exit(1)
        
        # Initialisiere ElevenLabs Client mit EU Environment
        self.client = ElevenLabs(
            api_key=Config.ELEVENLABS_API_KEY,
            environment=ElevenLabsEnvironment.PRODUCTION_EU
        )
        self.conversation = None
        
        print(f"{Fore.GREEN}✅ Voice-Agent bereit!{Style.RESET_ALL}\n")
    
    def cursor_chat(self, prompt: str, conversation_history: list = None) -> str:
        """
        Sendet eine Anfrage an die Cursor API
        
        Args:
            prompt: Die Benutzereingabe
            conversation_history: Bisheriger Gesprächsverlauf
            
        Returns:
            Die Antwort von Cursor
        """
        headers = {
            "Authorization": f"Bearer {Config.CURSOR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Baue Nachrichten-Array
        messages = conversation_history or []
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": Config.CURSOR_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(Config.CURSOR_API_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ Fehler bei Cursor API: {e}{Style.RESET_ALL}")
            return "Entschuldigung, ich konnte keine Antwort generieren."
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Wandelt Text in Sprache um mit ElevenLabs
        
        Args:
            text: Der zu sprechende Text
            
        Returns:
            Audio-Daten als Bytes
        """
        try:
            audio = self.client.generate(
                text=text,
                voice=Config.VOICE_NAME,
                model=Config.VOICE_MODEL,
                voice_settings=VoiceSettings(
                    stability=Config.VOICE_STABILITY,
                    similarity_boost=Config.VOICE_SIMILARITY_BOOST
                )
            )
            return audio
        except Exception as e:
            print(f"{Fore.RED}❌ Fehler bei Text-to-Speech: {e}{Style.RESET_ALL}")
            return None
    
    def start_conversation(self):
        """Startet eine interaktive Konversation"""
        print(f"{Fore.YELLOW}💬 Konversation gestartet! (Tippe 'exit' zum Beenden){Style.RESET_ALL}\n")
        
        conversation_history = []
        
        while True:
            try:
                # Benutzer-Eingabe
                user_input = input(f"{Fore.BLUE}Du: {Style.RESET_ALL}")
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'tschüss']:
                    print(f"{Fore.CYAN}👋 Auf Wiedersehen!{Style.RESET_ALL}")
                    break
                
                if not user_input.strip():
                    continue
                
                # Hole Antwort von Cursor
                print(f"{Fore.YELLOW}🤔 Denke nach...{Style.RESET_ALL}", end="\r")
                ai_response = self.cursor_chat(user_input, conversation_history)
                
                # Füge zur History hinzu
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": ai_response})
                
                # Zeige Antwort
                print(f"{Fore.GREEN}Agent: {Style.RESET_ALL}{ai_response}\n")
                
                # Optional: Generiere Audio (auskommentiert, da noch keine Wiedergabe implementiert)
                # audio = self.text_to_speech(ai_response)
                # if audio:
                #     play(audio)  # Benötigt Audio-Wiedergabe-Implementierung
                
            except KeyboardInterrupt:
                print(f"\n{Fore.CYAN}👋 Auf Wiedersehen!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Fehler: {e}{Style.RESET_ALL}")
    
    def start_conversational_ai(self):
        """
        Startet den Conversational AI Mode mit ElevenLabs
        (Erfordert Agent-ID in der .env Datei)
        """
        if not Config.ELEVENLABS_AGENT_ID:
            print(f"{Fore.RED}❌ ELEVENLABS_AGENT_ID fehlt in der .env Datei{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Erstelle zuerst einen Agent im ElevenLabs Dashboard{Style.RESET_ALL}")
            return
        
        try:
            print(f"{Fore.CYAN}🎙️ Starte Conversational AI...{Style.RESET_ALL}")
            
            self.conversation = self.client.conversational_ai.conversations.start(
                agent_id=Config.ELEVENLABS_AGENT_ID,
                override_agent_settings={
                    "llm": {
                        "api_key": Config.CURSOR_API_KEY,
                        "base_url": "https://api.cursor.sh/v1",
                        "model": Config.CURSOR_MODEL
                    }
                }
            )
            
            print(f"{Fore.GREEN}✅ Conversational AI aktiv!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}🎤 Sprich mit dem Agent über dein Mikrofon{Style.RESET_ALL}")
            
            # Halte die Konversation am Leben
            input(f"\n{Fore.YELLOW}Drücke Enter um die Konversation zu beenden...{Style.RESET_ALL}\n")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Fehler beim Starten der Konversation: {e}{Style.RESET_ALL}")
        finally:
            if self.conversation:
                self.conversation.end()
                print(f"{Fore.CYAN}👋 Konversation beendet{Style.RESET_ALL}")


def main():
    """Hauptfunktion"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════╗
║     🎙️  ElevenLabs Voice Agent mit Cursor API 🤖   ║
╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
    
    agent = VoiceAgent()
    
    print(f"{Fore.YELLOW}Wähle einen Modus:{Style.RESET_ALL}")
    print(f"  1. Text-Chat (nur Tastatur)")
    print(f"  2. Conversational AI (mit Sprach-Ein- und Ausgabe)")
    
    choice = input(f"\n{Fore.BLUE}Deine Wahl (1/2): {Style.RESET_ALL}").strip()
    
    if choice == "1":
        agent.start_conversation()
    elif choice == "2":
        agent.start_conversational_ai()
    else:
        print(f"{Fore.RED}❌ Ungültige Wahl{Style.RESET_ALL}")


if __name__ == "__main__":
    main()

