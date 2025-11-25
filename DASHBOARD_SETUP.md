# ElevenLabs Dashboard Konfiguration

## Wichtig: Dynamic Variables konfigurieren

Damit der WebRTC-Link die dynamischen Variablen und den Fragebogen-Kontext erhält, müssen diese **im ElevenLabs Dashboard konfiguriert** werden.

### Schritt 1: Dashboard öffnen

Öffne deinen Agent im Dashboard:
```
https://eu.residency.elevenlabs.io/app/agents/agent_2101kab7rs5tefesz0gm66418aw1
```

### Schritt 2: Dynamic Variables konfigurieren

Gehe zu **Configuration** → **Dynamic Variables** und füge folgende Variablen hinzu:

#### Erforderliche Variablen (Required):

1. **`companyname`**
   - Typ: String
   - Beschreibung: Name der Firma
   - Required: ✅

2. **`candidatefirst_name`**
   - Typ: String
   - Beschreibung: Vorname des Kandidaten
   - Required: ✅

3. **`candidatelast_name`**
   - Typ: String
   - Beschreibung: Nachname des Kandidaten
   - Required: ✅

4. **`campaignlocation_label`**
   - Typ: String
   - Beschreibung: Standort der Kampagne
   - Required: ✅

5. **`questionnaire_context`**
   - Typ: String (Long Text)
   - Beschreibung: Fragebogen-Kontext aus HOC
   - Required: ✅

#### Optionale Variablen:

6. **`campaign_id`**
   - Typ: String
   - Beschreibung: ID der Kampagne

7. **`companysize`**
   - Typ: String
   - Beschreibung: Unternehmensgröße

8. **`companypitch`**
   - Typ: String
   - Beschreibung: Unternehmensbeschreibung

9. **`companypriorities`**
   - Typ: String
   - Beschreibung: Unternehmenspriorität

10. **`position`**
    - Typ: String
    - Beschreibung: Position

11. **`department`**
    - Typ: String
    - Beschreibung: Abteilung

12. **`campaign_title`**
    - Typ: String
    - Beschreibung: Titel der Kampagne

### Schritt 3: First Message anpassen

Deine aktuelle First Message:
```
Guten Tag {{candidatefirst_name}} {{candidatelast_name}}, hier spricht Susi von {{companyname}}. Es geht um ihre Bewerbung am Standort {{campaignlocation_label}}. Haben Sie ungefähr 15 Minuten Zeit für dieses Gespräch um ihre Daten zu erfassen?
```

✅ Diese ist bereits korrekt!

### Schritt 4: System Prompt anpassen

Füge am Ende deines System Prompts folgende Zeile hinzu, um den Fragebogen-Kontext zu integrieren:

```
{{questionnaire_context}}
```

Der komplette System Prompt sollte also so aussehen:

```
[DEIN BESTEHENDER DASHBOARD PROMPT]

{{questionnaire_context}}
```

---

## Wie es funktioniert:

1. **Webhook empfängt Anfrage** von HOC mit:
   - `campaign_id`
   - `company_name`
   - `candidate_first_name`
   - `candidate_last_name`

2. **Webhook holt Fragebogen** aus HOC API:
   - `/api/v1/questionnaire/{campaign_id}`

3. **Webhook erstellt Dynamic Variables**:
   - Basis-Variablen (Name, Firma, etc.)
   - Fragebogen-Kontext als `questionnaire_context`

4. **Webhook generiert WebRTC Link** mit allen Variablen als Query-Parameter:
   ```
   https://eu.residency.elevenlabs.io/app/talk-to?agent_id={AGENT_ID}&companyname=...&questionnaire_context=...
   ```

5. **ElevenLabs ersetzt Variablen** im Dashboard-Prompt:
   - `{{companyname}}` → "Urban Kita gGmbH"
   - `{{candidatefirst_name}}` → "Max"
   - `{{questionnaire_context}}` → [Fragebogen-Daten]

6. **Agent startet Gespräch** mit gefüllten Variablen!

---

## Testen

Nach der Konfiguration:

1. Webhook aufrufen:
   ```bash
   python test_call_local.py
   ```

2. Link öffnen und prüfen, ob:
   - First Message die richtigen Namen enthält
   - System Prompt den Fragebogen-Kontext enthält

---

## Troubleshooting

### Fehler: "Missing required dynamic variables"

**Ursache**: Variablen sind nicht im Dashboard konfiguriert.

**Lösung**: Füge alle erforderlichen Variablen im Dashboard hinzu (siehe Schritt 2).

### Variablen werden nicht ersetzt (z.B. `{{companyname}}` bleibt stehen)

**Ursache**: Variable ist nicht als Query-Parameter im Link enthalten.

**Lösung**: Prüfe, ob die Variable im Webhook korrekt übergeben wird (Logs checken).

### Fragebogen-Kontext wird nicht angezeigt

**Ursache**: `{{questionnaire_context}}` fehlt im System Prompt.

**Lösung**: Füge `{{questionnaire_context}}` am Ende des System Prompts im Dashboard hinzu.

