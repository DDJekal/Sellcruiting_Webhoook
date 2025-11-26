"""
Twilio ↔ ElevenLabs Integration
Nutzt Twilio REST API für Outbound Calls + ElevenLabs WebSocket
"""
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start
from config import Config

class TwilioElevenLabsIntegration:
    """Handler für Twilio + ElevenLabs Calls mit Prompt Override"""
    
    def __init__(self):
        """Initialisiere Twilio Client"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.twilio_number]):
            raise ValueError("Twilio credentials missing in .env!")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def initiate_call_with_elevenlabs(
        self, 
        to_number: str,
        enhanced_prompt: str,
        first_message: str,
        webhook_base_url: str
    ):
        """
        Startet einen Twilio Outbound Call und verbindet zu ElevenLabs
        
        Args:
            to_number: Ziel-Telefonnummer (E.164)
            enhanced_prompt: Der überschriebene Prompt
            first_message: Die überschriebene erste Nachricht
            webhook_base_url: Base URL des Webhooks (z.B. https://yourapp.onrender.com)
        
        Returns:
            dict: Call-Information mit SID, Status, etc.
        """
        
        # Erstelle TwiML-URL mit Parametern
        # Diese URL wird von Twilio aufgerufen, wenn der Call verbunden wird
        twiml_url = f"{webhook_base_url}/webhook/twilio-connect"
        
        # WICHTIG: Wir müssen Prompt + First Message irgendwo speichern
        # für den TwiML Callback. Optionen:
        # 1. In einer Session/Database (empfohlen für Produktion)
        # 2. Als URL-Parameter (zu lang!)
        # 3. In einem temporären Cache (Redis, Memcached)
        
        # Für jetzt: Erstelle den Call und übergebe eine Session-ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Speichere Session-Daten (in Produktion: Redis/Database)
        # Für Demo: In-Memory Dict (nur für Tests!)
        if not hasattr(self, '_sessions'):
            self._sessions = {}
        
        self._sessions[session_id] = {
            'enhanced_prompt': enhanced_prompt,
            'first_message': first_message
        }
        
        # Starte Twilio Call
        call = self.client.calls.create(
            to=to_number,
            from_=self.twilio_number,
            url=f"{twiml_url}?session_id={session_id}",
            method='POST',
            status_callback=f"{webhook_base_url}/webhook/twilio-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        return {
            'call_sid': call.sid,
            'status': call.status,
            'to_number': to_number,
            'from_number': self.twilio_number,
            'session_id': session_id
        }
    
    def generate_elevenlabs_twiml(
        self,
        session_id: str,
        agent_id: str
    ) -> str:
        """
        Generiert TwiML, das Twilio zu ElevenLabs WebSocket verbindet
        
        Args:
            session_id: Session-ID für Prompt/First Message Lookup
            agent_id: ElevenLabs Agent ID
        
        Returns:
            str: TwiML XML
        """
        
        # Hole Session-Daten
        session_data = self._sessions.get(session_id, {})
        enhanced_prompt = session_data.get('enhanced_prompt', '')
        first_message = session_data.get('first_message', '')
        
        # Erstelle TwiML Response
        response = VoiceResponse()
        
        # WICHTIG: Twilio <Stream> Element für WebSocket-Verbindung
        # Verbindet Twilio Audio zu ElevenLabs WebSocket
        start = Start()
        
        # ElevenLabs WebSocket URL (EU Residency)
        websocket_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
        
        # PROBLEM: ElevenLabs WebSocket akzeptiert conversation_config_override
        # ABER: Nur über die initial connection, nicht über TwiML <Stream>!
        
        # LÖSUNG: Wir nutzen einen PROXY WebSocket-Server, der:
        # 1. Von Twilio das Audio empfängt
        # 2. Zu ElevenLabs mit conversation_config_override connectet
        # 3. Audio zwischen beiden hin- und herschickt
        
        # Für eine einfachere Lösung OHNE Proxy:
        # Nutze ElevenLabs signed_url mit Dynamic Variables (aber begrenzt!)
        
        start.stream(
            url=websocket_url,
            track='both_tracks'
        )
        
        response.append(start)
        
        # Fallback: Wenn Stream nicht funktioniert
        response.say(
            "Verbinde Sie mit unserem Assistenten. Bitte warten Sie einen Moment.",
            voice='Polly.Vicki',
            language='de-DE'
        )
        
        return str(response)


# ============================================================================
# ALTERNATIVE: EINFACHERE LÖSUNG ohne WebSocket-Proxy
# ============================================================================

def initiate_twilio_call_simple(
    to_number: str,
    enhanced_prompt: str,
    first_message: str
):
    """
    EINFACHERE Twilio-Integration ohne WebSocket-Komplexität
    
    Strategie:
    1. Speichere Enhanced Prompt in ElevenLabs als "Knowledge Base" Entry
    2. Nutze Dynamic Variables für First Message
    3. Starte Twilio Call zu ElevenLabs Phone Number
    
    ABER: Prompt Override ist so nicht möglich! ❌
    
    BESSER: Nutze ElevenLabs Phone Number direkt, OHNE Twilio!
    """
    pass


# ============================================================================
# EMPFEHLUNG: SIP TRUNK ist die beste Lösung!
# ============================================================================

"""
WARUM TWILIO KOMPLIZIERT IST:

1. Twilio Calls → Brauchen TwiML Webhook
2. TwiML → Kann zu WebSocket connecten (<Stream>)
3. ElevenLabs WebSocket → Braucht conversation_config_override
4. ABER: <Stream> kann keine Header/Initial Message senden!

LÖSUNG A: WebSocket Proxy (komplex)
LÖSUNG B: SIP Trunk (einfach, funktioniert bereits!)

Für deine Anwendung: SIP TRUNK mit Xelion ist die beste Wahl!
- Volle API-Kontrolle ✅
- Prompt Override ✅  
- Keine Twilio-Komplexität ✅
"""

