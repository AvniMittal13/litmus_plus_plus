# Deployment Guide — litmusreagent (Azure App Service)

## App Details
- **App Name:** litmusreagent
- **URL:** https://litmusreagent.azurewebsites.net
- **Resource Group:** litmus-india
- **Region:** Central India
- **Plan:** B1 (Linux)
- **Runtime:** Python 3.10
- **Startup Command:** `python startup.py`

---

## How to Deploy (after making code changes)

### Step 1: Make sure you're in the project root
```powershell
cd "c:\Users\avnimittal\OneDrive - Microsoft\Desktop\tp\litmus"
```

### Step 2: Login to Azure (if not already logged in)
```powershell
az login --tenant 1292023e-30ac-4e6b-af99-d58ea6eace00
```

### Step 3: Deploy using `az webapp up`
```powershell
az webapp up --name litmusreagent --resource-group litmus-india --runtime "PYTHON:3.10" --sku B1
```

This command:
- Zips your source code (excludes `venv/`, `.git/` automatically)
- Uploads it to Azure
- Triggers Oryx build (installs pip packages from requirements.txt)
- Restarts the app with the new code

### Step 4: Wait ~8 minutes for cold start
The app takes 5-8 minutes to start due to heavy Python imports (chromadb, sklearn, autogen, etc.)

### Step 5: Verify
```powershell
# Quick test
Invoke-WebRequest "https://litmusreagent.azurewebsites.net" -UseBasicParsing -TimeoutSec 60
```

Or just open https://litmusreagent.azurewebsites.net in your browser.

---

## What NOT to do

| Don't | Why |
|-------|-----|
| `az webapp deploy --type zip` | Oryx build doesn't extract `web_interface/` properly with manual zip |
| Use `gunicorn` in startup command | Gunicorn can't resolve module paths in Oryx's extracted directory |
| Use `allow_unsafe_werkzeug=True` | Not supported by Werkzeug 2.3.x installed on Azure |
| Use `eventlet` async mode | Causes `TypeError` with the installed flask-socketio version |
| Deploy on F1 (Free) tier | App needs ~2 GB RAM; F1 only has 1 GB and 60 min CPU/day limit |

---

## Environment Variables (Azure App Settings)

These are already configured. If you need to reconfigure:

```powershell
az webapp config appsettings set --name litmusreagent --resource-group litmus-india --settings `
  FLASK_ENV=production `
  USE_API_KEY=true `
  WEBSITES_CONTAINER_START_TIME_LIMIT=1800 `
  SCM_DO_BUILD_DURING_DEPLOYMENT=1 `
  ENABLE_ORYX_BUILD=true `
  OPENAI_API_KEY="<your-key>" `
  OPENAI_BASE_URL="https://litmus1.openai.azure.com/" `
  OPENAI_API_TYPE=azure `
  OPENAI_API_VERSION="2025-01-01-preview" `
  OPENAI_DEPLOYMENT_NAME="gpt-4.1" `
  OPENAI_EMBEDDING_MODEL="text-embedding-ada-002" `
  AZURE_OPENAI_ENDPOINT_EMBEDDING="https://litmus1.openai.azure.com/" `
  AZURE_OPENAI_API_KEY_EMBEDDING="<your-key>" `
  FIRECRAWL_API_KEY="<your-key>" `
  CHROMA_OPENAI_API_KEY="<your-key>"
```

---

## Checking Logs

```powershell
# Check app state
az webapp show --name litmusreagent --resource-group litmus-india --query state -o tsv

# Stream live logs (Ctrl+C to stop)
az webapp log tail --name litmusreagent --resource-group litmus-india

# Download Docker container logs via API
$token = az account get-access-token --resource "https://management.azure.com/" --query accessToken -o tsv
$resp = Invoke-RestMethod -Uri "https://litmusreagent.scm.azurewebsites.net/api/logs/docker" -Headers @{Authorization="Bearer $token"}
$latestLog = ($resp | Sort-Object lastUpdated -Descending | Where-Object { $_.href -match "default_docker\.log$" } | Select-Object -First 1).href
$log = Invoke-RestMethod -Uri $latestLog -Headers @{Authorization="Bearer $token"}
($log -split "`n") | Select-Object -Last 20
```

---

## Restarting the App

```powershell
az webapp restart --name litmusreagent --resource-group litmus-india
# Wait ~8 minutes for cold start
```

---

## Backup Branch
The `main_backup` branch on GitHub contains additional improvements (local vendor JS files, lazy-init for heavy imports) that can be cherry-picked later.
