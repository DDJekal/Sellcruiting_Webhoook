"""
Webhook Receiver für HOC → ElevenLabs Outbound Calls
Empfängt Call-Trigger von HOC und startet personalisierten Agent-Call
Nutzt campaign_id um Questionnaire/Kontext aus HOC zu laden
"""
import sys
import io
import json
from urllib.parse import urlencode
from flask import Flask, request, jsonify
from elevenlabs import ElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
from elevenlabs.types.conversation_initiation_client_data_request_input import ConversationInitiationClientDataRequestInput
from config import Config
import requests
from datetime import datetime
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix Windows Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)

# ElevenLabs Client mit EU Environment
client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY,
    environment=ElevenLabsEnvironment.PRODUCTION_EU
)


def require_api_key(f):
    """
    Decorator für API Key Authentifizierung
    Prüft Authorization Header: Bearer {API_KEY}
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Prüfe ob API Key konfiguriert ist
        if not Config.WEBHOOK_API_KEY:
            logger.warning("⚠️  WEBHOOK_API_KEY nicht gesetzt - Authentifizierung deaktiviert")
            return f(*args, **kwargs)
        
        # Hole Authorization Header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            logger.warning("❌ Fehlender Authorization Header")
            return jsonify({
                "status": "error",
                "error": "Missing Authorization header",
                "message": "Please provide Authorization: Bearer {API_KEY}"
            }), 401
        
        # Prüfe Format: Bearer {key}
        if not auth_header.startswith('Bearer '):
            logger.warning("❌ Ungültiges Authorization Format")
            return jsonify({
                "status": "error",
                "error": "Invalid Authorization format",
                "message": "Use format: Authorization: Bearer {API_KEY}"
            }), 401
        
        # Extrahiere API Key
        provided_key = auth_header.replace('Bearer ', '').strip()
        
        # Vergleiche mit konfiguriertem Key
        if provided_key != Config.WEBHOOK_API_KEY:
            logger.warning(f"❌ Ungültiger API Key (von {request.remote_addr})")
            return jsonify({
                "status": "error",
                "error": "Invalid API key",
                "message": "The provided API key is invalid"
            }), 401
        
        # API Key ist gültig
        logger.info(f"✅ API Key validiert (von {request.remote_addr})")
        return f(*args, **kwargs)
    
    return decorated_function


def fetch_questionnaire_context(campaign_id: int) -> dict:
    """
    Holt Questionnaire/Kontextdatei aus HOC basierend auf Campaign-ID
    
    Args:
        campaign_id: Campaign ID für den Fragebogen
        
    Returns:
        dict mit Questionnaire-Daten und Kontext
    """
    try:
        headers = {
            "Authorization": f"Bearer {Config.HIRINGS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # HIRINGS API Endpunkt: questionnaire/<campaign_id>
        # HIRINGS_API_URL enthält bereits /api/v1
        url = f"{Config.HIRINGS_API_URL}/questionnaire/{campaign_id}"
        
        logger.info(f"📥 Lade Questionnaire von HOC: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        questionnaire = response.json()
        logger.info(f"✅ Questionnaire erfolgreich geladen für Campaign: {campaign_id}")
        
        return questionnaire
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Fehler beim Laden des Questionnaires: {e}")
        # Gib leeres Dict zurück, damit Call trotzdem funktioniert
        return {}


def build_first_message(company_name: str, first_name: str, last_name: str, campaign_location: str = "") -> str:
    """
    Erstellt personalisierte First Message für den Agent
    
    Args:
        company_name: Firmenname
        first_name: Vorname Kandidat
        last_name: Nachname Kandidat
        campaign_location: Standort der Kampagne (optional)
        
    Returns:
        Personalisierte First Message
    """
    if campaign_location:
        first_message = f"Guten Tag {first_name} {last_name}, hier spricht Susi von {company_name}. Es geht um ihre Bewerbung am Standort {campaign_location}. Haben Sie ungefähr 15 Minuten Zeit für dieses Gespräch um ihre Daten zu erfassen?"
    else:
        first_message = f"Guten Tag {first_name} {last_name}, hier spricht Susi von {company_name}. Es geht um ihre Bewerbung. Haben Sie ungefähr 15 Minuten Zeit für dieses Gespräch um ihre Daten zu erfassen?"
    
    logger.info(f"📝 First Message erstellt: {first_message[:100]}...")
    return first_message


def build_enhanced_prompt(questionnaire: dict, company_name: str, first_name: str, last_name: str) -> str:
    """
    Erstellt erweiterten System-Prompt mit Questionnaire-Kontext
    Lädt Dashboard-Prompt und ergänzt ihn mit Kontext-Daten
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        company_name: Firmenname
        first_name: Vorname Kandidat
        last_name: Nachname Kandidat
        
    Returns:
        Erweiterter System-Prompt mit vollem Kontext
    """
    
    # Lade Dashboard-Prompt aus Datei
    try:
        with open('dashboard_prompt.txt', 'r', encoding='utf-8') as f:
            dashboard_prompt = f.read()
        logger.info("✅ Dashboard-Prompt aus Datei geladen")
    except FileNotFoundError:
        logger.warning("⚠️  dashboard_prompt.txt nicht gefunden, nutze Basis-Prompt")
        dashboard_prompt = f"""Du bist ein professioneller Recruiting-Assistent für {company_name}.
Du führst ein Gespräch mit {first_name} {last_name}."""
    
    # Ersetze NUR Kandidaten-Platzhalter (Rest kommt aus Kontext!)
    dashboard_prompt = dashboard_prompt.replace('{{candidatefirst_name}}', first_name)
    dashboard_prompt = dashboard_prompt.replace('{{candidatelast_name}}', last_name)
    
    # Baue Questionnaire-Kontext
    questionnaire_context = build_questionnaire_context(questionnaire, company_name, first_name, last_name)
    
    # FINALER PROMPT: Dashboard-Prompt + Questionnaire-Kontext
    final_prompt = dashboard_prompt + "\n\n" + questionnaire_context
    
    logger.info(f"📝 Enhanced Prompt erstellt: {len(final_prompt)} Zeichen (Dashboard: {len(dashboard_prompt)}, Kontext: {len(questionnaire_context)})")
    
    return final_prompt


def build_questionnaire_context(questionnaire: dict, company_name: str, first_name: str, last_name: str) -> str:
    """
    Erstellt Questionnaire-Kontext als formatierten Text
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        company_name: Firmenname
        first_name: Vorname Kandidat
        last_name: Nachname Kandidat
        
    Returns:
        Questionnaire-Kontext als formatierter Text
    """
    
    # KONTEXT: Questionnaire-Daten formatieren
    questionnaire_context = f"""
===================================
KONTEXT AUS QUESTIONNAIRE (Campaign-ID: {questionnaire.get('id', 'N/A')}):
===================================

Kandidat: {first_name} {last_name}
Firma: {company_name}
"""
    
    if questionnaire:
        if questionnaire.get('title'):
            questionnaire_context += f"\nKampagne: {questionnaire['title']}"
        
        if questionnaire.get('position'):
            questionnaire_context += f"\nPosition: {questionnaire['position']}"
        
        if questionnaire.get('department'):
            questionnaire_context += f"\nAbteilung: {questionnaire['department']}"
        
        # Unternehmensinformationen
        if questionnaire.get('company_size'):
            questionnaire_context += f"\nMitarbeiterzahl: {questionnaire['company_size']}"
        
        if questionnaire.get('company_pitch'):
            questionnaire_context += f"\nUnternehmensbeschreibung: {questionnaire['company_pitch']}"
        
        if questionnaire.get('company_priorities'):
            questionnaire_context += f"\nAktuelle Prioritäten: {questionnaire['company_priorities']}"
        
        if questionnaire.get('description'):
            questionnaire_context += f"\n\nStellenbeschreibung:\n{questionnaire['description']}"
        
        if questionnaire.get('job_requirements'):
            questionnaire_context += f"\n\nAnforderungen:\n{questionnaire['job_requirements']}"
        
        if questionnaire.get('work_location') or questionnaire.get('office_address'):
            location = questionnaire.get('work_location') or questionnaire.get('office_address')
            questionnaire_context += f"\n\nArbeitsplatz-Standort: {location}"
        
        if questionnaire.get('work_location_postal_code'):
            questionnaire_context += f"\nPostleitzahl des Arbeitsplatzes: {questionnaire['work_location_postal_code']}"
        
        if questionnaire.get('campaignlocation_label'):
            questionnaire_context += f"\nStandort-Label: {questionnaire['campaignlocation_label']}"
        
        if questionnaire.get('questions'):
            questionnaire_context += "\n\nRelevante Fragen aus Questionnaire:"
            for i, q in enumerate(questionnaire['questions'], 1):
                if isinstance(q, dict):
                    questionnaire_context += f"\n{i}. {q.get('question_text', q.get('text', str(q)))}"
                else:
                    questionnaire_context += f"\n{i}. {q}"
        
        if questionnaire.get('key_qualifications'):
            questionnaire_context += f"\n\nSchlüssel-Qualifikationen:\n{questionnaire['key_qualifications']}"
        
        if questionnaire.get('company_benefits'):
            questionnaire_context += f"\n\nUnternehmensvorteile:\n{questionnaire['company_benefits']}"
        
        if questionnaire.get('conversation_goals'):
            questionnaire_context += f"\n\nGesprächsziele:\n{questionnaire['conversation_goals']}"
        
        # Falls es ein komplettes JSON-Objekt ist, zeige wichtige Felder
        if questionnaire.get('data'):
            data = questionnaire['data']
            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'updated_at']:
                        questionnaire_context += f"\n{key}: {value}"
    
    questionnaire_context += "\n===================================\n"
    
    logger.info(f"📝 Questionnaire-Kontext erstellt: {len(questionnaire_context)} Zeichen")
    
    return questionnaire_context


@app.route('/webhook/trigger-call', methods=['POST'])
@require_api_key
def trigger_outbound_call():
    """
    Webhook Endpoint: Empfängt Call-Request von HOC
    
    Intelligenter Fallback:
    - Wenn to_number vorhanden → Outbound SIP Trunk Call (Twilio)
    - Wenn to_number fehlt → WebRTC Link erstellen (Browser-basiert)
    
    Erwartet JSON:
    {
        "campaign_id": 123,
        "company_name": "Tech Startup GmbH",
        "candidate_first_name": "Max",
        "candidate_last_name": "Mustermann",
        "to_number": "+491234567890" (optional - falls fehlt: WebRTC Link),
        "agent_phone_number_id": "phnum_xxx..." (nur für SIP Trunk)
    }
    """
    try:
        # Parse Request - robuster JSON Parsing
        data = request.get_json(force=True, silent=True)
        
        # Falls get_json() None oder String zurückgibt, versuche manuell zu parsen
        if not data or isinstance(data, str):
            try:
                if isinstance(data, str):
                    # data ist bereits ein String, parse es
                    data = json.loads(data)
                elif request.data:
                    # Versuche request.data zu parsen
                    data = json.loads(request.data.decode('utf-8'))
                else:
                    return jsonify({
                        "error": "No JSON data provided",
                        "message": "Request body is empty"
                    }), 400
            except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as e:
                logger.error(f"❌ JSON Parse Error: {e}")
                logger.error(f"Request data: {request.data[:200] if request.data else 'None'}")
                return jsonify({
                    "error": "Invalid JSON format",
                    "message": f"Could not parse JSON: {str(e)}"
                }), 400
        
        # Sicherstellen dass data ein Dict ist
        if not isinstance(data, dict):
            logger.error(f"❌ Data is not a dict, type: {type(data)}, value: {data}")
            return jsonify({
                "error": "Invalid request format",
                "message": f"Request body must be a JSON object (dict), got {type(data).__name__}"
            }), 400
        
        # Validiere erforderliche Felder
        required_fields = ['campaign_id', 'company_name', 'candidate_first_name', 
                          'candidate_last_name']  # to_number ist jetzt OPTIONAL!
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing_fields
            }), 400
        
        # Extrahiere Daten
        campaign_id = int(data['campaign_id'])
        company_name = data['company_name']
        first_name = data['candidate_first_name']
        last_name = data['candidate_last_name']
        to_number = data.get('to_number')  # OPTIONAL!
        agent_phone_number_id = data.get('agent_phone_number_id', Config.ELEVENLABS_AGENT_PHONE_NUMBER_ID)
        override_prompt = data.get('override_prompt')
        
        # Validiere agent_phone_number_id nur wenn to_number vorhanden
        if to_number and not agent_phone_number_id:
            return jsonify({
                "error": "Missing agent_phone_number_id",
                "message": "Provide agent_phone_number_id in request or set ELEVENLABS_AGENT_PHONE_NUMBER_ID in environment"
            }), 400
        
        logger.info(f"\n{'='*70}")
        if to_number:
            logger.info(f"📞 NEUE CALL-ANFRAGE VON HOC (SIP TRUNK)")
        else:
            logger.info(f"🔗 NEUE LINK-ANFRAGE VON HOC (WEBRTC)")
        logger.info(f"{'='*70}")
        logger.info(f"⏰ Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📋 Campaign-ID: {campaign_id}")
        logger.info(f"👤 Kandidat: {first_name} {last_name}")
        logger.info(f"🏢 Firma: {company_name}")
        if to_number:
            logger.info(f"📞 Nummer: {to_number}")
            logger.info(f"📱 Phone Number ID: {agent_phone_number_id}")
        else:
            logger.info(f"🔗 Methode: WebRTC Link (kein to_number)")
        
        # 1. Hole Questionnaire aus HOC
        logger.info(f"\n🔄 Lade Questionnaire für Campaign {campaign_id}...")
        questionnaire = fetch_questionnaire_context(campaign_id)
        
        if not questionnaire:
            logger.warning(f"⚠️  Kein Questionnaire gefunden, fahre mit Basis-Prompt fort")
        
        # 2. Baue Enhanced Prompt mit Questionnaire-Kontext
        enhanced_prompt = override_prompt if override_prompt else build_enhanced_prompt(
            questionnaire=questionnaire,
            company_name=company_name,
            first_name=first_name,
            last_name=last_name
        )
        
        # 3. Baue personalisierte First Message
        campaign_location = (
            questionnaire.get('campaignlocation_label', '') or 
            questionnaire.get('work_location', '') or 
            questionnaire.get('location', '') or
            (f"{questionnaire.get('work_location', '')} {questionnaire.get('work_location_postal_code', '')}".strip())
        )
        
        first_message = build_first_message(
            company_name=company_name,
            first_name=first_name,
            last_name=last_name,
            campaign_location=campaign_location
        )
        
        logger.info(f"📝 Enhanced Prompt: {len(enhanced_prompt)} Zeichen")
        logger.info(f"💬 First Message: {first_message}")
        
        # =================================================================
        # INTELLIGENTER FALLBACK: SIP Trunk vs. WebRTC Link
        # =================================================================
        
        if to_number:
            # 📞 OPTION A: SIP TRUNK OUTBOUND CALL (Twilio)
            logger.info(f"\n{'='*70}")
            logger.info(f"📞 STARTE OUTBOUND CALL (SIP TRUNK mit Twilio)")
            logger.info(f"{'='*70}")
            
            try:
                # Erstelle ConversationInitiationClientDataRequestInput mit conversation_config_override
                client_data = ConversationInitiationClientDataRequestInput(
                    conversation_config_override={
                        "agent": {
                            "prompt": {
                                "prompt": enhanced_prompt  # ← Überschreibt Dashboard-Prompt!
                            },
                            "first_message": first_message  # ← Überschreibt Dashboard First Message!
                        }
                    }
                )
                
                response = client.conversational_ai.sip_trunk.outbound_call(
                    agent_id=Config.ELEVENLABS_AGENT_ID,
                    to_number=to_number,
                    agent_phone_number_id=agent_phone_number_id,
                    conversation_initiation_client_data=client_data
                )
                
                # Parse Response
                conversation_id = getattr(response, 'conversation_id', 'unknown')
                call_status = getattr(response, 'status', 'initiated')
                
                logger.info(f"✅ Call erfolgreich gestartet!")
                logger.info(f"📞 Conversation ID: {conversation_id}")
                logger.info(f"📊 Status: {call_status}")
                logger.info(f"{'='*70}\n")
                
                # Response zurück an HOC
                return jsonify({
                    "status": "success",
                    "method": "sip_trunk_call",
                    "message": "Outbound call initiated successfully",
                    "data": {
                        "campaign_id": campaign_id,
                        "candidate": f"{first_name} {last_name}",
                        "company": company_name,
                        "to_number": to_number,
                        "conversation_id": conversation_id,
                        "call_status": call_status,
                        "questionnaire_loaded": bool(questionnaire),
                        "timestamp": datetime.now().isoformat(),
                        "prompt_length": len(enhanced_prompt),
                        "first_message": first_message
                    }
                }), 200
                
            except Exception as api_error:
                logger.error(f"❌ ElevenLabs API Error: {api_error}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "error": "API call failed",
                    "message": str(api_error),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        else:
            # 🔗 OPTION B: WEBRTC LINK (Fallback)
            logger.info(f"\n{'='*70}")
            logger.info(f"🔗 ERSTELLE WEBRTC LINK (Kein to_number vorhanden)")
            logger.info(f"{'='*70}")
            
            try:
                # Hole direkt Signed URL (Conversation wird automatisch erstellt)
                # HINWEIS: conversation_config_override wird NICHT unterstützt bei WebRTC Links!
                # Die Conversation nutzt die Dashboard-Konfiguration
                logger.info("ℹ️  WebRTC Links nutzen Dashboard-Konfiguration (kein Override möglich)")
                
                signed_result = client.conversational_ai.conversations.get_signed_url(
                    agent_id=Config.ELEVENLABS_AGENT_ID
                )
                
                signed_url = getattr(signed_result, 'url', None)
                
                if signed_url:
                    logger.info(f"✅ WebRTC Link erstellt!")
                    logger.info(f"🔗 Signed URL: {signed_url[:80]}...")
                    logger.info(f"{'='*70}\n")
                    
                    return jsonify({
                        "status": "success",
                        "method": "webrtc_link",
                        "message": "WebRTC link created successfully",
                        "data": {
                            "campaign_id": campaign_id,
                            "candidate": f"{first_name} {last_name}",
                            "company": company_name,
                            "signed_url": signed_url,
                            "questionnaire_loaded": bool(questionnaire),
                            "timestamp": datetime.now().isoformat(),
                            "note": "WebRTC links use Dashboard configuration (override not supported)"
                        }
                    }), 200
                else:
                    raise AttributeError('Could not get signed URL')
                    
            except Exception as api_error:
                logger.error(f"❌ WebRTC Link Error: {api_error}", exc_info=True)
                
                # Fallback: Erstelle URL mit Query-Parametern
                logger.warning("⚠️  Fallback: Erstelle URL mit Query-Parametern")
                
                questionnaire_context = build_questionnaire_context(questionnaire, company_name, first_name, last_name)
                params = {
                    'agent_id': Config.ELEVENLABS_AGENT_ID,
                    'companyname': company_name,
                    'candidatefirst_name': first_name,
                    'candidatelast_name': last_name,
                    'questionnaire_context': questionnaire_context[:500]  # Begrenzt wg. URL-Länge
                }
                signed_url = f"https://eu.residency.elevenlabs.io/app/talk-to?{urlencode(params)}"
                
                logger.info(f"✅ Fallback URL erstellt")
                logger.info(f"🔗 URL: {signed_url[:80]}...")
                logger.info(f"{'='*70}\n")
                
                return jsonify({
                    "status": "success",
                    "method": "webrtc_link_fallback",
                    "message": "WebRTC link created (fallback mode)",
                    "data": {
                        "campaign_id": campaign_id,
                        "candidate": f"{first_name} {last_name}",
                        "company": company_name,
                        "conversation_id": None,
                        "signed_url": signed_url,
                        "questionnaire_loaded": bool(questionnaire),
                        "timestamp": datetime.now().isoformat(),
                        "fallback": True
                    }
                }), 200
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Call: {e}", exc_info=True)
        
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health Check Endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Sellcruiting Agent Webhook",
        "agent_id": Config.ELEVENLABS_AGENT_ID,
        "hirings_api_url": Config.HIRINGS_API_URL,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/webhook/create-webrtc-link', methods=['POST'])
@require_api_key
def create_webrtc_link():
    try:
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request format",
                "message": "Request body must be a JSON object"
            }), 400

        required_fields = ['campaign_id', 'company_name', 'candidate_first_name', 'candidate_last_name']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing
            }), 400

        campaign_id = int(data['campaign_id'])
        company_name = data['company_name']
        first_name = data['candidate_first_name']
        last_name = data['candidate_last_name']
        override_prompt = data.get('override_prompt')

        questionnaire = fetch_questionnaire_context(campaign_id)
        enhanced_prompt = override_prompt if override_prompt else build_enhanced_prompt(
            questionnaire=questionnaire,
            company_name=company_name,
            first_name=first_name,
            last_name=last_name
        )
        campaign_location = (
            questionnaire.get('campaignlocation_label', '') or 
            questionnaire.get('work_location', '') or 
            questionnaire.get('location', '') or
            (f"{questionnaire.get('work_location', '')} {questionnaire.get('work_location_postal_code', '')}".strip())
        )
        first_message = build_first_message(company_name, first_name, last_name, campaign_location)

        try:
            conv = client.conversational_ai.conversations.create(
                agent_id=Config.ELEVENLABS_AGENT_ID,
                agent_override={
                    "prompt": {"prompt": enhanced_prompt},
                    "first_message": first_message
                }
            )
            conversation_id = getattr(conv, 'id', getattr(conv, 'conversation_id', None))
            signed_result = None
            if hasattr(client.conversational_ai.conversations, 'get_signed_url'):
                signed_result = client.conversational_ai.conversations.get_signed_url(conversation_id=conversation_id)
                signed_url = getattr(signed_result, 'url', signed_result)
                return jsonify({
                    "status": "success",
                    "conversation_id": conversation_id,
                    "signed_url": signed_url,
                    "questionnaire_loaded": bool(questionnaire),
                    "timestamp": datetime.now().isoformat()
                }), 200
            else:
                raise AttributeError('get_signed_url not available')
        except Exception:
            try:
                with open('dashboard_prompt.txt', 'r', encoding='utf-8') as f:
                    _ = f.read()
            except Exception:
                pass
            questionnaire_context = build_questionnaire_context(questionnaire, company_name, first_name, last_name)
            params = {
                'agent_id': Config.ELEVENLABS_AGENT_ID,
                'companyname': company_name,
                'candidatefirst_name': first_name,
                'candidatelast_name': last_name,
                'questionnaire_context': questionnaire_context
            }
            signed_url = f"https://eu.residency.elevenlabs.io/app/talk-to?{urlencode(params)}"
            return jsonify({
                "status": "success",
                "conversation_id": None,
                "signed_url": signed_url,
                "fallback": True,
                "questionnaire_loaded": bool(questionnaire),
                "timestamp": datetime.now().isoformat()
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/webhook/test-questionnaire/<int:campaign_id>', methods=['GET'])
def test_questionnaire_fetch(campaign_id):
    """Test-Endpoint um Questionnaire-Abruf zu testen"""
    questionnaire = fetch_questionnaire_context(campaign_id)
    
    if questionnaire:
        return jsonify({
            "status": "success",
            "campaign_id": campaign_id,
            "questionnaire": questionnaire
        }), 200
    else:
        return jsonify({
            "status": "error",
            "campaign_id": campaign_id,
            "message": "Questionnaire not found or error fetching"
        }), 404


if __name__ == '__main__':
    print(f"""
{'='*70}
🎙️  SELLCRUITING AGENT - WEBHOOK RECEIVER
{'='*70}

Agent ID: {Config.ELEVENLABS_AGENT_ID}
Environment: PRODUCTION_EU (DSGVO-konform)
HIRINGS API: {Config.HIRINGS_API_URL}/api/v1/questionnaire/<campaign_id>

Endpoints:
  POST /webhook/trigger-call                 - Empfängt Call-Request
  GET  /webhook/health                       - Health Check
  GET  /webhook/test-questionnaire/<id>     - Test Questionnaire-Abruf

Server startet auf: http://0.0.0.0:5000
{'='*70}
""")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
