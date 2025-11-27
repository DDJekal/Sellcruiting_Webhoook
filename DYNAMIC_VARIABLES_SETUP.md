# Dynamic Variables System für ElevenLabs Dashboard-Workflows

## 🎯 Überblick

Das System extrahiert automatisch **9 Dynamic Variables** aus dem HOC Questionnaire und injiziert sie in ElevenLabs Dashboard-Workflows.

**WICHTIG:** Der `conversation_config_override` wurde ENTFERNT - das bedeutet, dass deine Dashboard-Workflows in ElevenLabs jetzt aktiv sind und die Variablen nutzen können!

---

## ✅ Verfügbare Dynamic Variables

### 1. **Basis-Variablen** (immer vorhanden)
```
{{candidatefirst_name}}    → Vorname des Kandidaten (z.B. "Max")
{{candidatelast_name}}     → Nachname des Kandidaten (z.B. "Mustermann")
{{companyname}}            → Firmenname (z.B. "Urban Kita gGmbH")
```

### 2. **Unternehmensvariablen** (aus Onboarding extrahiert)
```
{{companysize}}            → Mitarbeiterzahl (z.B. "ca. 120 Mitarbeitende")
{{companypitch}}           → USP + Zielgruppe kombiniert
```

**Extraktions-Logik:**
- Sucht in `questionnaire.onboarding.pages[].prompts[]`
- Findet Fragen mit Keywords: "mitarbeitende", "mitarbeiter", "beschäftigte"
- Findet USP: "unterscheidet", "alleinstellungsmerkmal"
- Findet Zielgruppe: "zielgruppe"

### 3. **Campaign-Variablen** (aus Transcript/Metadaten extrahiert)
```
{{campaignlocation_label}} → Standort (z.B. "München-Schwabing")
{{companypriorities}}      → Prioritäten (z.B. "Psychiatrische Pflege, Nacht- und Wechselschicht")
{{campaignrole_title}}     → Jobtitel (z.B. "Pflegefachkraft Psychiatrie")
```

**Extraktions-Logik:**
- **Location**: Sucht in `campaignlocation_label`, `work_location`, oder `transcript.pages[].prompts[]` nach "Standort:"
- **Priorities**: Analysiert MUSS-Kriterien aus `transcript.pages[]` (filtert "Zwingend:", Arbeitszeitmodelle)
- **Role**: Aus `campaignrole_title` oder `job_title`

### 4. **Kontext-Variablen** (strukturiert generiert)
```
{{questionnaire_context}}  → Formatierter Kontext mit Gate-Kriterien, Rahmenbedingungen
{{questions}}              → Strukturierte Fragenliste für Phase 3
```

**Format von `questionnaire_context`:**
```
===================================
KONTEXT AUS QUESTIONNAIRE:
===================================

Kandidat: Max Mustermann
Firma: Urban Kita gGmbH

📋 FRAGEN ZU KLÄREN (15 insgesamt):
==================================================

🔹 QUALIFIKATIONEN:

  ⚠️  MUSS-KRITERIEN:
  • Haben Sie eine 3-jährige Ausbildung?
    (Kontext: Examinierte Pflegefachkraft erforderlich)

  ℹ️  ZUSÄTZLICHE FRAGEN:
  • Haben Sie eine Fachweiterbildung Psychiatrie?
...
```

**Format von `questions`:**
```
=== FRAGEN FÜR PHASE 3 ===

MUSS-FRAGEN:
1. Haben Sie eine 3-jährige Ausbildung?
   (Hinweis: Examinierte Pflegefachkraft erforderlich)
2. Verfügen Sie über eine Masernimpfung?

ZUSÄTZLICHE FRAGEN:
1. Haben Sie eine Fachweiterbildung Psychiatrie?
2. Sind Sie als Studierender in der Pflege tätig?
```

---

## 🔧 Technische Implementierung

### Extraktions-Funktionen

```python
extract_company_size(questionnaire)     # → "ca. 120 Mitarbeitende"
extract_company_pitch(questionnaire)    # → "Psychiatrischer Versorger im kbo-Verbund..."
extract_location(questionnaire)         # → "München-Schwabing"
extract_priorities(questionnaire)       # → "Psychiatrische Pflege, Nacht- und Wechselschicht"
build_questions_list(questionnaire)     # → Strukturierte Fragenliste
```

### Hauptfunktion

```python
def extract_dynamic_variables(questionnaire, company_name, first_name, last_name):
    """
    Extrahiert ALLE Dynamic Variables aus dem HOC Questionnaire
    
    Returns:
        dict mit 9 Variables für ElevenLabs
    """
    variables = {
        "candidatefirst_name": first_name,
        "candidatelast_name": last_name,
        "companyname": company_name,
        "companysize": extract_company_size(questionnaire),
        "companypitch": extract_company_pitch(questionnaire),
        "campaignlocation_label": extract_location(questionnaire),
        "companypriorities": extract_priorities(questionnaire),
        "campaignrole_title": questionnaire.get('campaignrole_title', 'Ihre Position'),
        "questionnaire_context": build_questionnaire_context(...),
        "questions": build_questions_list(questionnaire)
    }
    return variables
```

### API Call (OHNE conversation_config_override!)

```python
# NEU: Nur Dynamic Variables senden
dynamic_vars = extract_dynamic_variables(questionnaire, company_name, first_name, last_name)

response = client.conversational_ai.twilio.outbound_call(
    agent_id=Config.ELEVENLABS_AGENT_ID,
    agent_phone_number_id=agent_phone_number_id,
    to_number=to_number,
    conversation_initiation_client_data={
        "dynamic_variables": dynamic_vars
        # KEIN conversation_config_override → Dashboard-Workflows bleiben aktiv!
    }
)
```

---

## 📝 Dashboard-Workflow Konfiguration

### Phase 1: Begrüßung & Gate-Check

**System Prompt:**
```
Du bist ein virtueller Recruiting-Assistent von {{companyname}}.

ZIEL DIESER PHASE:
- Begrüßung: {{candidatefirst_name}} {{candidatelast_name}}
- Standort-Check: {{campaignlocation_label}}
- Zeitrahmen klären (15 Min)
- Datenschutz einholen

INTERNER KONTEXT (nicht verlesen):
{{questionnaire_context}}

Prüfe zuerst die MUSS-Kriterien aus dem Kontext.
Bei Nicht-Erfüllung: Gespräch höflich beenden.
```

**First Message:**
```
Guten Tag {{candidatefirst_name}} {{candidatelast_name}}, 
hier spricht Susi von {{companyname}}. 
Es geht um ihre Bewerbung am Standort {{campaignlocation_label}}. 
Haben Sie ungefähr 15 Minuten Zeit für dieses Gespräch?
```

---

### Phase 2: Arbeitgebervorstellung

**System Prompt:**
```
ZIEL: Unternehmen präsentieren (max. 2 Minuten)

Stelle vor:
- {{companyname}} mit {{companysize}} Mitarbeitenden
- {{companypitch}}
- Prioritäten: {{companypriorities}}

Keine Fragen stellen, nur informieren!
```

**Beispiel-Formulierung:**
```
"Wir sind {{companyname}} mit {{companysize}} Mitarbeitenden. 
{{companypitch}}
Aktuell suchen wir besonders für {{companypriorities}}, 
aber grundsätzlich gibt es viele verschiedene Einsatzmöglichkeiten bei uns."
```

---

### Phase 3: Gesprächsprotokoll

**System Prompt:**
```
ZIEL: Qualifikationen & Präferenzen erfassen

Nutze {{questionnaire_context}} für:
- Gate-Kriterien prüfen
- Einsatzbereich-Präferenzen
- Arbeitszeitmodell

Nutze {{questions}} für strukturierte Fragen.

Eine Frage pro Redeanteil!
```

---

### Phase 4: Lebenslauf & Abschluss

**System Prompt:**
```
ZIEL: Beruflicher Werdegang + Handoff

- Ausbildung
- Letzte 3 Arbeitgeber (mit Zeiträumen)
- Zusammenfassung
- Verabschiedung

Halte diese Phase KURZ (max. 3-4 Minuten).
```

---

## 🧪 Testing

### Lokaler Test

```bash
python test_twilio_outbound_final.py
```

**Erwartete Response:**
```json
{
  "status": "success",
  "method": "twilio_outbound_call",
  "message": "Twilio outbound call initiated successfully with Dashboard Workflows + Dynamic Variables",
  "data": {
    "conversation_id": "conv_...",
    "call_status": "initiated",
    "dynamic_variables_count": 9,
    "dynamic_variables_filled": [
      "candidatefirst_name",
      "candidatelast_name",
      "companyname",
      "companysize",
      "companypitch",
      "campaignlocation_label",
      "companypriorities",
      "campaignrole_title",
      "questionnaire_context",
      "questions"
    ],
    "workflow_mode": "dashboard_workflows",
    "note": "Using ElevenLabs Dashboard Workflows with injected Dynamic Variables"
  }
}
```

### Render Logs checken

```bash
# Auf Render: Logs → Suche nach:
"🔍 Extrahiere Dynamic Variables aus Questionnaire..."
"✅ X/9 Dynamic Variables gefüllt:"
```

---

## ⚠️ Wichtige Hinweise

### 1. Dashboard-Workflows sind jetzt AKTIV!

**Vorher:**
- ❌ Masterprompt hat alles überschrieben
- ❌ Dashboard-Workflows wurden ignoriert

**Jetzt:**
- ✅ Dashboard-Workflows werden genutzt
- ✅ Dynamic Variables werden injiziert
- ✅ Du kannst Prompts im ElevenLabs UI anpassen

### 2. Was tun, wenn Variablen leer sind?

**Variablen-Fallbacks:**
```python
# Wenn companysize leer ist:
→ Webhook prüft: onboarding.pages[].prompts[] → company_size → ""

# Wenn campaignlocation_label leer ist:
→ Webhook prüft: campaignlocation_label → work_location → transcript → ""

# Wenn companypriorities leer ist:
→ Webhook prüft: transcript MUSS-Kriterien → questions[priority=1] → ""
```

**Im Dashboard Prompt kannst du Fallbacks nutzen:**
```
{{companyname}} mit {{companysize}} Mitarbeitenden
→ Wenn companysize leer: "{{companyname}} Mitarbeitenden" (grammatikalisch falsch!)

Besser:
"Wir sind {{companyname}}{{#if companysize}} mit {{companysize}}{{/if}}"
```

### 3. AIDA Context

**Status:** `{{aida_context}}` ist bereits im Dashboard vorhanden (nicht vom Webhook generiert).

**Wenn du AIDA Context brauchst:** Erstelle eine neue Funktion `build_aida_context(questionnaire)` im Webhook.

---

## 🚀 Next Steps

### 1. Dashboard-Workflows konfigurieren

- Gehe zu ElevenLabs → Agent → Workflows
- Konfiguriere die 4 Phasen mit den Variablen oben
- Teste jeden Workflow einzeln

### 2. HOC Request anpassen

Stelle sicher, dass HOC folgende Felder sendet:

```json
{
  "campaign_id": 804,
  "company_name": "Urban Kita gGmbH",
  "candidate_first_name": "Max",
  "candidate_last_name": "Mustermann",
  "to_number": "+4915204465582"
}
```

### 3. Render Deployment checken

Nach jedem Git Push:
- Render deployt automatisch
- Checke Logs für "🔍 Extrahiere Dynamic Variables..."
- Teste mit `test_twilio_outbound_final.py`

---

## 📊 Vergleich: Vorher vs. Nachher

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| **Prompt-Quelle** | Masterprompt (17.100 Zeichen) | Dashboard-Workflows (4 Phasen) |
| **Anpassbarkeit** | Nur via Code + Git Push | Direkt im ElevenLabs UI |
| **Dynamic Variables** | 4 (hart codiert) | 9 (automatisch extrahiert) |
| **Phasen-Trennung** | ❌ Keine | ✅ 4 separate Workflows |
| **conversation_config_override** | ✅ Überschreibt alles | ❌ Entfernt (Dashboard aktiv) |
| **Deployment-Geschwindigkeit** | Langsam (Code → Render) | Schnell (UI → sofort) |

---

## 🎉 Fazit

**Du kannst jetzt:**
- ✅ Dashboard-Workflows in ElevenLabs UI konfigurieren
- ✅ 9 Dynamic Variables nutzen (automatisch gefüllt)
- ✅ Prompts pro Phase anpassen (ohne Code-Änderung)
- ✅ Schneller iterieren (keine Render Deployments)

**Webhook sendet automatisch:**
- ✅ Alle 9 Dynamic Variables
- ✅ KEIN conversation_config_override mehr
- ✅ Dashboard-Workflows bleiben aktiv

**Next Step:** Konfiguriere deine Dashboard-Workflows im ElevenLabs UI! 🚀

