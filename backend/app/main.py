from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO
import os
import math
from datetime import datetime

from app.services.ai_service import generate_summary
from app.db.supabase_client import supabase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# CLEAN JSON (FIX ERROR 500)
# =========================
def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, tuple):
        return [clean_for_json(v) for v in obj]
    elif pd.isna(obj):
        return None
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    return obj


# =========================
# CLASIFICADOR MEJORADO
# =========================
def classify_columns(df: pd.DataFrame):
    identifier_columns = []
    date_columns = []
    numeric_columns = []
    categorical_columns = []
    descriptive_text_columns = []

    exact_identifier_names = {
        "id", "codigo", "código", "indice", "índice", "index",
        "nro", "numero", "número", "folio", "ticket"
    }

    identifier_suffixes = ("_id", "_codigo", "_código", "_index", "_indice", "_índice")

    for col in df.columns:
        col_name = str(col).strip().lower()
        normalized_name = col_name.replace(" ", "_").replace("-", "_")
        series = df[col].dropna()

        # 1. IDENTIFICADORES
        if (
            normalized_name in exact_identifier_names
            or normalized_name.endswith(identifier_suffixes)
            or normalized_name.startswith("id_")
        ):
            identifier_columns.append(col)
            continue

        # 2. FECHAS: primero intentamos detectar fechas antes que numéricos
        try:
            series_str = df[col].astype(str).str.strip()
            parsed = pd.to_datetime(series_str, errors="coerce", format="mixed")
            valid_date_ratio = parsed.notna().sum() / len(df[col]) if len(df[col]) > 0 else 0

            # solo considerar fecha si no es una columna claramente numérica
            if valid_date_ratio > 0.7 and not pd.api.types.is_numeric_dtype(df[col]):
                date_columns.append(col)
                continue
        except Exception:
            pass

        # 3. NUMÉRICOS LIMPIOS
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col)
            continue

        # 4. NUMÉRICOS SUCIOS (ej: "10", "20", "abc")
        converted = pd.to_numeric(df[col], errors="coerce")
        valid_numeric_ratio = converted.notna().sum() / len(df[col]) if len(df[col]) > 0 else 0
        if valid_numeric_ratio > 0.7:
            numeric_columns.append(col)
            continue

        # 5. TEXTO
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            if len(series) == 0:
                continue

            series_str = series.astype(str).str.strip()
            unique_count = series_str.nunique()
            total_count = len(series_str)
            avg_length = series_str.map(len).mean()
            unique_ratio = unique_count / total_count if total_count > 0 else 0

            if unique_count <= 20 and avg_length < 40 and unique_ratio < 0.9:
                categorical_columns.append(col)
            else:
                descriptive_text_columns.append(col)

    return {
        "identifier_columns": identifier_columns,
        "date_columns": date_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "descriptive_text_columns": descriptive_text_columns,
    }


# =========================
# FALLBACK
# =========================
def build_fallback_summary(file_name, rows, cols, profile, metrics):
    findings = []

    findings.append(f"El archivo {file_name} contiene {rows} filas y {cols} columnas.")
    findings.append(
        f"Se detectaron {len(profile['descriptive_text_columns'])} columnas descriptivas, "
        f"{len(profile['categorical_columns'])} categóricas, "
        f"{len(profile['numeric_columns'])} numéricas y "
        f"{len(profile['date_columns'])} de fecha."
    )

    recommendation = (
        "Se recomienda analizar las columnas descriptivas, categóricas y temporales para identificar patrones y anomalías."
    )

    return {
        "executive_summary": " ".join(findings),
        "key_findings": findings[:3],
        "recommendation": recommendation,
    }


# =========================
# ENDPOINTS
# =========================
@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # =========================
        # VALIDACIÓN DE ARCHIVO
        # =========================
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            return {
                "error": "Formato de archivo no soportado. Solo se permiten archivos Excel (.xlsx, .xls)"
            }

        # =========================
        # LECTURA SEGURA
        # =========================
        try:
            df = pd.read_excel(BytesIO(contents))
        except Exception:
            return {
                "error": "No se pudo leer el archivo Excel. Verifique que no esté corrupto."
            }

        rows, cols = df.shape
        columns = df.columns.tolist()

        # =========================
        # CASO: ARCHIVO TOTALMENTE VACÍO
        # =========================
        if rows == 0 and cols == 0:
            return clean_for_json({
                "file_name": file.filename,
                "rows": 0,
                "columns": 0,
                "column_names": [],
                "identifier_columns": [],
                "date_columns": [],
                "numeric_columns": [],
                "categorical_columns": [],
                "descriptive_text_columns": [],
                "metrics": {},
                "ai_summary": "El archivo está completamente vacío.",
                "ai_error": None,
                "fallback_summary": None
            })

        # =========================
        # PERFILADO
        # =========================
        profile = classify_columns(df)

        metrics = {}

        # =========================
        # NUMERIC SUMMARY
        # =========================
        if profile["numeric_columns"]:
            numeric_df = df[profile["numeric_columns"]].copy()

            for col in numeric_df.columns:
                numeric_df[col] = pd.to_numeric(numeric_df[col], errors="coerce")

            if not numeric_df.empty:
                metrics["numeric_summary"] = numeric_df.describe().to_dict()

        # =========================
        # DATE SUMMARY
        # =========================
        if profile["date_columns"]:
            date_summary = {}
            for col in profile["date_columns"]:
                parsed = pd.to_datetime(
                    df[col].astype(str).str.strip(),
                    errors="coerce",
                    format="mixed"
                )

                date_summary[col] = {
                    "count_valid": int(parsed.notna().sum()),
                    "min": parsed.min(),
                    "max": parsed.max()
                }

            metrics["date_summary"] = date_summary

        # =========================
        # CATEGORICAL SUMMARY
        # =========================
        if profile["categorical_columns"]:
            categorical_summary = {}
            for col in profile["categorical_columns"]:
                categorical_summary[col] = (
                    df[col]
                    .astype(str)
                    .value_counts()
                    .head(5)
                    .to_dict()
                )
            metrics["categorical_summary"] = categorical_summary

        # =========================
        # TEXT SAMPLE
        # =========================
        if profile["descriptive_text_columns"]:
            descriptive_samples = {}
            for col in profile["descriptive_text_columns"]:
                descriptive_samples[col] = (
                    df[col]
                    .astype(str)
                    .dropna()
                    .head(5)
                    .tolist()
                )
            metrics["descriptive_text_samples"] = descriptive_samples

        # =========================
        # CONTEXTO IA
        # =========================
        analysis_context = f"""
Archivo: {file.filename}
Filas: {rows}
Columnas: {cols}
Columnas identificadoras: {profile['identifier_columns']}
Columnas de fecha: {profile['date_columns']}
Columnas numéricas: {profile['numeric_columns']}
Columnas categóricas: {profile['categorical_columns']}
Columnas descriptivas: {profile['descriptive_text_columns']}
Métricas: {metrics}
"""

        gemini_api_key = os.getenv("GEMINI_API_KEY")

        ai_summary = None
        ai_error = None
        fallback_summary = None

        if gemini_api_key:
            try:
                ai_summary = generate_summary(gemini_api_key, analysis_context)
            except Exception as ai_exc:
                ai_error = str(ai_exc)
                fallback_summary = build_fallback_summary(
                    file.filename, rows, cols, profile, metrics
                )
        else:
            ai_error = "GEMINI_API_KEY no configurada"
            fallback_summary = build_fallback_summary(
                file.filename, rows, cols, profile, metrics
            )

        # =========================
        # RESPUESTA SEGURA
        # =========================
        safe_response = clean_for_json({
            "file_name": file.filename,
            "rows": rows,
            "columns": cols,
            "column_names": columns,
            "identifier_columns": profile["identifier_columns"],
            "date_columns": profile["date_columns"],
            "numeric_columns": profile["numeric_columns"],
            "categorical_columns": profile["categorical_columns"],
            "descriptive_text_columns": profile["descriptive_text_columns"],
            "metrics": metrics,
            "ai_summary": ai_summary,
            "ai_error": ai_error,
            "fallback_summary": fallback_summary
        })

        # =========================
        # GUARDADO (OPCIONAL)
        # =========================
        if supabase:
            try:
                supabase.table("analysis_results").insert({
                    "file_name": file.filename,
                    "rows": rows,
                    "columns": cols,
                    "column_names": safe_response["column_names"],
                    "identifier_columns": safe_response["identifier_columns"],
                    "date_columns": safe_response.get("date_columns", []),
                    "numeric_columns": safe_response["numeric_columns"],
                    "categorical_columns": safe_response["categorical_columns"],
                    "descriptive_text_columns": safe_response["descriptive_text_columns"],
                    "metrics": safe_response["metrics"],
                    "ai_summary": safe_response["ai_summary"]
                }).execute()
            except Exception as db_error:
                print("Error guardando en Supabase:", db_error)
        else:
            print("Supabase no configurado todavía.")

        return safe_response

    except Exception as e:
        return {"error": str(e)}
    

@app.get("/history")
def get_history():
    try:
        if not supabase:
            return {"error": "Supabase no configurado"}

        response = supabase.table("analysis_results").select("*").order("created_at", desc=True).execute()

        return clean_for_json(response.data)

    except Exception as e:
        return {"error": str(e)}