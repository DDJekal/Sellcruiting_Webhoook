# 🎙️ ElevenLabs Voice Agent mit Cursor API

Ein interaktiver Voice-Agent, der die Cursor API für intelligente Text-Generation und ElevenLabs für natürliche Sprachausgabe nutzt.

## 🚀 Features

- ✅ Integration von Cursor API für KI-gestützte Konversationen
- ✅ ElevenLabs Text-to-Speech für natürliche Sprachausgabe
- ✅ Zwei Modi: Text-Chat und vollwertiger Conversational AI Voice-Agent
- ✅ Konversations-Historie für kontextbezogene Gespräche
- ✅ Farbige Terminal-Ausgabe für bessere UX

## 📋 Voraussetzungen

- Python 3.8 oder höher
- ElevenLabs API Key
- Cursor API Key
- (Optional) ElevenLabs Agent ID für Conversational AI Mode

## 🔧 Installation

### 1. Virtuelle Umgebung aktivieren

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. API Keys konfigurieren

Bearbeite die `.env` Datei und füge deine API Keys ein:

```env
ELEVENLABS_API_KEY=dein_elevenlabs_api_key
CURSOR_API_KEY=dein_cursor_api_key
```

#### 🔑 Wo bekomme ich die API Keys?

**ElevenLabs API Key:**
1. Gehe zu [ElevenLabs Dashboard](https://elevenlabs.io/app/settings/api-keys)
2. Klicke auf "Create API Key"
3. Kopiere den Key in deine `.env` Datei

**Cursor API Key:**
1. Öffne Cursor
2. Gehe zu Settings → API Keys
3. Erstelle einen neuen API Key
4. Kopiere den Key in deine `.env` Datei

**ElevenLabs Agent ID (optional für Conversational AI):**
1. Gehe zu [ElevenLabs Conversational AI](https://elevenlabs.io/app/conversational-ai)
2. Erstelle einen neuen Agent
3. Kopiere die Agent ID in deine `.env` Datei

## 🎮 Verwendung

Starte den Voice-Agent:

```bash
python voice_agent.py
```

### Modi

#### 1️⃣ Text-Chat Mode
- Interaktive Konversation über die Tastatur
- Cursor generiert die Antworten
- Perfekt zum Testen und Entwickeln

#### 2️⃣ Conversational AI Mode
- Vollwertiger Voice-Agent mit Sprach-Ein- und Ausgabe
- Erfordert ElevenLabs Agent ID
- Sprich direkt mit dem Agent über dein Mikrofon

## 🛠️ Konfiguration

Alle Einstellungen können in der `.env` Datei angepasst werden:

```env
# Voice Settings
VOICE_NAME=Bella              # Verfügbare Stimmen im ElevenLabs Dashboard
VOICE_MODEL=eleven_multilingual_v2
VOICE_STABILITY=0.5           # 0.0 - 1.0 (niedriger = dynamischer)
VOICE_SIMILARITY_BOOST=0.75   # 0.0 - 1.0 (höher = ähnlicher zur Original-Stimme)

# Cursor Model
CURSOR_MODEL=cursor-small     # Optionen: cursor-small, cursor-large
```

## 📁 Projektstruktur

```
Elevenlabs_VoiceAgent/
├── .venv/                  # Virtuelle Python-Umgebung
├── .env                    # API Keys und Konfiguration (nicht im Git!)
├── .gitignore             # Git-Ignore-Regeln
├── config.py              # Zentrale Konfiguration
├── voice_agent.py         # Hauptprogramm
├── requirements.txt       # Python-Dependencies
└── README.md             # Diese Datei
```

## 🐛 Troubleshooting

### "API Key fehlt in der .env Datei"
→ Stelle sicher, dass du die `.env` Datei mit deinen API Keys ausgefüllt hast

### "Module not found"
→ Aktiviere das virtuelle Environment und installiere die Dependencies:
```bash
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Audio-Wiedergabe funktioniert nicht
→ Für lokale Audio-Wiedergabe musst du zusätzliche System-Dependencies installieren:
- Windows: PyAudio benötigt Visual C++ Build Tools
- macOS: `brew install portaudio`
- Linux: `sudo apt-get install portaudio19-dev`

### Cursor API Fehler
→ Überprüfe, ob dein API Key gültig ist und ob die URL korrekt ist:
```python
CURSOR_API_URL = "https://api.cursor.sh/v1/chat/completions"
```

## 💡 Tipps

1. **Voice-Qualität optimieren:** Passe `VOICE_STABILITY` und `VOICE_SIMILARITY_BOOST` in der `.env` an
2. **Verschiedene Stimmen:** Liste aller verfügbaren Stimmen findest du im [ElevenLabs Dashboard](https://elevenlabs.io/app/voice-library)
3. **Bessere Antworten:** Nutze `cursor-large` für komplexere Konversationen (langsamer, aber intelligenter)

## 📝 Lizenz

Dieses Projekt ist Open Source und frei verwendbar.

## 🤝 Support

Bei Fragen oder Problemen:
- ElevenLabs Docs: https://docs.elevenlabs.io/
- Cursor Docs: https://cursor.sh/docs

---

**Viel Spaß mit deinem Voice-Agent! 🎉**

