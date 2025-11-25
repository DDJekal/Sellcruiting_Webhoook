# Twilio Setup-Anleitung für ElevenLabs Voice Agent

## Übersicht

Diese Anleitung zeigt dir, wie du Twilio als SIP Trunk Provider für deinen ElevenLabs Voice Agent einrichtest. Mit Twilio kannst du volle Kontrolle über Prompt und First Message haben (`agent_override` funktioniert!).

---

## Vorteile von Twilio

✅ **Voller Prompt-Override**: Unbegrenzte Länge für Fragebogen-Kontext  
✅ **Personalisierte First Message**: Dynamisch für jeden Call  
✅ **Zuverlässig**: Weit verbreitet, gut dokumentiert  
✅ **Kein "Isolated Environment" Problem**: Funktioniert sofort  

❌ **Setup-Aufwand**: Verifizierung erforderlich  
❌ **Kosten**: ~0.01-0.05€ pro Minute (abhängig von Land)  

---

## Schritt 1: Twilio Account erstellen

1. Gehe zu: https://www.twilio.com/try-twilio
2. Registriere dich (kostenlose Trial verfügbar)
3. Verifiziere deine E-Mail und Telefonnummer

### Erforderliche Informationen:
- Firmenname
- Verwendungszweck (z.B. "Voice AI for recruiting")
- ⚠️ **Für EU**: Evtl. Steuernummer/VAT ID erforderlich

---

## Schritt 2: Telefonnummer kaufen

1. Im Twilio Dashboard: **Phone Numbers** → **Buy a Number**
2. Wähle Land (z.B. Deutschland `+49`)
3. Suche nach Nummer mit **Voice Capabilities** ✅
4. Kaufe Nummer (~1€/Monat)

**Wichtig**: Notiere die **Phone Number** (z.B. `+4930123456789`)

---

## Schritt 3: Twilio in ElevenLabs integrieren

### 1. Hole Twilio Credentials

Im Twilio Dashboard:
- **Account SID**: z.B. `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Auth Token**: z.B. `your_auth_token_here`

### 2. Verbinde mit ElevenLabs

1. Gehe zu ElevenLabs Dashboard: https://eu.residency.elevenlabs.io/app/agents
2. Wähle deinen Agent: `agent_2101kab7rs5tefesz0gm66418aw1`
3. Klicke auf **"Phone Numbers"** → **"Add Phone Number"**
4. Wähle **"Twilio"**
5. Gib ein:
   - **Account SID**: (von Twilio)
   - **Auth Token**: (von Twilio)
   - **Phone Number**: (gekaufte Nummer, z.B. `+4930123456789`)

### 3. Notiere die Phone Number ID

Nach der Integration zeigt ElevenLabs eine **Phone Number ID** an:
```
phnum_xxx...
```

⚠️ **Diese ID brauchst du im nächsten Schritt!**

---

## Schritt 4: Code konfigurieren

### Option A: Phone Number ID im Request mitgeben

Die HOC schickt bei jedem Request:
```json
{
  "campaign_id": 123,
  "company_name": "Urban Kita gGmbH",
  "candidate_first_name": "Max",
  "candidate_last_name": "Mustermann",
  "to_number": "+491234567890",
  "agent_phone_number_id": "phnum_xxx..."  ← Twilio Phone Number ID
}
```

### Option B: Default Phone Number ID im Code

Öffne `webhook_receiver.py` und ändere Zeile ~336:

```python
agent_phone_number_id = data.get(
    'agent_phone_number_id', 
    'phnum_xxx...'  # ← DEINE Twilio Phone Number ID hier eintragen!
)
```

Dann entferne die Validierung (Zeile ~343-348).

---

## Schritt 5: Testen

### Lokaler Test:

1. Öffne `test_call_local.py`
2. Ändere:
```python
"to_number": "+49...",  # Deine Telefonnummer
"agent_phone_number_id": "phnum_xxx..."  # Twilio Phone Number ID
```

3. Starte Test:
```bash
python test_call_local.py
```

4. Dein Telefon sollte klingeln! 📞

### Remote Test (Render):

Warte 2-3 Minuten nach Git Push, dann:

```bash
python test_call_local.py --url https://sellcruiting-webhoook.onrender.com
```

---

## Schritt 6: HOC-Integration

Die HOC muss bei jedem Request folgendes senden:

```json
POST https://sellcruiting-webhoook.onrender.com/webhook/trigger-call
Headers:
  Authorization: Bearer YOUR_WEBHOOK_API_KEY
  Content-Type: application/json

Body:
{
  "campaign_id": 123,
  "company_name": "Urban Kita gGmbH",
  "candidate_first_name": "Max",
  "candidate_last_name": "Mustermann",
  "to_number": "+491234567890",
  "agent_phone_number_id": "phnum_xxx..."  // Twilio Phone Number ID
}
```

---

## Kosten

### Twilio Preise (ca.):

- **Phone Number**: ~1€/Monat
- **Outbound Calls (Deutschland)**:
  - ~0.01€ pro Minute
  - 15-Minuten-Gespräch = ~0.15€
- **Monatliche Kosten** (100 Calls à 15 Min): ~16€

**Hinweis**: Trial-Guthaben (~10€) ist verfügbar für Tests!

---

## Troubleshooting

### Problem: "Invalid phone number"

**Ursache**: Nummer ist nicht im E.164 Format

**Lösung**: Format muss sein: `+49123456789` (mit `+` und Landesvorwahl)

### Problem: "Insufficient balance"

**Ursache**: Twilio Trial-Guthaben aufgebraucht

**Lösung**: Kreditkarte hinzufügen oder Guthaben aufladen

### Problem: "Phone number not verified"

**Ursache**: In Trial-Mode können nur verifizierte Nummern angerufen werden

**Lösung**: 
1. Verifiziere Zielnummern in Twilio Dashboard: **Phone Numbers** → **Verified Caller IDs**
2. ODER: Upgrade zu bezahltem Account

---

## Was du jetzt hast

✅ **Volle Funktionalität**:
- Enhanced Prompt mit Fragebogen-Kontext (unbegrenzt)
- Personalisierte First Message
- Dynamische Anpassungen pro Call

✅ **Telefon-basiert**: Echte Anrufe über Twilio

✅ **Produktionsbereit**: Zuverlässig und skalierbar

---

## Nächste Schritte

1. ✅ Twilio Account einrichten
2. ✅ Telefonnummer kaufen
3. ✅ In ElevenLabs integrieren
4. ✅ Phone Number ID im Code eintragen
5. ✅ Lokal testen
6. ✅ Code auf Render deployen
7. ✅ HOC über neue Request-Format informieren

---

**Bei Fragen**: Twilio Support oder ElevenLabs Discord!

