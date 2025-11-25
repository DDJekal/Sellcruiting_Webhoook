# 📋 HOC Webhook API - Dokumentation

## 🔐 Authentifizierung

**WICHTIG:** Alle Requests benötigen einen API Key im Authorization Header!

### Header Format:
```
Authorization: Bearer {API_KEY}
```

### API Key:
```
FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q
```

---

## 🌐 Base URL

```
https://sellcruiting-webhoook.onrender.com
```

---

## 📡 Endpoints

### 1. Outbound Call starten (SIP Trunk mit Twilio)

**Endpoint:**
```
POST /webhook/trigger-call
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q
```

**Request Body:**
```json
{
  "campaign_id": 123,
  "company_name": "Tech Startup GmbH",
  "candidate_first_name": "Max",
  "candidate_last_name": "Mustermann",
  "to_number": "+491234567890",
  "agent_phone_number_id": "phnum_xxx..."
}
```

**Feld-Beschreibung:**
- `campaign_id` (required): ID der Kampagne in HOC
- `company_name` (required): Name der Firma
- `candidate_first_name` (required): Vorname des Kandidaten
- `candidate_last_name` (required): Nachname des Kandidaten
- `to_number` (required): Telefonnummer des Kandidaten (E.164 Format: +491234567890)
- `agent_phone_number_id` (required): Twilio Phone Number ID aus ElevenLabs Dashboard

**Response (200):**
```json
{
  "status": "success",
  "message": "Outbound call initiated successfully",
  "data": {
    "campaign_id": 123,
    "candidate": "Max Mustermann",
    "company": "Tech Startup GmbH",
    "to_number": "+491234567890",
    "conversation_id": "conv_abc123...",
    "call_status": "initiated",
    "questionnaire_loaded": true,
    "timestamp": "2025-11-25T11:20:05.169839",
    "prompt_length": 5432,
    "first_message": "Guten Tag Max Mustermann, hier spricht Susi von Tech Startup GmbH..."
  }
}
```

**Error Response (401 - Unauthorized):**
```json
{
  "status": "error",
  "error": "Missing Authorization header",
  "message": "Please provide Authorization: Bearer {API_KEY}"
}
```

**Error Response (400 - Bad Request):**
```json
{
  "status": "error",
  "error": "Missing required fields",
  "missing": ["campaign_id", "company_name"]
}
```

---

### 2. Health Check

**Endpoint:**
```
GET /webhook/health
```

**Keine Authentifizierung erforderlich** (für Monitoring)

**Response:**
```json
{
  "status": "healthy",
  "service": "Sellcruiting Agent Webhook",
  "agent_id": "agent_2101kab7rs5tefesz0gm66418aw1",
  "hirings_api_url": "https://high-office.hirings.cloud/api/v1",
  "timestamp": "2025-11-25T11:20:05.169839"
}
```

---

## 📝 Request Felder

### Erforderlich:
- `campaign_id` (Integer): ID für Questionnaire-Abruf
- `company_name` (String): Firmenname
- `candidate_first_name` (String): Vorname Kandidat
- `candidate_last_name` (String): Nachname Kandidat

### Optional:
- `to_number` (String): Telefonnummer (wird aktuell ignoriert - WebRTC Link-Modus)

---

## 🔄 Workflow

1. **HOC sendet Request** mit Campaign-ID und Kandidaten-Daten
2. **Webhook lädt Questionnaire** von HOC API: `GET /api/v1/questionnaire/{campaign_id}`
3. **Webhook generiert Link** mit personalisiertem Kontext
4. **HOC erhält Link** in Response
5. **HOC sendet Link** an Kandidaten (E-Mail/SMS/Portal)
6. **Kandidat öffnet Link** → spricht im Browser mit Agent (ohne Login!)

---

## 💻 Code Beispiel

### cURL:
```bash
curl -X POST https://sellcruiting-webhoook.onrender.com/webhook/trigger-call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q" \
  -d '{
    "campaign_id": 456,
    "company_name": "High Office IT GmbH",
    "candidate_first_name": "Anna",
    "candidate_last_name": "Schmidt"
  }'
```

### JavaScript (fetch):
```javascript
fetch('https://sellcruiting-webhoook.onrender.com/webhook/trigger-call', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q'
  },
  body: JSON.stringify({
    campaign_id: 456,
    company_name: 'High Office IT GmbH',
    candidate_first_name: 'Anna',
    candidate_last_name: 'Schmidt'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Conversation Link:', data.data.conversation_link);
  // Link an Kandidaten senden
});
```

### Python (requests):
```python
import requests

url = "https://sellcruiting-webhoook.onrender.com/webhook/trigger-call"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q"
}
payload = {
    "campaign_id": 456,
    "company_name": "High Office IT GmbH",
    "candidate_first_name": "Anna",
    "candidate_last_name": "Schmidt"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

if response.status_code == 200:
    conversation_link = data["data"]["conversation_link"]
    print(f"Link: {conversation_link}")
    # Link an Kandidaten senden
else:
    print(f"Error: {data['error']}")
```

---

## ⚠️ Wichtige Hinweise

1. **API Key sicher aufbewahren** - Nicht in Code committen oder öffentlich teilen
2. **HTTPS verwenden** - Alle Requests müssen über HTTPS gehen
3. **Error Handling** - Immer Response Status prüfen
4. **Rate Limiting** - Aktuell kein Limit, aber bitte nicht missbrauchen
5. **Questionnaire** - Falls `campaign_id` nicht existiert, wird trotzdem ein Link generiert (ohne Questionnaire-Kontext)

---

## 🆘 Support

Bei Fragen oder Problemen:
- Health Check: `GET /webhook/health` (ohne Auth)
- Logs prüfen auf Render Dashboard
- Fehler-Responses enthalten Details

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-25

