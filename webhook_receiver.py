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
from config import Config
import requests
from datetime import datetime
import logging
from openai import OpenAI

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix Windows Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)

# ElevenLabs Client mit EU Base URL (für Twilio Outbound Calls)
client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY,
    base_url="https://api.eu.residency.elevenlabs.io"
)

# OpenAI Client konfigurieren
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)


def extract_with_ai(questions: list, variable_name: str) -> str:
    """
    Nutzt OpenAI GPT-4o-mini, um eine Dynamic Variable aus Fragen zu extrahieren
    
    Args:
        questions: Liste der Fragen aus HOC
        variable_name: Name der zu extrahierenden Variable
        
    Returns:
        Extrahierter Wert als String oder ""
    """
    
    if not questions or not Config.OPENAI_API_KEY:
        return ""
    
    # Formatiere Fragen für AI
    questions_text = "\n".join([
        f"- {q.get('question', '')} (Priority: {q.get('priority', 'N/A')}, Group: {q.get('group', 'N/A')}, Context: {q.get('context', 'N/A')})"
        for q in questions
    ])
    
    # Prompts pro Variable
    prompts = {
        "campaignlocation_label": f"""
Analysiere diese Recruiting-Fragen und extrahiere NUR den ARBEITSORT (Stadt/Stadtteil):

{questions_text}

WICHTIG:
- Gib NUR die Stadt oder den Stadtteil zurück (z.B. "Berlin-Hellersdorf" oder "München")
- NICHT die komplette Adresse mit Straße und Hausnummer
- Falls mehrere Standorte: Wähle den Hauptstandort
- Falls kein Standort erkennbar: Antworte mit einem leeren String

Beispiel:
Frage: "Unser Standort ist Kita Springmäuse, Stollberger Straße 25-27, 12627 Berlin."
Antwort: "Berlin"

Frage: "Der Arbeitsort ist München-Schwabing, Leopoldstraße 50."
Antwort: "München-Schwabing"
""",
        
        "companypriorities": f"""
Analysiere diese Recruiting-Fragen und extrahiere die TOP 3-4 WICHTIGSTEN ANFORDERUNGEN/PRIORITÄTEN:

{questions_text}

Fokus auf:
- Qualifikationen mit Priority=1 oder "Muss-Kriterium" im Context
- Arbeitszeitmodelle (Vollzeit/Teilzeit)
- Zentrale fachliche Anforderungen

Format: Kommaseparierte Liste (z.B. "Deutschkenntnisse B2, mehrjährige Berufserfahrung, Vollzeit 39h")
Falls keine klaren Prioritäten erkennbar: Antworte mit einem leeren String
""",
        
        "companysize": f"""
Analysiere diese Recruiting-Fragen und extrahiere die UNTERNEHMENSGRÖSSE:

{questions_text}

Suche nach Hinweisen auf:
- Anzahl Mitarbeitende
- Größe des Unternehmens

Falls gefunden: Gib zurück im Format "ca. X Mitarbeitende" oder "X Mitarbeiter"
Falls nicht gefunden: Antworte mit einem leeren String
""",
        
        "companypitch": f"""
Analysiere diese Recruiting-Fragen und erstelle einen KURZEN COMPANY PITCH (1-2 Sätze):

{questions_text}

Erstelle basierend auf erkennbaren Informationen (Branche, Besonderheiten, Benefits) einen professionellen Pitch.
Falls zu wenig Information verfügbar: Antworte mit einem leeren String
""",
        
        "campaignrole_title": f"""
Analysiere diese Recruiting-Fragen und extrahiere die BERUFSBEZEICHNUNG/JOBTITEL:

{questions_text}

Suche nach Hinweisen auf:
- Berufsbezeichnung (z.B. "Pflegefachkraft", "Erzieher", "Leitungskraft")
- Position/Rolle (z.B. "Wohnbereichsleitung", "Kitaleitung")
- Fachrichtung (z.B. "Sozialpädagoge", "Gesundheits- und Krankenpfleger")

WICHTIG:
- Gib NUR die Berufsbezeichnung zurück (z.B. "Pflegefachkraft" oder "Kitaleitung")
- KEINE Artikel (nicht "die Pflegefachkraft", sondern "Pflegefachkraft")
- Falls mehrere Berufe erkennbar: Wähle den Hauptberuf
- Falls kein Jobtitel erkennbar: Antworte mit "Fachkraft"

Beispiele:
- Fragen über "staatlich anerkannter Erzieher" → "Erzieher"
- Fragen über "Wohnbereichsleitung" → "Wohnbereichsleitung"
- Fragen über "Pflegefachkraft" → "Pflegefachkraft"
"""
    }
    
    prompt = prompts.get(variable_name, "")
    if not prompt:
        return ""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Recruiting-Datenextraktion. Antworte präzise, kurz und direkt. Keine Erklärungen, nur das Ergebnis."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=150,
            timeout=10
        )
        
        result = response.choices[0].message.content.strip()
        
        # Entferne Anführungszeichen falls vorhanden
        result = result.strip('"').strip("'")
        
        logger.info(f"✅ AI-Extraktion für {variable_name}: {result[:50]}...")
        return result
        
    except Exception as e:
        logger.warning(f"⚠️ AI-Extraktion für {variable_name} fehlgeschlagen: {e}")
        return ""


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


def parse_json_response(response_text: str) -> dict:
    """
    Transformiert und validiert JSON-Response von HOC API
    
    Handhabt verschiedene Response-Formate:
    - Reines JSON
    - JSON in HTML eingebettet
    - Text mit JSON-Inhalt
    
    Args:
        response_text: Roher Response-Text von HOC API
        
    Returns:
        Parsed JSON als dict oder leeres dict bei Fehler
    """
    import re
    
    if not response_text or not response_text.strip():
        logger.warning("⚠️  Leere Response von HOC API")
        return {}
    
    # Versuche direktes JSON-Parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Versuche JSON aus HTML zu extrahieren
    # Suche nach <script> Tags mit JSON
    script_pattern = r'<script[^>]*>.*?(\{.*?\}).*?</script>'
    matches = re.findall(script_pattern, response_text, re.DOTALL | re.IGNORECASE)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # Entferne HTML-Tags und versuche erneut
    cleaned = re.sub(r'<[^>]+>', '', response_text)
    cleaned = cleaned.strip()
    
    # Suche nach JSON-Objekt im Text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, cleaned, re.DOTALL)
    
    for json_str in json_matches:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and 'questions' in parsed:
                logger.info("✅ JSON aus bereinigter Response extrahiert")
                return parsed
        except json.JSONDecodeError:
            continue
    
    logger.error(f"❌ Konnte kein gültiges JSON aus Response extrahieren")
    logger.debug(f"Response Preview: {response_text[:200]}...")
    return {}


def fetch_questionnaire_context(campaign_id: int) -> dict:
    """
    Holt Questionnaire/Kontextdatei aus HOC basierend auf Campaign-ID
    
    Mit robuster JSON-Transformation und Validierung
    
    Args:
        campaign_id: Campaign ID für den Fragebogen
        
    Returns:
        dict mit Questionnaire-Daten und Kontext
    """
    try:
        headers = {
            "Authorization": Config.HIRINGS_API_TOKEN,  # ⚠️ OHNE "Bearer" - HOC API benötigt direkten Token!
            "Content-Type": "application/json"
        }
        
        # HIRINGS API Endpunkt: questionnaire/<campaign_id>
        # HIRINGS_API_URL enthält bereits /api/v1
        url = f"{Config.HIRINGS_API_URL}/questionnaire/{campaign_id}"
        
        logger.info(f"📥 Lade Questionnaire von HOC: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # ✅ NEU: Prüfe Content-Type
        content_type = response.headers.get('Content-Type', '')
        logger.info(f"📋 Content-Type: {content_type}")
        
        # ✅ NEU: Verwende JSON-Transformator
        questionnaire = parse_json_response(response.text)
        
        # ✅ NEU: Validierung der Struktur
        if not isinstance(questionnaire, dict):
            logger.error(f"❌ Questionnaire ist kein Dict! Type: {type(questionnaire)}")
            logger.error(f"   Response Preview: {response.text[:200]}...")
            return {}
        
        # ✅ NEU: Prüfe ob questions vorhanden
        questions = questionnaire.get('questions', [])
        if not questions:
            logger.warning(f"⚠️  Campaign {campaign_id}: 'questions' Array ist leer oder fehlt!")
            logger.warning(f"   Verfügbare Keys: {list(questionnaire.keys())}")
            logger.warning(f"   Content-Type war: {content_type}")
        else:
            logger.info(f"✅ Questionnaire erfolgreich geladen für Campaign: {campaign_id}")
            logger.info(f"   📊 {len(questions)} Fragen gefunden")
            
            # Zeige Priority-Verteilung
            priority_1 = len([q for q in questions if q.get('priority') == 1])
            priority_2 = len([q for q in questions if q.get('priority') == 2])
            logger.info(f"   📋 Priority 1: {priority_1}, Priority 2: {priority_2}")
        
        return questionnaire
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP Fehler beim Laden des Questionnaires (Campaign {campaign_id}): {e}")
        if e.response:
            logger.error(f"   Status Code: {e.response.status_code}")
            logger.error(f"   Response: {e.response.text[:200]}")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Fehler beim Laden des Questionnaires (Campaign {campaign_id}): {e}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Parse Fehler (Campaign {campaign_id}): {e}")
        logger.error(f"   Response Preview: {response.text[:200] if 'response' in locals() else 'N/A'}...")
        return {}
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler beim Laden des Questionnaires (Campaign {campaign_id}): {e}")
        import traceback
        logger.error(traceback.format_exc())
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


def extract_variable_with_ai(questions: list, variable_name: str) -> str:
    """
    Nutzt OpenAI GPT-4o-mini, um eine Dynamic Variable aus den Fragen zu extrahieren
    
    Args:
        questions: Liste von Fragen aus HOC Questionnaire
        variable_name: Name der zu extrahierenden Variable
        
    Returns:
        Extrahierter Wert als String oder "" falls nicht extrahierbar
    """
    try:
        # Prüfe OpenAI API Key
        if not Config.OPENAI_API_KEY:
            logger.warning("⚠️ OpenAI API Key nicht konfiguriert - AI-Extraktion übersprungen")
            return ""
        
        # Formatiere Fragen für AI
        questions_text = "\n".join([
            f"- Frage: {q.get('question', '')}\n  Gruppe: {q.get('group', 'N/A')}\n  Priority: {q.get('priority', 'N/A')}\n  Context: {q.get('context', 'N/A')}"
            for q in questions
        ])
        
        # AI-Prompts pro Variable
        prompts = {
            "campaignlocation_label": f"""Analysiere diese Recruiting-Fragen und extrahiere den ARBEITSORT/STANDORT:

{questions_text}

WICHTIG: Extrahiere NUR den ORT/DIE STADT (z.B. "Berlin", "München-Schwabing", "Hamburg-Altona").
NICHT die komplette Adresse mit Straße und Hausnummer!

Beispiele:
- "Unser Standort ist Kita Springmäuse, Stollberger Straße 25-27, 12627 Berlin" → "Berlin"
- "Der Arbeitsort ist München-Schwabing, Leopoldstraße 123" → "München-Schwabing"
- "Arbeiten Sie in Hamburg-Altona?" → "Hamburg-Altona"

Antworte NUR mit dem Ort, ohne Erklärung.
Falls kein Standort erkennbar: Antworte mit einem leeren String.""",
            
            "companypriorities": f"""Analysiere diese Recruiting-Fragen und identifiziere die TOP 3-4 MUSS-KRITERIEN oder PRIORITÄTEN:

{questions_text}

Fokus auf:
- Fragen mit Priority=1 (Muss-Kriterien)
- Context-Felder mit "Muss-Kriterium:"
- Qualifikationen und Abschlüsse
- Arbeitszeitmodelle (Vollzeit/Teilzeit)

Gib die Prioritäten als kommaseparierte Liste zurück (max. 4 Items).
Format: "Kriterium 1, Kriterium 2, Kriterium 3"

Beispiel: "Deutschkenntnisse B2, mehrjährige Berufserfahrung, staatlich anerkannter Abschluss, Vollzeit 39h"

Falls keine klaren Prioritäten: Antworte mit einem leeren String.""",
            
            "companysize": f"""Analysiere diese Recruiting-Fragen und extrahiere die UNTERNEHMENSGRÖSSE (Mitarbeiterzahl):

{questions_text}

Suche nach Angaben zur Mitarbeiterzahl oder Unternehmensgröße.

Beispiele:
- "Wir sind ein Unternehmen mit 120 Mitarbeitenden" → "120 Mitarbeitende"
- "Unser Team hat ca. 50 Mitarbeiter" → "ca. 50 Mitarbeiter"

Falls keine Angabe vorhanden: Antworte mit einem leeren String.""",
            
            "companypitch": f"""Analysiere diese Recruiting-Fragen und erstelle einen kurzen COMPANY PITCH (2-3 Sätze):

{questions_text}

Erstelle basierend auf erkennbaren Informationen (Branche, Besonderheiten, Benefits, Arbeitszeitmodelle) einen professionellen Pitch.

Format: 2-3 prägnante Sätze
Stil: Professionell und einladend

Falls zu wenig Information erkennbar: Antworte mit einem leeren String."""
        }
        
        # Hole Prompt für die Variable
        prompt = prompts.get(variable_name, "")
        if not prompt:
            logger.warning(f"⚠️ Kein AI-Prompt für Variable '{variable_name}' definiert")
            return ""
        
        logger.info(f"🤖 Starte AI-Extraktion für: {variable_name}")
        
        # OpenAI API Call (neue SDK Syntax)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Schnell & günstig (~$0.15/1M tokens)
            messages=[
                {"role": "system", "content": "Du bist ein Experte für Recruiting-Datenextraktion. Antworte präzise, kurz und ohne Erklärungen."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Deterministisch
            max_tokens=150,
            timeout=10
        )
        
        result = response.choices[0].message.content.strip()
        
        # Bereinige Ergebnis
        if result.lower() in ['', 'nicht vorhanden', 'keine angabe', 'n/a', 'null', 'none']:
            result = ""
        
        logger.info(f"✅ AI-Extraktion für {variable_name}: {result[:100] if result else '(leer)'}...")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ AI-Extraktion für {variable_name} fehlgeschlagen: {e}")
        return ""


def extract_company_size(questionnaire: dict) -> str:
    """
    Extrahiert Mitarbeiterzahl - AI-basiert aus questions Array
    """
    questions = questionnaire.get('questions', [])
    if not questions:
        return ""
    
    return extract_variable_with_ai(questions, "companysize")


def extract_company_pitch(questionnaire: dict) -> str:
    """
    Extrahiert Company Pitch - AI-basiert aus questions Array
    """
    questions = questionnaire.get('questions', [])
    if not questions:
        return ""
    
    return extract_variable_with_ai(questions, "companypitch")


def extract_location(questionnaire: dict) -> str:
    """
    Extrahiert Standort (NUR ORT/STADT) - AI-basiert aus questions Array
    """
    questions = questionnaire.get('questions', [])
    if not questions:
        # Fallback: Direkte Felder prüfen
        if questionnaire.get('campaignlocation_label'):
            return questionnaire['campaignlocation_label']
        if questionnaire.get('work_location'):
            return questionnaire['work_location']
        return ""
    
    return extract_variable_with_ai(questions, "campaignlocation_label")


def extract_priorities(questionnaire: dict) -> str:
    """
    Extrahiert Prioritäten aus MUSS-Kriterien - AI-basiert aus questions Array
    """
    questions = questionnaire.get('questions', [])
    if not questions:
        return ""
    
    return extract_variable_with_ai(questions, "companypriorities")


def build_questions_list(questionnaire: dict) -> str:
    """
    Erstellt strukturierte Fragenliste für Phase 3 (Dashboard)
    ALLE Fragen kombiniert
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        
    Returns:
        Formatierte Fragenliste als String
    """
    try:
        questions_text = "=== ALLE FRAGEN (Überblick) ===\n\n"
        
        if questionnaire.get('questions'):
            questions = questionnaire['questions']
            
            # Gruppiere nach Kategorien
            must_questions = [q for q in questions if q.get('priority') == 1]
            optional_questions = [q for q in questions if q.get('priority') == 2]
            
            if must_questions:
                questions_text += "MUSS-FRAGEN (Priority 1):\n"
                for i, q in enumerate(must_questions, 1):
                    question_text = q.get('question', '')
                    context = q.get('context', '')
                    questions_text += f"{i}. {question_text}\n"
                    if context:
                        questions_text += f"   (Hinweis: {context})\n"
                questions_text += "\n"
            
            if optional_questions:
                questions_text += "ZUSÄTZLICHE FRAGEN (Priority 2):\n"
                for i, q in enumerate(optional_questions, 1):
                    question_text = q.get('question', '')
                    questions_text += f"{i}. {question_text}\n"
        
        return questions_text
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Erstellen der Fragenliste: {e}")
        return ""


def build_gate_questions(questionnaire: dict) -> str:
    """
    Erstellt Liste der MUSS-Fragen (Priority=1) für Phase 1 (Gate)
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        
    Returns:
        Formatierte Liste nur der Priority=1 Fragen
    """
    try:
        gate_text = "=== MUSS-KRITERIEN (Gate) für Phase 1 ===\n\n"
        gate_text += "Diese Fragen MÜSSEN in Phase 1 gestellt werden.\n"
        gate_text += "Bei Nichterfüllung: Gespräch beenden!\n\n"
        
        if questionnaire.get('questions'):
            questions = questionnaire['questions']
            
            # Nur Priority=1 Fragen
            must_questions = [q for q in questions if q.get('priority') == 1]
            
            if must_questions:
                for i, q in enumerate(must_questions, 1):
                    question_text = q.get('question', '')
                    question_type = q.get('question_type', 'boolean').upper()
                    context = q.get('context', '')
                    preamble = q.get('preamble', '')
                    
                    gate_text += f"{i}. [{question_type}] {question_text}\n"
                    
                    if context:
                        gate_text += f"   → Kontext: {context}\n"
                    if preamble:
                        gate_text += f"   → Preamble: \"{preamble}\"\n"
                    
                    gate_text += "\n"
                
                gate_text += "⚠️ BEI NICHTERFÜLLUNG:\n"
                gate_text += "\"Vielen Dank für Ihre Offenheit. Für diese Position ist [Kriterium] zwingend erforderlich.\n"
                gate_text += "Deshalb können wir das Gespräch hier leider nicht fortsetzen. Alles Gute für Ihre weitere Suche.\"\n"
            else:
                gate_text += "(Keine Muss-Kriterien definiert)\n"
        else:
            gate_text += "(Keine Fragen vorhanden)\n"
        
        logger.info(f"✅ Gate Questions erstellt: {len([q for q in questionnaire.get('questions', []) if q.get('priority') == 1])} Fragen")
        return gate_text
        
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Erstellen der Gate Questions: {e}")
        return ""


def build_preference_questions(questionnaire: dict) -> str:
    """
    Erstellt Liste der Präferenz-Fragen (Priority=2) für Phase 3
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        
    Returns:
        Formatierte Liste nur der Priority=2 Fragen
    """
    try:
        pref_text = "=== PRÄFERENZEN & WÜNSCHE für Phase 3 ===\n\n"
        pref_text += "Diese Fragen werden in Phase 3 gestellt.\n"
        pref_text += "Nutze Preamble als Einleitung, falls vorhanden!\n\n"
        
        if questionnaire.get('questions'):
            questions = questionnaire['questions']
            
            # Nur Priority=2 Fragen
            optional_questions = [q for q in questions if q.get('priority') == 2]
            
            if optional_questions:
                for i, q in enumerate(optional_questions, 1):
                    question_text = q.get('question', '')
                    question_type = q.get('question_type', 'boolean').upper()
                    preamble = q.get('preamble', '')
                    help_text = q.get('help_text', '')
                    options = q.get('options', None)
                    
                    pref_text += f"{i}. [{question_type}] {question_text}\n"
                    
                    if preamble:
                        pref_text += f"   → Preamble: \"{preamble}\" (Nutze als Einleitung!)\n"
                    if help_text:
                        pref_text += f"   → Help Text: {help_text}\n"
                    if options:
                        pref_text += f"   → Optionen: {options}\n"
                    
                    pref_text += "\n"
            else:
                pref_text += "(Keine optionalen Fragen definiert)\n"
        else:
            pref_text += "(Keine Fragen vorhanden)\n"
        
        logger.info(f"✅ Preference Questions erstellt: {len([q for q in questionnaire.get('questions', []) if q.get('priority') == 2])} Fragen")
        return pref_text
        
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Erstellen der Preference Questions: {e}")
        return ""


def extract_dynamic_variables(questionnaire: dict, company_name: str, first_name: str, last_name: str) -> dict:
    """
    Extrahiert alle Dynamic Variables aus dem HOC Questionnaire
    für ElevenLabs Dashboard-Workflows
    
    NUTZT AI (GPT-4o-mini) für intelligente Extraktion aus questions Array
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC
        company_name: Firmenname
        first_name: Vorname Kandidat
        last_name: Nachname Kandidat
        
    Returns:
        Dict mit allen Dynamic Variables für ElevenLabs
    """
    logger.info("🔍 Extrahiere Dynamic Variables aus Questionnaire (AI-basiert)...")
    
    # BASIS-VARIABLEN (immer vorhanden)
    variables = {
        "candidatefirst_name": first_name,
        "candidatelast_name": last_name,
        "companyname": company_name
    }
    
    # Hole questions Array
    questions = questionnaire.get('questions', [])
    
    # AI-BASIERTE EXTRAKTION
    if questions and len(questions) > 0:
        logger.info(f"📊 {len(questions)} Fragen gefunden - starte AI-Extraktion...")
        
        # Extrahiere mit AI (parallel möglich, aber sequential für Einfachheit)
        variables["campaignlocation_label"] = extract_with_ai(questions, "campaignlocation_label")
        variables["companypriorities"] = extract_with_ai(questions, "companypriorities")
        variables["companysize"] = extract_with_ai(questions, "companysize")
        variables["companypitch"] = extract_with_ai(questions, "companypitch")
        variables["campaignrole_title"] = extract_with_ai(questions, "campaignrole_title")  # NEU: AI-Extraktion für Job-Titel
    else:
        # ✅ WICHTIG: Keine Fragen im Questionnaire
        logger.warning("⚠️  Keine Fragen im Questionnaire - AI-Extraktion übersprungen")
        if questionnaire:
            logger.warning(f"   Questionnaire-Struktur: {list(questionnaire.keys())}")
            logger.warning(f"   'questions' Array: {questions if questions else 'leer oder fehlt'}")
            logger.warning(f"   → Campaign hat möglicherweise keine Fragen im HOC System konfiguriert")
        else:
            logger.warning(f"   → Questionnaire ist komplett leer")
        
        # Setze alle auf leere Strings (außer campaignrole_title mit Fallback)
        variables["campaignlocation_label"] = ""
        variables["companypriorities"] = ""
        variables["companysize"] = ""
        variables["companypitch"] = ""
        variables["campaignrole_title"] = "Ihre Position"  # Fallback
    
    # KONTEXT-VARIABLEN (strukturiert)
    variables["questionnaire_context"] = build_questionnaire_context(questionnaire, company_name, first_name, last_name)
    variables["questions"] = build_questions_list(questionnaire)
    
    # PHASEN-SPEZIFISCHE FRAGEN (NEU!)
    variables["gate_questions"] = build_gate_questions(questionnaire)  # Phase 1: MUSS-Kriterien
    variables["preference_questions"] = build_preference_questions(questionnaire)  # Phase 3: Präferenzen
    
    # Log welche Variablen gefüllt wurden
    filled_vars = [k for k, v in variables.items() if v]
    logger.info(f"✅ {len(filled_vars)}/{len(variables)} Dynamic Variables gefüllt:")
    for var in filled_vars:
        value_preview = str(variables[var])[:50]
        logger.info(f"   • {var}: {value_preview}...")
    
    return variables


def build_questionnaire_context(questionnaire: dict, company_name: str, first_name: str, last_name: str) -> str:
    """
    Erstellt Questionnaire-Kontext als formatierten Text
    
    Args:
        questionnaire: Questionnaire-Daten aus HOC (enthält 'questions' Array)
        company_name: Firmenname
        first_name: Vorname Kandidat
        last_name: Nachname Kandidat
        
    Returns:
        Questionnaire-Kontext als formatierter Text mit Fragen
    """
    
    # KONTEXT: Basis-Informationen
    questionnaire_context = f"""
===================================
KONTEXT AUS QUESTIONNAIRE:
===================================

Kandidat: {first_name} {last_name}
Firma: {company_name}
"""
    
    if questionnaire and questionnaire.get('questions'):
        questions = questionnaire['questions']
        
        # Gruppiere Fragen nach Kategorien
        questions_by_category = {}
        for q in questions:
            if isinstance(q, dict):
                category = q.get('category', 'general')
                group = q.get('group', 'Allgemein')
                
                if category not in questions_by_category:
                    questions_by_category[category] = {
                        'group': group,
                        'questions': []
                    }
                
                questions_by_category[category]['questions'].append(q)
        
        # Formatiere Fragen nach Kategorien
        questionnaire_context += f"\n\n📋 FRAGEN ZU KLÄREN ({len(questions)} insgesamt):\n"
        questionnaire_context += "="*50
        
        # Sortiere nach category_order wenn vorhanden
        sorted_categories = sorted(
            questions_by_category.items(),
            key=lambda x: x[1]['questions'][0].get('category_order', 99) if x[1]['questions'] else 99
        )
        
        for category, data in sorted_categories:
            group_name = data['group']
            category_questions = data['questions']
            
            questionnaire_context += f"\n\n🔹 {group_name.upper()}:"
            
            # Sortiere Fragen nach Priority (1 = wichtig, 2 = optional)
            must_questions = [q for q in category_questions if q.get('priority') == 1]
            optional_questions = [q for q in category_questions if q.get('priority') == 2]
            
            if must_questions:
                questionnaire_context += f"\n\n  ⚠️  MUSS-KRITERIEN:"
                for q in must_questions:
                    question_text = q.get('question', '')
                    context = q.get('context', '')
                    preamble = q.get('preamble', '')
                    
                    questionnaire_context += f"\n  • {question_text}"
                    if context:
                        questionnaire_context += f"\n    (Kontext: {context})"
                    if preamble:
                        questionnaire_context += f"\n    (Überleitung: {preamble})"
            
            if optional_questions:
                questionnaire_context += f"\n\n  ℹ️  ZUSÄTZLICHE FRAGEN:"
                for q in optional_questions:
                    question_text = q.get('question', '')
                    preamble = q.get('preamble', '')
                    
                    questionnaire_context += f"\n  • {question_text}"
                    if preamble:
                        questionnaire_context += f"\n    (Überleitung: {preamble})"
    
    questionnaire_context += "\n\n===================================\n"
    
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
        agent_phone_number_id = data.get('agent_phone_number_id')  # Optional, nur für SIP Trunk
        override_prompt = data.get('override_prompt')
        
        # Validiere agent_phone_number_id nur wenn to_number vorhanden (SIP Trunk)
        if to_number and not agent_phone_number_id:
            # Versuche aus Config zu holen
            agent_phone_number_id = Config.ELEVENLABS_AGENT_PHONE_NUMBER_ID if hasattr(Config, 'ELEVENLABS_AGENT_PHONE_NUMBER_ID') else None
            
            if not agent_phone_number_id:
                return jsonify({
                    "error": "Missing agent_phone_number_id",
                    "message": "Provide agent_phone_number_id in request for SIP trunk calls"
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
            # 📞 OPTION A: TWILIO OUTBOUND CALL (mit Personalisierung)
            logger.info(f"\n{'='*70}")
            logger.info(f"📞 STARTE TWILIO OUTBOUND CALL (mit voller Personalisierung)")
            logger.info(f"{'='*70}")
            
            try:
                # ✨ NEU: Extrahiere ALLE Dynamic Variables aus Questionnaire
                dynamic_vars = extract_dynamic_variables(questionnaire, company_name, first_name, last_name)
                
                logger.info(f"📊 {len(dynamic_vars)} Dynamic Variables extrahiert:")
                for key in dynamic_vars.keys():
                    value_preview = str(dynamic_vars[key])[:50] if dynamic_vars[key] else "(leer)"
                    logger.info(f"   • {key}: {value_preview}...")
                
                # WICHTIG: Nutze twilio.outbound_call mit DIRECT DICT
                # OPTION A: Nur Dynamic Variables (Dashboard-Workflows werden genutzt!)
                response = client.conversational_ai.twilio.outbound_call(
                    agent_id=Config.ELEVENLABS_AGENT_ID,
                    agent_phone_number_id=agent_phone_number_id,
                    to_number=to_number,
                    conversation_initiation_client_data={
                        "dynamic_variables": dynamic_vars
                        # KEIN conversation_config_override → Dashboard-Workflows bleiben aktiv!
                    }
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
                    "method": "twilio_outbound_call",
                    "message": "Twilio outbound call initiated successfully with Dashboard Workflows + Dynamic Variables",
                    "data": {
                        "campaign_id": campaign_id,
                        "candidate": f"{first_name} {last_name}",
                        "company": company_name,
                        "to_number": to_number,
                        "conversation_id": conversation_id,
                        "call_status": call_status,
                        "questionnaire_loaded": bool(questionnaire),
                        "timestamp": datetime.now().isoformat(),
                        "dynamic_variables_count": len(dynamic_vars),
                        "dynamic_variables_filled": list(dynamic_vars.keys()),
                        "workflow_mode": "dashboard_workflows",
                        "note": "Using ElevenLabs Dashboard Workflows with injected Dynamic Variables"
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
            
            # WebRTC Links nutzen Dashboard-Konfiguration + Dynamic Variables via URL
            logger.info("ℹ️  WebRTC Links nutzen Dashboard-Konfiguration mit Dynamic Variables")
            
            try:
                # ✨ NEU: Extrahiere ALLE Dynamic Variables aus Questionnaire
                dynamic_vars_full = extract_dynamic_variables(questionnaire, company_name, first_name, last_name)
                
                # Füge Dynamic Variables als URL-Parameter hinzu
                # WICHTIG: var_ Prefix für ElevenLabs Public Talk-to Page!
                # Siehe: https://elevenlabs.io/docs/agents-platform/customization/personalization/dynamic-variables
                dynamic_vars = {
                    'agent_id': Config.ELEVENLABS_AGENT_ID,
                }
                
                # Füge alle Variablen mit var_ Prefix hinzu
                for key, value in dynamic_vars_full.items():
                    if value:  # Nur gefüllte Variablen
                        # Kürze große Variablen für URL (questionnaire_context, questions)
                        if key in ['questionnaire_context', 'questions'] and len(str(value)) > 500:
                            value = str(value)[:500] + "..."
                        dynamic_vars[f'var_{key}'] = value
                
                # Baue BROWSER-URL für ElevenLabs Public Talk-to Page
                param_string = urlencode(dynamic_vars)
                browser_url = f"https://elevenlabs.io/app/talk-to?{param_string}"
                
                logger.info(f"✅ WebRTC Browser-Link mit Dynamic Variables erstellt!")
                logger.info(f"📊 Dynamic Variables gefüllt: {len([k for k in dynamic_vars.keys() if k.startswith('var_')])}")
                logger.info(f"   • agent_id: {Config.ELEVENLABS_AGENT_ID}")
                for key in sorted([k for k in dynamic_vars.keys() if k.startswith('var_')]):
                    value_preview = str(dynamic_vars[key])[:40] if dynamic_vars[key] else "(leer)"
                    logger.info(f"   • {key}: {value_preview}...")
                logger.info(f"🔗 Browser URL: {browser_url[:120]}...")
                logger.info(f"📏 URL-Länge: {len(browser_url)} Zeichen")
                logger.info(f"{'='*70}\n")
                
                return jsonify({
                    "status": "success",
                    "method": "webrtc_browser_link",
                    "message": "WebRTC browser link created successfully with dynamic variables",
                    "data": {
                        "campaign_id": campaign_id,
                        "candidate": f"{first_name} {last_name}",
                        "company": company_name,
                        "browser_url": browser_url,
                        "questionnaire_loaded": bool(questionnaire),
                        "questions_count": len(questionnaire.get('questions', [])) if questionnaire else 0,
                        "timestamp": datetime.now().isoformat(),
                        "dynamic_variables_filled": list(dynamic_vars.keys()),
                        "note": "Browser-URL can be opened directly in any web browser"
                    }
                }), 200
                    
            except Exception as api_error:
                logger.error(f"❌ WebRTC Link Error: {api_error}", exc_info=True)
                
                return jsonify({
                    "status": "error",
                    "error": "WebRTC Link creation failed",
                    "message": str(api_error),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
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

@app.route('/webhook/twilio-personalization', methods=['POST'])
@require_api_key
def twilio_personalization():
    """
    ElevenLabs Twilio Personalization Webhook
    
    Wird von ElevenLabs aufgerufen, wenn ein eingehender Twilio-Call ankommt.
    Gibt personalisierte conversation_initiation_client_data zurück.
    
    Request (von ElevenLabs):
    {
        "caller_id": "+4915204465582",
        "agent_id": "agent_...",
        "called_number": "+123456...",
        "call_sid": "CA..."
    }
    
    Response:
    {
        "type": "conversation_initiation_client_data",
        "dynamic_variables": {...},
        "conversation_config_override": {...}
    }
    """
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"🔔 TWILIO PERSONALIZATION WEBHOOK AUFGERUFEN")
        logger.info(f"{'='*70}")
        
        # Parse incoming data
        data = request.get_json()
        logger.info(f"📥 Empfangene Daten: {json.dumps(data, indent=2)}")
        
        caller_id = data.get('caller_id')  # z.B. +4915204465582
        agent_id = data.get('agent_id')
        called_number = data.get('called_number')
        call_sid = data.get('call_sid')
        
        # TODO: Lookup campaign_id from HOC based on caller_id
        # Für jetzt: Nutze eine Test campaign_id
        campaign_id = 804  # Beispiel: Urban Kita gGmbH
        
        # Hole Kandidaten-Daten (in Produktion: aus Datenbank via caller_id)
        # Für jetzt: Beispiel-Daten
        first_name = "Max"
        last_name = "Mustermann"
        company_name = "Urban Kita gGmbH"
        
        logger.info(f"📞 Anruf von: {caller_id}")
        logger.info(f"👤 Kandidat: {first_name} {last_name}")
        logger.info(f"🏢 Firma: {company_name}")
        logger.info(f"📋 Campaign ID: {campaign_id}")
        
        # Hole Questionnaire-Kontext von HOC
        questionnaire = fetch_questionnaire_context(campaign_id)
        
        if not questionnaire:
            logger.warning(f"⚠️  Kein Questionnaire für campaign_id {campaign_id} gefunden!")
            # Fallback: Minimaler Kontext
            questionnaire = {
                'campaign_name': 'Allgemeine Bewerbung',
                'work_location': 'Berlin',
                'questions_list': []
            }
        
        # Baue Enhanced Prompt mit Questionnaire-Kontext
        enhanced_prompt = build_enhanced_prompt(
            questionnaire=questionnaire,
            company_name=company_name,
            first_name=first_name,
            last_name=last_name
        )
        
        # Baue Questionnaire-Kontext für Dynamic Variables
        questionnaire_context = build_questionnaire_context(
            questionnaire=questionnaire,
            company_name=company_name,
            first_name=first_name,
            last_name=last_name
        )
        
        # Extrahiere campaign_location für First Message
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
        logger.info(f"💬 First Message: {first_message[:80]}...")
        logger.info(f"📊 Questionnaire Context: {len(questionnaire_context)} Zeichen")
        
        # Baue Response im RICHTIGEN Format für ElevenLabs
        response_data = {
            "type": "conversation_initiation_client_data",
            "dynamic_variables": {
                "candidatefirst_name": first_name,
                "candidatelast_name": last_name,
                "companyname": company_name,
                "questionnaire_context": questionnaire_context
            },
            "conversation_config_override": {
                "agent": {
                    "prompt": {
                        "prompt": enhanced_prompt
                    },
                    "first_message": first_message,
                    "language": "de"
                }
            }
        }
        
        logger.info(f"✅ Personalisierte Daten erstellt!")
        logger.info(f"{'='*70}\n")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Fehler in Twilio Personalization: {e}", exc_info=True)
        
        # Fallback: Minimale Response
        return jsonify({
            "type": "conversation_initiation_client_data",
            "dynamic_variables": {
                "candidatefirst_name": "Kandidat",
                "candidatelast_name": "",
                "companyname": "Unser Unternehmen",
                "questionnaire_context": ""
            },
            "conversation_config_override": {
                "agent": {
                    "first_message": "Guten Tag, wie kann ich Ihnen helfen?",
                    "language": "de"
                }
            }
        }), 200


@app.route('/webhook/twilio-status', methods=['POST'])
def twilio_status():
    """
    Twilio Status Callback Endpoint
    Empfängt Status-Updates von Twilio Calls
    """
    try:
        data = request.form.to_dict()
        logger.info(f"📞 Twilio Status Update: {data.get('CallStatus', 'unknown')}")
        logger.info(f"   Call SID: {data.get('CallSid', 'unknown')}")
        
        return jsonify({"status": "received"}), 200
    except Exception as e:
        logger.error(f"❌ Fehler in Twilio Status: {e}")
        return jsonify({"status": "error"}), 200


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
  POST /webhook/twilio-personalization       - Twilio Personalization Webhook
  GET  /webhook/health                       - Health Check
  GET  /webhook/test-questionnaire/<id>     - Test Questionnaire-Abruf

Server startet auf: http://0.0.0.0:5000
{'='*70}
""")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
