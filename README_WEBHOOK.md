# 🎙️ Sellcruiting Agent Webhook Receiver

Webhook-Service für die Integration von HOC mit ElevenLabs Outbound Calls.

## 🚀 Features

- ✅ Empfängt Call-Requests von HOC
- ✅ Lädt Questionnaire/Kontext aus HOC basierend auf `campaign_id`
- ✅ Startet personalisierte ElevenLabs Outbound Calls
- ✅ Erweitert System-Prompt mit Questionnaire-Kontext
- ✅ Nutzt Cursor API für intelligente Antworten

## 📋 Setup

### 1. Dependencies installieren

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. .env konfigurieren

Füge folgende Zeilen zu deiner `.env` hinzu:

```env
# HOC Configuration
HOC_BASE_URL=https://your-hoc-server.com
HOC_API_KEY=dein_hoc_api_key
```

### 3. Webhook Server starten

```powershell
python webhook_receiver.py
```

## 📡 API Endpoints

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

print("="*70)
print("🧪 TEST: Webhook Request (simuliert HOC)")
print("="*70)
print("\n📤 Sende Test-Request...")
print(json.dumps(test_data, indent=2, ensure_ascii=False))

try:
    response = requests.post(
        WEBHOOK_URL,
        json=test_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    print("\n📋 Response Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        print("\n✅ Webhook erfolgreich!")
    else:
        print("\n❌ Webhook Fehler!")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Verbindungsfehler!")
    print("💡 Stelle sicher, dass der Webhook-Server läuft:")
    print("   python webhook_receiver.py")
except Exception as e:
    print(f"\n❌ Fehler: {e}")

print("\n" + "="*70)
```

Ich habe jetzt die webhook_receiver.py Datei erstellt, aber ich muss sicherstellen, dass alle Funktionen vollständig sind. Lass mich die Datei nochmal prüfen und sicherstellen, dass alles korrekt ist.
</think>
Prüfe die Datei auf Vollständigkeit und korrigiere sie gegebenenfalls:
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
read_file
