# 🚀 Render Deployment Guide

## ✅ Vorbereitung abgeschlossen

Alle notwendigen Dateien wurden erstellt:
- ✅ `render.yaml` - Render Blueprint Konfiguration
- ✅ `Procfile` - Start-Command für Gunicorn
- ✅ `runtime.txt` - Python Version (3.10.14)
- ✅ `.gitignore` - Aktualisiert für Production
- ✅ `requirements.txt` - Optimiert (Audio-Pakete entfernt)

---

## 📋 Deployment Schritte

### 1. Git Repository vorbereiten

```powershell
cd "C:\Users\David Jekal\Desktop\Projekte\Elevenlabs_VoiceAgent"

# Git initialisieren (falls noch nicht geschehen)
git init

# Alle Dateien hinzufügen
git add .

# Status prüfen
git status

# Commit erstellen
git commit -m "Initial commit - ElevenLabs Voice Agent für Production"
```

### 2. GitHub Repository erstellen

1. Gehe zu: https://github.com/new
2. Repository Name: z.B. `elevenlabs-voiceagent`
3. Visibility: **Private** (empfohlen, da API Keys)
4. **Nicht** "Initialize with README" auswählen
5. **Create repository**

### 3. Code zu GitHub pushen

```powershell
# Remote hinzufügen (ersetze USERNAME und REPO)
git remote add origin https://github.com/USERNAME/REPO.git

# Branch umbenennen zu main
git branch -M main

# Pushen
git push -u origin main
```

### 4. Render Deployment

#### A. Account erstellen
1. Gehe zu: https://render.com
2. **Sign up** mit GitHub Account
3. Autorisiere Render für GitHub Zugriff

#### B. Web Service erstellen
1. Dashboard → **New +** → **Web Service**
2. **Connect Repository**: Wähle dein GitHub Repo
3. Konfiguration:

**Basic Settings:**
- **Name:** `elevenlabs-voiceagent`
- **Region:** Frankfurt (näher zu EU)
- **Branch:** `main`
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn webhook_receiver:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info`

**Plan:**
- **Free** (für Testing - geht nach 15 Min in Sleep)
- **Starter ($7/mo)** (empfohlen für Production - kein Sleep)

#### C. Environment Variables eintragen

Klicke auf **Advanced** → **Add Environment Variable**

Füge hinzu:
```
ELEVENLABS_API_KEY = dein_elevenlabs_api_key_hier
ELEVENLABS_AGENT_ID = agent_2101kab7rs5tefesz0gm66418aw1
HIRINGS_API_URL = https://high-office.hirings.cloud/api/v1
HIRINGS_API_TOKEN = dein_hirings_token_hier
```

**WICHTIG:** Nutze die echten Werte aus deiner lokalen `.env` Datei!

#### D. Deploy starten
- Klicke **Create Web Service**
- Render startet automatisch das Deployment
- Warte 2-5 Minuten

### 5. Deployment testen

Nach erfolgreichem Deploy bekommst du eine URL wie:
```
https://elevenlabs-voiceagent.onrender.com
```

**Health Check testen:**
```
https://elevenlabs-voiceagent.onrender.com/webhook/health
```

Erwartete Response:
```json
{
    "status": "healthy",
    "service": "Sellcruiting Agent Webhook",
    "agent_id": "agent_2101kab7rs5tefesz0gm66418aw1",
    "hirings_api_url": "https://high-office.hirings.cloud/api/v1",
    "timestamp": "2025-11-24T..."
}
```

### 6. Webhook-URL an HOC-Team geben

**Production Webhook-Endpunkt:**
```
https://elevenlabs-voiceagent.onrender.com/webhook/trigger-call
```

Diese URL können sie für ihre Webhook-Integration nutzen.

---

## 🔧 Nach dem Deployment

### Logs überwachen
```
Render Dashboard → dein Service → Logs
```

### Updates deployen
```powershell
# Änderungen machen
git add .
git commit -m "Update: Beschreibung"
git push

# Render deployed automatisch!
```

### Neu deployen (manuell)
```
Render Dashboard → dein Service → Manual Deploy → Deploy latest commit
```

---

## ⚠️ Wichtige Hinweise

### Free Plan Limitierungen:
- Service geht nach **15 Minuten Inaktivität** in Sleep
- Erster Request nach Sleep: **30-60 Sekunden** Spin-up Zeit
- **750 Stunden/Monat** gratis (reicht für Tests)

### Für Production empfohlen:
- **Starter Plan ($7/mo):**
  - Kein Sleep
  - Schnelle Response-Zeiten
  - Mehr RAM & CPU

### Environment Variables ändern:
```
Render Dashboard → dein Service → Environment → Edit
```
Nach Änderung: Service wird automatisch neu deployed

### Domain ändern:
```
Render Dashboard → dein Service → Settings → Custom Domain
```

---

## 🆘 Troubleshooting

### Service startet nicht:
- Prüfe Logs: `Render Dashboard → Logs`
- Prüfe Environment Variables vollständig gesetzt
- Prüfe Build Command erfolgreich

### 502 Bad Gateway:
- Service ist im Sleep → warte 30-60 Sekunden
- Oder: Upgrade zu Starter Plan (kein Sleep)

### Webhook funktioniert nicht:
- Teste Health Check zuerst
- Prüfe HIRINGS_API_TOKEN korrekt
- Prüfe ELEVENLABS_API_KEY korrekt

---

## 📊 Kosten

**Free Plan:**
- ✅ $0/Monat
- ⏰ 750 Stunden/Monat
- 😴 Sleep nach 15 Min Inaktivität

**Starter Plan:**
- 💰 $7/Monat
- ⚡ Kein Sleep
- 🚀 Bessere Performance

---

## ✅ Checkliste

- [ ] Git Repository initialisiert
- [ ] Code auf GitHub gepusht
- [ ] Render Account erstellt
- [ ] Web Service erstellt
- [ ] Environment Variables gesetzt
- [ ] Service deployed
- [ ] Health Check erfolgreich
- [ ] URL an HOC-Team gegeben

---

## 🎉 Fertig!

Dein Voice Agent läuft jetzt in Production auf Render!

**Webhook-Endpunkt für HOC:**
```
https://deine-app.onrender.com/webhook/trigger-call
```

