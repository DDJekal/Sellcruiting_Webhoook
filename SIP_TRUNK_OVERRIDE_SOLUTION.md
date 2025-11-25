# SIP Trunk Prompt Override - Lösung

## Problem
Der Parameter `agent_override` wird von `sip_trunk.outbound_call()` **nicht unterstützt**:
```python
TypeError: SipTrunkClient.outbound_call() got an unexpected keyword argument 'agent_override'
```

## Lösung
Verwende `conversation_initiation_client_data` mit `conversation_config_override`:

### Korrekte Implementierung

```python
from elevenlabs.types.conversation_initiation_client_data_request_input import ConversationInitiationClientDataRequestInput

# Erstelle Client Data mit conversation_config_override
client_data = ConversationInitiationClientDataRequestInput(
    conversation_config_override={
        "agent": {
            "prompt": {
                "prompt": enhanced_prompt  # Großer Prompt (5000+ Zeichen möglich!)
            },
            "first_message": first_message
        }
    }
)

# Starte Outbound Call
response = client.conversational_ai.sip_trunk.outbound_call(
    agent_id=agent_id,
    to_number=to_number,
    agent_phone_number_id=agent_phone_number_id,
    conversation_initiation_client_data=client_data
)
```

## Wichtige Erkenntnisse

### ✅ Was funktioniert
- **Große Prompts**: 5000+ Zeichen sind möglich
- **First Message Override**: Kann pro Call überschrieben werden
- **API Request Body**: Daten werden über Request Body gesendet (nicht SIP Headers)
- **Kein Server Tool nötig**: Direkte Überschreibung funktioniert

### ❌ Was NICHT funktioniert
- `agent_override` Parameter (existiert nicht)
- Direkte Überschreibung ohne `ConversationInitiationClientDataRequestInput`

## Parameter-Struktur

### Verfügbare Parameter in `outbound_call()`
```python
def outbound_call(
    *,
    agent_id: str,                          # REQUIRED
    agent_phone_number_id: str,             # REQUIRED
    to_number: str,                         # REQUIRED
    conversation_initiation_client_data: Optional[ConversationInitiationClientDataRequestInput] = None,
    request_options: Optional[RequestOptions] = None
) -> SipTrunkOutboundCallResponse
```

### ConversationInitiationClientDataRequestInput Felder
```python
ConversationInitiationClientDataRequestInput(
    conversation_config_override={...},     # Agent-Konfiguration überschreiben
    dynamic_variables={...},                # Dynamic Variables setzen
    custom_llm_extra_body={...},           # Custom LLM Parameter
    user_id="...",                         # User ID
    source_info="..."                      # Source Info
)
```

## Geänderte Dateien

### webhook_receiver.py
**Alt (funktioniert NICHT):**
```python
response = client.conversational_ai.sip_trunk.outbound_call(
    agent_id=Config.ELEVENLABS_AGENT_ID,
    to_number=to_number,
    agent_phone_number_id=agent_phone_number_id,
    agent_override={  # ← FALSCH!
        "prompt": {"prompt": enhanced_prompt},
        "first_message": first_message
    }
)
```

**Neu (funktioniert):**
```python
from elevenlabs.types.conversation_initiation_client_data_request_input import ConversationInitiationClientDataRequestInput

client_data = ConversationInitiationClientDataRequestInput(
    conversation_config_override={
        "agent": {
            "prompt": {"prompt": enhanced_prompt},
            "first_message": first_message
        }
    }
)

response = client.conversational_ai.sip_trunk.outbound_call(
    agent_id=Config.ELEVENLABS_AGENT_ID,
    to_number=to_number,
    agent_phone_number_id=agent_phone_number_id,
    conversation_initiation_client_data=client_data  # ← RICHTIG!
)
```

## Tests

### Test 1: Parameter-Inspektion
```bash
python inspect_sip_trunk_params.py
```
Zeigt verfügbare Parameter von `outbound_call()`.

### Test 2: Großer Prompt (5000+ Zeichen)
```bash
python test_conversation_config_override.py
```
Testet ob conversation_config_override mit großem Prompt funktioniert.

### Test 3: Webhook Integration
```bash
# Terminal 1: Starte Webhook
python webhook_receiver.py

# Terminal 2: Teste Webhook
python test_webhook_with_new_override.py
```

## Ergebnis

✅ **conversation_config_override funktioniert!**
- Große Prompts (5000+ Zeichen) möglich
- first_message Override funktioniert
- Keine Server Tools notwendig
- Daten werden über API Request Body gesendet (nicht SIP Headers)

## Empfehlung für ElevenLabs Agent

Diese Fragen wurden durch Tests beantwortet:

1. ✅ **WebRTC Link mit Overrides**: Nicht für Outbound Phone Calls geeignet
2. ✅ **SIP Trunk Overrides**: Funktioniert mit `conversation_config_override`
3. ✅ **Size Limits**: 5000+ Zeichen funktionieren (API Request Body)
4. ✅ **Architektur**: SIP Trunk mit `conversation_config_override` ist die richtige Lösung

Keine weiteren Fragen an ElevenLabs Support notwendig! 🎉

