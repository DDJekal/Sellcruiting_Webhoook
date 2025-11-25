# ElevenLabs Dashboard Setup für Dynamic Variables

## 🎯 Übersicht

Dieses Setup ermöglicht zwei verschiedene Modi:

### 📞 **SIP Trunk (Telefon-Anrufe mit `to_number`)**
- ✅ Prompt wird **KOMPLETT ÜBERSCHRIEBEN** via `conversation_config_override`
- ✅ Enhanced Prompt + Questionnaire-Kontext werden dynamisch gesendet
- ✅ Dashboard-Konfiguration wird IGNORIERT
- ✅ Jeder Call hat seinen eigenen Prompt

### 🔗 **WebRTC Link (Browser-basiert OHNE `to_number`)**
- ✅ Dashboard-Prompt bleibt **UNVERÄNDERT**
- ✅ **Dynamic Variables** werden via URL-Parameter gefüllt
- ✅ Questionnaire-Kontext und Fragen als Variables
- ✅ Flexibel, aber Dashboard muss vorbereitet sein

---

## 📝 Schritt 1: Dynamic Variables im Dashboard definieren

### Im ElevenLabs Dashboard unter "Agent Settings" → "Prompt":

Füge folgende **Dynamic Variables** in deinen Prompt ein:

```
Du bist Susi, eine professionelle KI-Recruiting-Assistentin von Sellcruiting.

===================================
KANDIDATEN-INFORMATIONEN
===================================

Name: {{candidate_first_name}} {{candidate_last_name}}
Firma: {{company_name}}
Campaign-ID: {{campaign_id}}

===================================
KONTEXT AUS QUESTIONNAIRE
===================================

{{questionnaire_context}}

===================================
FRAGEN ZU KLÄREN
===================================

{{questions_list}}

===================================
DEINE AUFGABE
===================================

1. Begrüße den Kandidaten persönlich mit Namen
2. Stelle dich als Susi von {{company_name}} vor
3. Gehe systematisch die Fragen aus "FRAGEN ZU KLÄREN" durch
4. Achte auf:
   - ⚠️ MUSS-Kriterien sind verpflichtend
   - ℹ️ OPTIONALE Fragen nur wenn Zeit
5. Nutze die Überleitungen aus der Fragen-Liste
6. Sei freundlich, professionell und effizient

===================================
GESPRÄCHSABLAUF
===================================

[Hier kommt dein detaillierter Gesprächsablauf...]
```

---

## 🔧 Schritt 2: Dynamic Variables Liste

Die folgenden Variables werden automatisch gefüllt:

| Variable | Beschreibung | Beispiel | Max. Länge |
|----------|--------------|----------|------------|
| `{{candidate_first_name}}` | Vorname des Kandidaten | "Max" | - |
| `{{candidate_last_name}}` | Nachname des Kandidaten | "Mustermann" | - |
| `{{company_name}}` | Firmenname | "Urban Kita gGmbH" | - |
| `{{campaign_id}}` | Campaign-ID aus HOC | "639" | - |
| `{{questionnaire_context}}` | Strukturierter Kontext mit Kandidaten-Info und Fragen-Kategorien | Siehe unten | 1500 Zeichen |
| `{{questions_list}}` | Liste aller Fragen mit Priorität und Kontext | Siehe unten | 1500 Zeichen |

---

## 📊 Beispiel: `{{questionnaire_context}}`

```
===================================
KONTEXT AUS QUESTIONNAIRE:
===================================

Kandidat: Max Mustermann
Firma: Urban Kita gGmbH

📋 FRAGEN ZU KLÄREN (12 insgesamt):
==================================================

🔹 QUALIFIKATION:

  ⚠️  MUSS-KRITERIEN:
  • Haben Sie: Deutschkenntnisse B2?
    (Kontext: Muss-Kriterium: Deutschkenntnisse B2)
  • Haben Sie: mehrjährige Berufserfahrung?
    (Kontext: Muss-Kriterium: mehrjährige Berufserfahrung)

  ℹ️  ZUSÄTZLICHE FRAGEN:
  • Können Sie einschlägige Fortbildungen nachweisen?

🔹 RAHMEN:

  ℹ️  ZUSÄTZLICHE FRAGEN:
  • Die Stelle ist in Vollzeit (39h). Ist das passend?
    (Überleitung: Ich möchte kurz auf das Arbeitszeitmodell eingehen.)

===================================
```

---

## 📋 Beispiel: `{{questions_list}}`

```
1. [⚠️ MUSS] Haben Sie: Deutschkenntnisse B2? (Kontext: Muss-Kriterium: Deutschkenntnisse B2)
2. [⚠️ MUSS] Haben Sie: mehrjährige Berufserfahrung? (Kontext: Muss-Kriterium: mehrjährige Berufserfahrung)
3. [⚠️ MUSS] Haben Sie: staatlich anerkannter Abschluss? (Kontext: Muss-Kriterium)
4. [ℹ️ OPTIONAL] Die Stelle ist in Vollzeit (39h). Ist das passend? (Überleitung: Ich möchte kurz auf das Arbeitszeitmodell eingehen.)
5. [⚠️ MUSS] Unser Standort ist Berlin. Passt das? 
...
```

---

## 🧪 Schritt 3: Testen

### Test 1: Lokaler Test
```bash
python test_webrtc_fallback_simple.py
```

### Test 2: Response prüfen
```json
{
  "status": "success",
  "method": "webrtc_link",
  "data": {
    "signed_url": "wss://api.eu.residency.elevenlabs.io/...",
    "dynamic_variables_filled": [
      "candidate_first_name",
      "candidate_last_name", 
      "company_name",
      "campaign_id",
      "questionnaire_context",
      "questions_list"
    ],
    "questions_count": 12,
    "note": "WebRTC link uses Dashboard configuration with dynamic variables"
  }
}
```

---

## ⚙️ Schritt 4: First Message anpassen

Im Dashboard unter "First Message":

```
Guten Tag {{candidate_first_name}} {{candidate_last_name}}, 
hier spricht Susi von {{company_name}}. 

Es geht um Ihre Bewerbung. Haben Sie ungefähr 15 Minuten Zeit 
für dieses Gespräch um Ihre Daten zu erfassen?
```

---

## 🔄 Vergleich: SIP Trunk vs. WebRTC

| Feature | SIP Trunk (Phone) | WebRTC (Browser) |
|---------|-------------------|------------------|
| **Prompt-Quelle** | `conversation_config_override` (API) | Dashboard + Dynamic Variables |
| **Dynamisch?** | Vollständig (jeder Call eigener Prompt) | Dashboard + URL-Parameter |
| **Questionnaire** | Im Override enthalten | Via `{{questionnaire_context}}` |
| **Fragen-Liste** | Im Override enthalten | Via `{{questions_list}}` |
| **Setup** | Keine Dashboard-Änderungen nötig | Dashboard muss vorbereitet sein |
| **Flexibilität** | Maximal (alles per API) | Dashboard-abhängig |

---

## 📌 Best Practices

### ✅ DO:
- Nutze `{{variables}}` im Dashboard-Prompt
- Teste mit Campaign 639 (echte Daten)
- Prüfe URL-Länge (max ~2000 Zeichen)
- Verwende strukturierte Fragen-Listen

### ❌ DON'T:
- Keine hartkodierten Namen im Dashboard
- Keine statischen Fragen im Prompt
- Keine sehr langen questionnaire_context (max 1500 Zeichen)

---

## 🆘 Troubleshooting

### Problem: Variables werden nicht gefüllt
**Lösung:** Prüfe ob die Variable im Dashboard genau so geschrieben ist: `{{variable_name}}`

### Problem: URL zu lang
**Lösung:** Questionnaire-Kontext wird automatisch auf 1500 Zeichen gekürzt

### Problem: Fragen fehlen
**Lösung:** Prüfe ob HOC API Token korrekt ist und Questionnaire geladen wird

---

## 📞 Support

Bei Fragen zur Einrichtung:
- Prüfe Logs: `webhook_receiver.py` zeigt alle gefüllten Variables
- Teste lokal: `test_webrtc_fallback_simple.py`
- Render Logs: Zeigen ob Variables korrekt gesendet wurden

