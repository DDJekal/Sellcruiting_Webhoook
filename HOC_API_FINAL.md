# 📞 HOC Webhook API - FINALE Dokumentation (Twilio Outbound)

## ✅ Was funktioniert

**Twilio Outbound Calls mit voller Personalisierung:**
- ✅ Dynamic Variables Infusion
- ✅ Prompt Override (mit Questionnaire-Kontext)
- ✅ First Message Override
- ✅ Conversations in ElevenLabs Dashboard
- ✅ Vollständiges Tracking & Transcripts

---

## 🔐 Authentifizierung

**Alle Requests benötigen einen API Key im Authorization Header!**

### Header Format:
```
Authorization: Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q
```

---

## 🌐 Base URL

```
https://sellcruiting-webhoook.onrender.com
```

---

## 📡 Endpoint: Outbound Call starten

### Request

**URL:**
```
POST https://sellcruiting-webhoook.onrender.com/webhook/trigger-call
```

**Headers:**
```http
Content-Type: application/json
Authorization: Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q
```

**Request Body:**
```json
{
  "campaign_id": 804,
  "company_name": "Urban Kita gGmbH",
  "candidate_first_name": "Max",
  "candidate_last_name": "Mustermann",
  "to_number": "+4915204465582"
}
```

**Feld-Beschreibung:**
- `campaign_id` (required): ID der Kampagne in HOC
- `company_name` (required): Name der Firma
- `candidate_first_name` (required): Vorname des Kandidaten
- `candidate_last_name` (required): Nachname des Kandidaten
- `to_number` (required): Telefonnummer des Kandidaten (E.164 Format: +491234567890)

---

### Response

**Success (200):**
```json
{
  "status": "success",
  "method": "twilio_outbound_call",
  "message": "Twilio outbound call initiated successfully with full personalization",
  "data": {
    "campaign_id": 804,
    "candidate": "Max Mustermann",
    "company": "Urban Kita gGmbH",
    "to_number": "+4915204465582",
    "conversation_id": "conv_5501kb068ntrev0r02hmbepjp02r",
    "call_status": "initiated",
    "questionnaire_loaded": true,
    "timestamp": "2025-11-26T13:45:12.123456",
    "prompt_length": 5432,
    "first_message": "Guten Tag Max Mustermann, hier spricht Susi von Urban Kita gGmbH...",
    "dynamic_variables_filled": true
  }
}
```

**Error (400):**
```json
{
  "error": "Missing required fields",
  "missing": ["campaign_id"]
}
```

**Error (401):**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

**Error (500):**
```json
{
  "status": "error",
  "error": "API call failed",
  "message": "...",
  "timestamp": "2025-11-26T13:45:12.123456"
}
```

---

## 🧪 Test-Beispiel (Python)

```python
import requests
import json

# API Configuration
url = "https://sellcruiting-webhoook.onrender.com/webhook/trigger-call"
api_key = "FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q"

# Request Data
data = {
    "campaign_id": 804,
    "company_name": "Urban Kita gGmbH",
    "candidate_first_name": "Max",
    "candidate_last_name": "Mustermann",
    "to_number": "+4915204465582"
}

# Headers
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Send Request
response = requests.post(url, json=data, headers=headers, timeout=120)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

---

## 📋 Was automatisch passiert

Wenn HOC die Anfrage sendet:

1. **Webhook empfängt Daten** ✅
2. **Webhook lädt Questionnaire** von HOC API (campaign_id=804) ✅
3. **Webhook baut Enhanced Prompt** mit:
   - Position, Standort, Gehalt
   - Muss-Kriterien
   - Alle Fragen aus dem Questionnaire
   - Bis zu 17.000 Zeichen Kontext! ✅
4. **Webhook ruft ElevenLabs Twilio API** ✅
5. **ElevenLabs startet Outbound Call** via Twilio ✅
6. **Kandidat bekommt Anruf** (+4915204465582) ✅
7. **Agent spricht mit personalisiertem Kontext:** ✅
   - "Guten Tag Max Mustermann"
   - "von Urban Kita gGmbH"
   - Erwähnt Standort, Gehalt aus Questionnaire
   - Stellt spezifische Fragen

---

## 🎯 Tracking & Analytics

Alle Calls erscheinen in:
```
https://elevenlabs.io/app/conversational-ai/conversations
```

Mit:
- ✅ Vollständigem Transcript
- ✅ Dauer, Status
- ✅ Audio-Aufzeichnung
- ✅ Analytics

---

## 📞 Kontakt

Bei Fragen oder Problemen:
- Webhook Logs: https://dashboard.render.com/ → sellcruiting-webhoook → Logs
- Support: [Deine Kontaktdaten]

---

## 🔄 Changelog

**Version 3.0 (26.11.2025):**
- ✅ Twilio Outbound Calls mit voller Personalisierung
- ✅ conversation_config_override für Enhanced Prompts
- ✅ Dynamic Variables für alle Kandidaten-Daten
- ✅ Questionnaire-Integration (bis 17.000 Zeichen Kontext)
- ✅ Vollständiges Tracking in ElevenLabs Dashboard

