# Excel Insight Analyzer

Aplicación web full-stack que recibe archivos Excel, perfila automáticamente su estructura, genera métricas estadísticas e insights ejecutivos mediante IA Generativa, persiste los resultados y los expone a través de un dashboard moderno.

**App en vivo:** https://excel-insight-analyzer.vercel.app/  
**API Docs:** https://excel-insight-analyzer-production.up.railway.app/docs  
**Repositorio:** https://github.com/johanasto/excel-insight-analyzer

---

## Caso de uso

**Opción A — IA Dashboard desde Excel**

Los archivos Excel contienen información valiosa pero difícil de interpretar rápidamente de forma consistente. Esta aplicación transforma cualquier tabla Excel en un análisis estructurado con métricas automáticas e interpretación ejecutiva generada por IA, sin depender de un formato rígido.

---

## Arquitectura general

Arquitectura desacoplada de cuatro capas:

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Vue.js + Vite)                               │
│  Carga de archivo · Dashboard · Historial               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST /analyze
┌────────────────────────▼────────────────────────────────┐
│  Backend (FastAPI + Python)                             │
│  Validación · Perfilado · Métricas · Prompt · IA        │
└───────┬──────────────────────────────────┬──────────────┘
        │                                  │
┌───────▼──────────┐            ┌──────────▼──────────────┐
│  Supabase        │            │  Gemini API              │
│  PostgreSQL      │            │  Resumen ejecutivo       │
│  Persistencia    │            │  Hallazgos · Recomendación│
└──────────────────┘            └─────────────────────────┘
```

---

## Flujo funcional

1. El usuario sube un archivo Excel desde el frontend
2. El frontend envía el archivo al backend via `POST /analyze`
3. El backend valida que sea un Excel válido
4. El backend lee la primera hoja útil con pandas
5. El backend perfila el dataset detectando: identificadores, fechas, numéricas, categóricas, descriptivas
6. El backend calcula métricas: estadísticas numéricas, resumen categórico, rangos de fechas, muestras de texto
7. El backend construye un contexto estructurado del dataset
8. Gemini recibe el contexto y genera resumen ejecutivo, hallazgos clave y recomendación
9. El resultado se persiste en Supabase
10. El frontend renderiza el dashboard con KPIs, perfil de columnas, distribuciones y análisis IA

---

## Stack tecnológico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Frontend | Vue.js + Vite + Axios | Framework exigido, bajo overhead, ideal para dashboard MVP |
| Backend | FastAPI + Uvicorn | API asíncrona, integración natural con pandas, Swagger automático |
| Procesamiento | Pandas + OpenPyXL | Lectura de Excel, detección de tipos, estadísticas descriptivas |
| IA Generativa | Gemini API | Costo cero, suficiente para análisis ejecutivo de calidad |
| Base de datos | Supabase (PostgreSQL) | Free tier, JSONB para columnas dinámicas, API REST automática |
| Deploy Frontend | Vercel | CI/CD automático desde GitHub |
| Deploy Backend | Railway | CI/CD automático desde GitHub, soporte nativo FastAPI |

---

## Modelo de datos

**Tabla principal:** `analysis_results`

```sql
id                       uuid        PRIMARY KEY DEFAULT gen_random_uuid()
file_name                text        NOT NULL
rows                     integer
columns                  integer
column_names             jsonb       -- ["col1", "col2", ...]
identifier_columns       jsonb       -- columnas tipo ID o código
date_columns             jsonb       -- columnas de fecha detectadas
numeric_columns          jsonb       -- columnas numéricas
categorical_columns      jsonb       -- columnas de baja cardinalidad
descriptive_text_columns jsonb       -- columnas de texto libre
metrics                  jsonb       -- {numeric_summary, categorical_summary, date_summary, text_samples}
ai_summary               text        -- resumen ejecutivo generado por Gemini
created_at               timestamp   DEFAULT now()
```

### Por qué JSONB

La estructura de un Excel no es fija. Cada tabla puede tener diferente cantidad de columnas, tipos y distribuciones. JSONB permite almacenar columnas dinámicas sin cambiar el esquema, consultar métricas con operadores PostgreSQL nativos y evolucionar el modelo sin migraciones destructivas. Se mantiene la robustez de PostgreSQL con la flexibilidad de un esquema semi-estructurado.

### Qué se persiste

Se persiste metadata del archivo, clasificación de columnas, métricas calculadas y resumen IA. No se persisten las filas originales del Excel. El objetivo es demostrar valor analítico, no construir un ETL completo.

---

## Motor de análisis — Clasificación de columnas

Heurística propia para clasificar columnas de forma flexible sin depender de un formato rígido:

**Identificadores:** nombres exactos como `id`, `codigo`, `ticket` o sufijos como `_id`, `_key`

**Fechas:** conversión con `pd.to_datetime(..., errors="coerce", format="mixed")`. Si al menos 70% de los valores se parsean como fecha, se clasifica como columna de fecha.

**Numéricas (con soporte para datos sucios):** conversión con `pd.to_numeric(..., errors="coerce")`. Si al menos 70% se convierte, se clasifica como numérica.

**Categóricas vs descriptivas:** baja cardinalidad y textos cortos → categórica. Alta variabilidad o longitud promedio mayor → descriptiva (texto libre).

**Casos borde soportados:**
- Columnas numéricas con texto mezclado
- Fechas inválidas o parcialmente válidas
- Valores faltantes (NaN)
- Archivos vacíos o con solo encabezados
- Archivos que no son Excel (error amigable)

---

## Integración de IA Generativa

### IA dentro de la aplicación

Gemini no recibe el archivo completo. El backend construye un contexto estructurado con el perfil del dataset, métricas calculadas y muestras de texto. Sobre ese contexto, Gemini genera:

1. Resumen ejecutivo orientado a toma de decisiones
2. Hallazgos clave: patrones, anomalías, observaciones relevantes
3. Recomendación final accionable

**Fallback inteligente:** si Gemini no está disponible, el sistema genera automáticamente un análisis estructurado de respaldo desde los metadatos. El flujo no se interrumpe.

### IA en el proceso de desarrollo

- Claude (Anthropic) asistió en diseño de arquitectura, generación de código y debugging
- Enfoque de vibecoding: desarrollo acelerado con IA como copiloto
- Prompt engineering para obtener análisis ejecutivos consistentes

---

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del servicio |
| POST | `/analyze` | Recibe Excel, procesa, llama a IA, guarda en Supabase, devuelve JSON |
| GET | `/history` | Historial de análisis persistidos |
| GET | `/docs` | Swagger UI automático |

### Estructura del JSON de respuesta

```json
{
  "file_name": "dataset.xlsx",
  "rows": 15,
  "columns": 12,
  "identifier_columns": ["ID_Envio"],
  "date_columns": ["Fecha_Pedido", "Fecha_Entrega"],
  "numeric_columns": ["Cantidad", "Peso_kg", "Costo_Envio"],
  "categorical_columns": ["Region", "Estado", "Prioridad"],
  "descriptive_text_columns": ["Cliente", "Producto", "Observaciones"],
  "metrics": {
    "numeric_summary": { "Cantidad": { "mean": 49.1, "min": 3, "max": 200, "count": 14 } },
    "categorical_summary": { "Region": { "Lima": 5, "Arequipa": 3, "Cusco": 3 } },
    "date_summary": { "Fecha_Pedido": { "min": "2025-02-01", "max": "2025-02-17" } },
    "descriptive_text_samples": { "Observaciones": ["Entrega retrasada", "Costo negativo"] }
  },
  "ai_summary": "Resumen ejecutivo generado por Gemini...",
  "ai_error": null,
  "fallback_summary": null
}
```

---

## Ejecutar en local

### Requisitos
- Python 3.10+
- Node.js 18+
- Gemini API Key (opcional, hay fallback)
- Cuenta Supabase (opcional para persistencia)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / Mac

pip install -r requirements.txt

# Variables de entorno
$env:GEMINI_API_KEY="tu_key"
$env:SUPABASE_URL="tu_url"
$env:SUPABASE_KEY="tu_key"

uvicorn app.main:app --reload --port 8000
```

Swagger en: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

App en: `http://localhost:5173`

---

## Estructura del repositorio

```
excel-insight-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, CORS, endpoints
│   │   └── services/
│   │       ├── excel_service.py  # Lectura y validación del Excel
│   │       ├── profile_service.py # Clasificación de columnas y métricas
│   │       ├── ai_service.py     # Integración Gemini API
│   │       └── db_service.py     # Persistencia en Supabase
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.vue               # Componente principal y dashboard
│   │   ├── main.js
│   │   └── services/
│   │       └── api.js            # Llamadas al backend
│   └── vite.config.js
└── README.md
```

---

## Deploy

| Servicio | Plataforma | Trigger |
|----------|-----------|---------|
| Frontend | Vercel | Push a `main` desde `frontend/` |
| Backend | Railway | Push a `main` desde `backend/` |
| Base de datos | Supabase | Siempre activo |

CI/CD completamente automático desde GitHub.

---

## Mejoras futuras

- Soporte para múltiples hojas simultáneo
- Scoring automático de calidad de datos
- Clustering semántico de texto libre
- Autenticación de usuarios
- Dashboard comparativo entre análisis del historial
- Exportación del análisis a PDF

---

## Autor

**Johan Vicente Asto Olivera**  
Software Developer & Automation Engineer — ZTE Corporation  
Electronic Engineering — PUCP
