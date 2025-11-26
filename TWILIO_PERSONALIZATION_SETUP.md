# 🎯 Twilio Personalization - Setup Anleitung

## ✅ Was wir implementiert haben

Statt Outbound SIP Trunk Calls (die nicht funktionieren mit ngnetwork.de), nutzen wir jetzt:

**Twilio → ElevenLabs Personalization**

### Flow:
```
1. Twilio ruft Kandidat an
2. Call wird zu ElevenLabs Agent weitergeleitet
3. ElevenLabs ruft DEINEN Webhook auf
4. Webhook gibt personalisierte Daten zurück
5. Agent spricht mit Kandidat (personalisiert!)
```

---

## 📋 Setup Schritte

### 1. In ElevenLabs: Webhook konfigurieren

1. Gehe zu: https://elevenlabs.io/app/agents/settings
2. **Webhook URL hinzufügen:**
   ```
   URL: https://sellcruiting-webhoook.onrender.com/webhook/twilio-personalization
   ```
3. **Secret hinzufügen:**
   - Name: `Authorization`
   - Value: `Bearer FcqRJPg0LcQZBKA-VgJfQ0UvEdCkDGWoRXzc8vG6x6Q`

### 2. In ElevenLabs Agent: Twilio Personalization aktivieren

1. Gehe zu deinem Agent: https://eu.residency.elevenlabs.io/app/agents
2. Wähle "Sellcruiting Agent"
3. Tab: **"Security"**
4. **Enable:**
   - ☑ Fetch conversation initiation data for inbound Twilio calls
5. **Allowed overrides:**
   - ☑ Prompt
   - ☑ First Message
   - ☑ Dynamic Variables
   - ☑ Language

### 3. Twilio mit ElevenLabs verknüpfen

1. Gehe zu: https://eu.residency.elevenlabs.io/app/agents
2. Agent → **Phone Numbers**
3. Wähle deine Twilio-Nummer: `phnum_9501kazrhbqqfnrsnadf751fg90f`
4. **Verify** dass sie mit dem Agent verknüpft ist

### 4. `.env` aktualisieren

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+12345678900

# ElevenLabs (Twilio Phone Number ID)
ELEVENLABS_AGENT_PHONE_NUMBER_ID=phnum_9501kazrhbqqfnrsnadf751fg90f
```

---

## 🧪 Test

### Lokal testen:

```bash
python test_twilio_personalization.py
```

### Was passiert:

1. **Twilio Call wird initiiert** zu +4915204465582
2. **Call wird zu ElevenLabs weitergeleitet**
3. **ElevenLabs ruft deinen Webhook auf:**
   ```
   POST /webhook/twilio-personalization
   {
     "caller_id": "+4915204465582",
     "agent_id": "agent_2101kab7rs5tefesz0gm66418aw1",
     "called_number": "+12345678900",
     "call_sid": "CA..."
   }
   ```
4. **Webhook gibt zurück:**
   ```json
   {
     "type": "conversation_initiation_client_data",
     "dynamic_variables": {
       "candidatefirst_name": "Max",
       "candidatelast_name": "Mustermann",
       "companyname": "Urban Kita gGmbH",
       "questionnaire_context": "..."
     },
     "conversation_config_override": {
       "agent": {
         "prompt": {
           "prompt": "PERSONALISIERTER PROMPT MIT QUESTIONNAIRE..."
         },
         "first_message": "Guten Tag Max Mustermann..."
       }
     }
   }
   ```
5. **Agent spricht mit personalisiertem Kontext!** 🎉

---

## 🔄 HOC Integration

### HOC sendet jetzt:

```python
# Statt direkt an /webhook/trigger-call
# Nutzt HOC jetzt die Twilio API

from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

call = client.calls.create(
    to=candidate_phone_number,  # z.B. +4915204465582
    from_=TWILIO_PHONE_NUMBER,
    url=f"https://api.elevenlabs.io/v1/convai/conversation/twilio?agent_id={AGENT_ID}"
)
```

**ODER:** Du baust einen neuen Endpoint, der das für HOC macht!

---

## ✅ Vorteile

- ✅ **Funktioniert mit Twilio Direct Integration**
- ✅ **Volle Personalisierung:**
  - Dynamic Variables ✅
  - Prompt Override ✅
  - First Message Override ✅
  - Questionnaire-Kontext (bis 17.000 Zeichen!) ✅
- ✅ **Keine SIP Trunk Komplexität**
- ✅ **Keine ngnetwork.de Probleme**

---

## 📞 Support

Bei Fragen:
- ElevenLabs Docs: https://elevenlabs.io/docs/agents-platform/customization/personalization/twilio-personalization
- Twilio Docs: https://www.twilio.com/docs/voice

