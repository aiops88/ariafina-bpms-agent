"""
Lambda: identificar_tipo_documental
=====================================
Identifica el tipo documental apropiado según la descripción del documento o caso.

Input (via AgentCore Gateway):
    - descripcion (str, required): Descripción del documento o contexto del trámite.
    - caso_id (str, optional): Identificador del caso asociado.

Returns:
    JSON con tipo documental, código de tipología, serie, subserie y retención.
"""

import json
import logging
import time
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging estructurado
# ---------------------------------------------------------------------------
logger = logging.getLogger("bpms.identificar_tipo_documental")
logger.setLevel(logging.INFO)

FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "identificar_tipo_documental")
FUNCTION_VERSION = os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "$LOCAL")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")


def _structured_log(level: str, message: str, **extra):
    """Emit a structured JSON log line for CloudWatch Insights."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "function": FUNCTION_NAME,
        "version": FUNCTION_VERSION,
        "environment": ENVIRONMENT,
        "message": message,
        **extra,
    }
    getattr(logger, level.lower(), logger.info)(json.dumps(log_entry, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------
def handler(event, context):
    """AWS Lambda handler for AgentCore Gateway."""
    start_time = time.time()
    request_id = getattr(context, "aws_request_id", "local") if context else "local"

    _structured_log("info", "Invocación recibida", request_id=request_id, event_keys=list(event.keys()))

    try:
        # --- Input extraction & validation ---
        parameters = _extract_parameters(event)
        descripcion = parameters.get("descripcion", "").strip()
        caso_id = parameters.get("caso_id", "").strip()

        if not descripcion:
            _structured_log("warning", "Validación fallida: descripcion vacía", request_id=request_id)
            return _error_response("El parámetro 'descripcion' es obligatorio.")

        if len(descripcion) < 5:
            _structured_log(
                "warning",
                "Validación fallida: descripcion muy corta",
                request_id=request_id,
                descripcion_length=len(descripcion),
            )
            return _error_response(
                "La descripción debe tener al menos 5 caracteres para una clasificación precisa."
            )

        _structured_log(
            "info",
            "Clasificando documento",
            request_id=request_id,
            caso_id=caso_id or "N/A",
            descripcion_length=len(descripcion),
        )

        # --- Business logic ---
        resultado = _identificar_tipo(descripcion, caso_id)

        # --- Metrics ---
        duration_ms = round((time.time() - start_time) * 1000, 2)
        _structured_log(
            "info",
            "Clasificación exitosa",
            request_id=request_id,
            tipo_documental=resultado["tipo_documental"],
            codigo_tipologia=resultado["codigo_tipologia"],
            duration_ms=duration_ms,
            metric_name="ClasificacionExitosa",
            metric_value=1,
        )

        return _success_response(resultado)

    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        _structured_log(
            "error",
            "Error inesperado",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            metric_name="ClasificacionError",
            metric_value=1,
        )
        return _error_response(f"Error interno: {str(e)}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_parameters(event: dict) -> dict:
    """Extract tool input parameters from the AgentCore Gateway event."""
    if "parameters" in event:
        return {p["name"]: p["value"] for p in event["parameters"]}
    if "inputText" in event:
        try:
            return json.loads(event["inputText"])
        except (json.JSONDecodeError, TypeError):
            return {}
    return event.get("body", {}) if isinstance(event.get("body"), dict) else {}


def _identificar_tipo(descripcion: str, caso_id: str) -> dict:
    """Clasifica el documento según su descripción.

    TODO: Reemplazar con llamada real al clasificador documental.
    - Conectar al servicio de clasificación (ML o reglas).
    - Consultar la Tabla de Retención Documental (TRD) vigente.
    - Validar contra el caso_id si se proporcionó.
    """
    return {
        "caso_id": caso_id or "N/A",
        "descripcion_entrada": descripcion,
        "tipo_documental": "Acta de reunión",
        "codigo_tipologia": "TRD-AC-003",
        "serie_documental": "Actas",
        "subserie": "Actas de comité",
        "retencion_archivo_gestion": "5 años",
        "retencion_archivo_central": "10 años",
        "disposicion_final": "Conservación total",
    }


def _success_response(body: dict) -> dict:
    """Format successful response for AgentCore Gateway."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "BPMSActions",
            "function": "identificar_tipo_documental",
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(body, ensure_ascii=False)
                    }
                }
            },
        },
    }


def _error_response(message: str) -> dict:
    """Format error response for AgentCore Gateway."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "BPMSActions",
            "function": "identificar_tipo_documental",
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps({"error": message}, ensure_ascii=False)
                    }
                }
            },
        },
    }
