# 📊 Excel Insight Analyzer

> Dashboard inteligente que transforma archivos Excel en insights accionables mediante IA Generativa.

**[🌐 App en Vivo](https://excel-insight-analyzer.vercel.app/)** · **[⚡ API Docs](https://excel-insight-analyzer-production.up.railway.app/docs)**

---

## 🏗️ Arquitectura

```
Usuario → Vue.js (Vercel) → FastAPI (Railway) → Gemini API
                                    ↓
                             Supabase PostgreSQL
```

**Flujo:**
1. Usuario sube archivo Excel desde la interfaz web
2. Frontend envía el archivo al backend via `POST /analyze`
3. FastAPI lee el Excel con pandas y detecta tipos de columnas
4. Backend calcula métricas y llama a Gemini API con prompt estructurado
5. Resultado guardado en Supabase y devuelto como JSON al frontend
6. Dashboard renderiza KPIs, distribuciones y análisis IA

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Frontend | Vue.js + Vite | SPA reactiva, rápida de desarrollar para MVP |
| Backend | FastAPI (Python) | API asíncrona, ideal para procesamiento de archivos |
| Datos | Pandas + OpenPyXL | Lectura y análisis de Excel |
| IA | Gemini API | Costo cero para MVP, suficiente para análisis ejecutivo |
| DB | Supabase PostgreSQL | Free tier, API REST automática, JSONB para datos flexibles |
| Deploy | Vercel + Railway | CI/CD automático desde GitHub, capa gratuita |

---

## 🗄️ Modelo de Datos

**Tabla:** `analysis_results`

```sql
id                    uuid        PRIMARY KEY
file_name             text
rows                  integer
columns               integer
column_names          jsonb       -- ["col1", "col2", ...]
identifier_columns    jsonb
date_columns          jsonb
numeric_columns       jsonb
categorical_columns   jsonb
descriptive_text_columns jsonb
metrics               jsonb       -- {numeric_summary, categorical_summary, ...}
ai_summary            text        -- Análisis generado por Gemini
created_at            timestamp   DEFAULT now()
```

**¿Por qué JSONB?** La estructura de un Excel no es fija. JSONB permite almacenar columnas dinámicas y métricas variables sin migraciones. Es flexible, consultable y escalable.

---

## 🤖 Uso de IA

### IA dentro de la aplicación
- **Gemini API** genera resumen ejecutivo, hallazgos clave y recomendación final
- El backend construye un prompt estructurado con el perfil del dataset
- Fallback inteligente: si Gemini no está disponible, el sistema devuelve análisis estructurado desde los metadatos

### IA en el proceso de desarrollo
- **Claude (Anthropic)** asistió en arquitectura, generación de código y debugging
- Enfoque de **vibecoding**: desarrollo acelerado con IA como copiloto
- Prompt engineering para obtener análisis ejecutivos de calidad desde Gemini

---

## 🚀 Ejecutar en local

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# Variables de entorno
$env:GEMINI_API_KEY="tu_key"
$env:SUPABASE_URL="tu_url"
$env:SUPABASE_KEY="tu_key"

uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install

# Crear .env
echo "VITE_API_URL=http://localhost:8000" > .env

npm run dev
```

Abrir: `http://localhost:5173`

---

## 📦 Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/analyze` | Analiza un archivo Excel |
| GET | `/history` | Historial de análisis |
| GET | `/docs` | Swagger UI |

---

## 🌐 Deploy

- **Frontend:** Vercel — deploy automático desde `frontend/` al hacer push a `main`
- **Backend:** Railway — deploy automático desde `backend/` al hacer push a `main`
- **CI/CD:** GitHub → Railway/Vercel automático

---

## 👤 Autor

**Johan Vicente Asto Olivera**  
Software Developer & Automation Engineer · ZTE Corporation  
Electronic Engineering · PUCP
