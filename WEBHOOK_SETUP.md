# 🎙️ Webhook Receiver - Setup Abgeschlossen!

## ✅ Was wurde implementiert:

1. ✅ **webhook_receiver.py** - Haupt-Webhook-Server
2. ✅ **config.py** - Erweitert mit HOC Settings
3. ✅ **requirements.txt** - Flask & Gunicorn hinzugefügt
4. ✅ **test_webhook_request.py** - Test-Skript
5. ✅ **Dependencies installiert**

## 🚀 SO STARTEST DU DEN WEBHOOK:

### 1. .env konfigurieren

Füge diese Zeilen zu deiner `.env` hinzu:

```env
# HOC Configuration
HOC_BASE_URL=https://your-hoc-server.com
HOC_API_KEY=dein_hoc_api_key
```

### 2. Webhook Server starten

```powershell
python webhook_receiver.py
```

Der Server läuft dann auf: `http://localhost:5000`

## 📡 API Endpoints:

### POST `/webhook/trigger-call`

Empfängt Call-Request von HOC und startet Outbound Call.

**Request Body:**
```json
{
    "campaign_id": 123,
    "company_name": "Tech Startup GmbH",
    "candidate_first_name": "Max",
    "candidate_last_name": "Mustermann",
    "to_number": "+491234567890",
    "agent_phone_number_id": "phnum_4901ka8wj2cjexfvpwwhnp9v94t9"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Outbound call started successfully",
    "data": {
        "campaign_id": 123,
        "candidate": "Max Mustermann",
        "company": "Tech Startup GmbH",
        "to_number": "+491234567890",
        "conversation_id": "...",
        "questionnaire_loaded": true,
        "timestamp": "2025-11-24T12:00:00"
    }
}
```

### GET `/webhook/health`

Health Check Endpoint

### GET `/webhook/test-questionnaire/<campaign_id>`

Test-Endpoint um Questionnaire-Abruf zu testen

## 🔄 Flow:

```
HOC → POST /webhook/trigger-call
       ↓
GET {HOC_BASE_URL}/api/v1/questionnaire/{campaign_id}
       ↓
Questionnaire/Kontext geladen
       ↓
Enhanced Prompt erstellt (mit Kontext)
       ↓
ElevenLabs Outbound Call gestartet
       ↓
Response zurück an HOC
```

## 🧪 Testen:

```powershell
# Test-Request senden
python test_webhook_request.py
```

## 📋 Wichtige Hinweise:

1. **HOC API URL**: Stelle sicher, dass `HOC_BASE_URL` korrekt ist
2. **HOC API Key**: Benötigt für Authentifizierung
3. **Campaign ID**: Muss als Integer übergeben werden
4. **Questionnaire-Struktur**: Passe `build_enhanced_prompt()` an deine Questionnaire-Struktur an

## 🎯 Nächste Schritte:

1. Konfiguriere HOC_BASE_URL und HOC_API_KEY in der .env
2. Teste den Questionnaire-Abruf mit `/webhook/test-questionnaire/<id>`
3. Integriere den Webhook in deine HOC-Infrastruktur
4. Teste einen echten Call-Request

Viel Erfolg! 🚀

