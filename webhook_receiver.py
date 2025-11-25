"""
Webhook Receiver für HOC → ElevenLabs Outbound Calls
Empfängt Call-Trigger von HOC und startet personalisierten Agent-Call
Nutzt campaign_id um Questionnaire/Kontext aus HOC zu laden
"""
import sys
import io
from flask import Flask, request, jsonify
from elevenlabs import ElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
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


def build_enhanced_prompt(questionnaire: dict, company_name: str, first_name: str, last_name: str) -> str:
    """
    Erstellt erweiterten System-Prompt mit Questionnaire-Kontext
    Nutzt den Dashboard-Prompt als Basis und ergänzt ihn mit Kontext
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        company_name: Firmenname
        first_name: Vorname Kandidat
        last_name: Nachname Kandidat
        
    Returns:
        Erweiterter System-Prompt
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
    
    # Ersetze Platzhalter im Dashboard-Prompt
    dashboard_prompt = dashboard_prompt.replace('{{companyname}}', company_name)
    dashboard_prompt = dashboard_prompt.replace('{{candidatefirst_name}}', first_name)
    dashboard_prompt = dashboard_prompt.replace('{{candidatelast_name}}', last_name)
    
    # Ersetze weitere Platzhalter falls vorhanden (aus dynamic_variables)
    # Diese werden später im override_agent_settings gesetzt
    # Hier nur die Basis-Platzhalter ersetzen
    
    # KONTEXT: Questionnaire-Daten hinzufügen
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
        
        if questionnaire.get('description'):
            questionnaire_context += f"\n\nBeschreibung:\n{questionnaire['description']}"
        
        if questionnaire.get('job_requirements'):
            questionnaire_context += f"\n\nAnforderungen:\n{questionnaire['job_requirements']}"
        
        if questionnaire.get('work_location') or questionnaire.get('office_address'):
            location = questionnaire.get('work_location') or questionnaire.get('office_address')
            questionnaire_context += f"\n\nArbeitsplatz-Standort: {location}"
        
        if questionnaire.get('work_location_postal_code'):
            questionnaire_context += f"\nPostleitzahl des Arbeitsplatzes: {questionnaire['work_location_postal_code']}"
        
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
    
    # FINALER PROMPT: Dashboard-Prompt + Questionnaire-Kontext
    # Die spezifischen Fragen (Wohnort, Arbeitsweg, Tätigkeiten, Weiterbildung) 
    # sind jetzt direkt im dashboard_prompt.txt integriert
    final_prompt = dashboard_prompt + questionnaire_context
    
    logger.info(f"📝 Prompt erstellt: {len(final_prompt)} Zeichen (Dashboard: {len(dashboard_prompt)}, Kontext: {len(questionnaire_context)})")
    
    return final_prompt


@app.route('/webhook/trigger-call', methods=['POST'])
def trigger_outbound_call():
    """
    Webhook Endpoint: Empfängt Call-Request von HOC und startet Outbound Call
    
    Erwartet JSON:
    {
        "campaign_id": 123,
        "company_name": "Tech Startup GmbH",
        "candidate_first_name": "Max",
        "candidate_last_name": "Mustermann",
        "to_number": "+491234567890",
        "agent_phone_number_id": "phnum_4901ka8wj2cjexfvpwwhnp9v94t9" (optional)
    }
    """
    try:
        # Parse Request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validiere erforderliche Felder
        required_fields = ['campaign_id', 'company_name', 'candidate_first_name', 
                          'candidate_last_name', 'to_number']
        
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
        to_number = data['to_number']
        agent_phone_number_id = data.get(
            'agent_phone_number_id', 
            'phnum_4801kateq1q7e61art2qbne1wgr3'  # Xelion Nummer (053138823189)
        )
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📞 NEUE CALL-ANFRAGE VON HOC")
        logger.info(f"{'='*70}")
        logger.info(f"⏰ Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📋 Campaign-ID: {campaign_id}")
        logger.info(f"👤 Kandidat: {first_name} {last_name}")
        logger.info(f"🏢 Firma: {company_name}")
        logger.info(f"📞 Nummer: {to_number}")
        
        # 1. Hole Questionnaire aus HOC
        logger.info(f"\n🔄 Lade Questionnaire für Campaign {campaign_id}...")
        questionnaire = fetch_questionnaire_context(campaign_id)
        
        if not questionnaire:
            logger.warning(f"⚠️  Kein Questionnaire gefunden, fahre mit Basis-Prompt fort")
        
        # 2. Baue erweiterten Prompt mit Questionnaire-Kontext
        enhanced_prompt = build_enhanced_prompt(
            questionnaire=questionnaire,
            company_name=company_name,
            first_name=first_name,
            last_name=last_name
        )
        
        logger.info(f"📝 Prompt erstellt: {len(enhanced_prompt)} Zeichen")
        
        # 3. Bereite Dynamic Variables vor
        dynamic_variables = {
            "companyname": company_name,
            "candidatefirst_name": first_name,
            "candidatelast_name": last_name,
            "campaign_id": str(campaign_id),
            # Optional: Zusätzliche Variablen aus Questionnaire
            "position": questionnaire.get('position', ''),
            "department": questionnaire.get('department', ''),
            "campaign_title": questionnaire.get('title', '')
        }
        
        # 4. Starte Outbound Call
        logger.info(f"\n📞 Starte Outbound Call...")
        
        # WICHTIG: SDK unterstützt aktuell KEIN override_agent_settings bei outbound_call
        # Dynamic Variables werden über conversation_initiation_client_data übergeben
        # Prompt-Customization muss im Dashboard konfiguriert werden mit {{variable}} Platzhaltern
        
        resp = client.conversational_ai.sip_trunk.outbound_call(
            agent_id=Config.ELEVENLABS_AGENT_ID,
            agent_phone_number_id=agent_phone_number_id,
            to_number=to_number,
            conversation_initiation_client_data=dynamic_variables
        )
        
        logger.info(f"✅ Call erfolgreich gestartet!")
        logger.info(f"{'='*70}\n")
        
        # Response zurück an HOC
        return jsonify({
            "status": "success",
            "message": "Outbound call started successfully",
            "data": {
                "campaign_id": campaign_id,
                "candidate": f"{first_name} {last_name}",
                "company": company_name,
                "to_number": to_number,
                "conversation_id": getattr(resp, 'conversation_id', None),
                "questionnaire_loaded": bool(questionnaire),
                "timestamp": datetime.now().isoformat()
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
