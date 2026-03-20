from google import genai


def generate_summary(api_key: str, analysis_context: str) -> str:
    client = genai.Client(api_key=api_key)

    prompt = f"""
Actúa como un analista de datos senior.

Recibirás el análisis preliminar de un archivo Excel.
Tu tarea es generar:

1. un resumen ejecutivo breve
2. tres hallazgos clave
3. una recomendación final

No inventes información que no esté en los datos.

Análisis del archivo:
{analysis_context}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text