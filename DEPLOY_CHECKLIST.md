# 🚀 Quick Deploy Checklist

## ✅ Dateien für Render erstellt:
- `render.yaml` - Render Konfiguration
- `Procfile` - Start Command
- `runtime.txt` - Python 3.10.14
- `.gitignore` - Aktualisiert
- `requirements.txt` - Optimiert (ohne Audio-Pakete)

## 📝 Nächste Schritte:

### 1. Git vorbereiten
```powershell
git init
git add .
git commit -m "Initial commit - Production ready"
```

### 2. GitHub Repository erstellen
- Gehe zu: https://github.com/new
- Name: `elevenlabs-voiceagent`
- Visibility: Private
- Create repository

### 3. Code pushen
```powershell
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

### 4. Render Deployment
1. https://render.com → Sign up mit GitHub
2. New → Web Service
3. Connect dein Repository
4. Konfiguration:
   - Name: `elevenlabs-voiceagent`
   - Region: Frankfurt
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn webhook_receiver:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - Plan: Free (oder Starter $7/mo)

5. Environment Variables:
   - `ELEVENLABS_API_KEY`
   - `ELEVENLABS_AGENT_ID`
   - `HIRINGS_API_URL`
   - `HIRINGS_API_TOKEN`

6. Create Web Service

### 5. Nach Deployment
URL: `https://deine-app.onrender.com`

Test: `https://deine-app.onrender.com/webhook/health`

**Webhook für HOC:**
```
https://deine-app.onrender.com/webhook/trigger-call
```

---

📖 Vollständige Anleitung: `RENDER_DEPLOYMENT.md`

