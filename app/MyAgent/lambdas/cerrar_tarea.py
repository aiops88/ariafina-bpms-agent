"""
Lambda: cerrar_tarea
=====================
Cierra (completa) una tarea pendiente en el flujo de trabajo del BPMS.

Input (via AgentCore Gateway):
    - tarea_id (str, required): Identificador único de la tarea a cerrar.
    - comentario (str, optional): Comentario o nota de cierre.

Returns:
    JSON con confirmación de cierre, fecha y usuario que cerró.
"""

import json
import logging
import time
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging estructurado
# ---------------------------------------------------------------------------
logger = logging.getLogger("bpms.cerrar_tarea")
logger.setLevel(logging.INFO)

FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "cerrar_tarea")
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
        tarea_id = parameters.get("tarea_id", "").strip()
        comentario = parameters.get("comentario", "").strip()

        if not tarea_id:
            _structured_log("warning", "Validación fallida: tarea_id vacío", request_id=request_id)
            return _error_response("El parámetro 'tarea_id' es obligatorio.")

        _structured_log(
            "info",
            "Cerrando tarea",
            request_id=request_id,
            tarea_id=tarea_id,
            tiene_comentario=bool(comentario),
        )

        # --- Business logic ---
        resultado = _cerrar_tarea(tarea_id, comentario)

        # --- Metrics ---
        duration_ms = round((time.time() - start_time) * 1000, 2)
        _structured_log(
            "info",
            "Tarea cerrada exitosamente",
            request_id=request_id,
            tarea_id=tarea_id,
            duration_ms=duration_ms,
            metric_name="TareaCerrada",
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
            metric_name="CierreTareaError",
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


def _cerrar_tarea(tarea_id: str, comentario: str) -> dict:
    """Cierra la tarea en el sistema BPMS.

    TODO: Reemplazar con llamada real al API del BPMS.
    - Verificar que la tarea existe y está en estado 'Abierta' o 'En progreso'.
    - Validar permisos del usuario para cerrar la tarea.
    - Ejecutar la transición de estado en el motor de workflow.
    - Registrar el comentario de cierre en el historial de la tarea.
    """
    fecha_cierre = datetime.now(timezone.utc).isoformat()

    return {
        "tarea_id": tarea_id,
        "estado": "Cerrada",
        "comentario": comentario or "Tarea completada satisfactoriamente.",
        "fecha_cierre": fecha_cierre,
        "cerrada_por": "Asistente BPMS",
    }


def _success_response(body: dict) -> dict:
    """Format successful response for AgentCore Gateway."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "BPMSActions",
            "function": "cerrar_tarea",
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
            "function": "cerrar_tarea",
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps({"error": message}, ensure_ascii=False)
                    }
                }
            },
        },
    }
