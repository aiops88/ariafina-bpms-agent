"""
Lambda: consultar_estado_proceso
=================================
Consulta el estado actual de una instancia de proceso en el BPMS.

Input (via AgentCore Gateway):
    - proceso_id (str, required): Identificador único de la instancia de proceso.

Returns:
    JSON con estado, etapa, responsable, fechas y progreso.
"""

import json
import logging
import time
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging estructurado
# ---------------------------------------------------------------------------
logger = logging.getLogger("bpms.consultar_estado_proceso")
logger.setLevel(logging.INFO)

FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "consultar_estado_proceso")
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
        proceso_id = parameters.get("proceso_id", "").strip()

        if not proceso_id:
            _structured_log("warning", "Validación fallida: proceso_id vacío", request_id=request_id)
            return _error_response("El parámetro 'proceso_id' es obligatorio.")

        _structured_log("info", "Consultando proceso", request_id=request_id, proceso_id=proceso_id)

        # --- Business logic ---
        resultado = _consultar_estado(proceso_id)

        # --- Metrics ---
        duration_ms = round((time.time() - start_time) * 1000, 2)
        _structured_log(
            "info",
            "Consulta exitosa",
            request_id=request_id,
            proceso_id=proceso_id,
            estado=resultado["estado"],
            duration_ms=duration_ms,
            metric_name="ConsultaExitosa",
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
            metric_name="ConsultaError",
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


def _consultar_estado(proceso_id: str) -> dict:
    """Consulta el estado del proceso en el sistema BPMS.

    TODO: Reemplazar con llamada real al API del BPMS.
    - Conectar al endpoint de consulta de procesos.
    - Autenticar con credenciales del servicio.
    - Mapear la respuesta al formato esperado.
    """
    return {
        "proceso_id": proceso_id,
        "estado": "En curso",
        "etapa_actual": "Revisión documental",
        "responsable": "Juan Pérez",
        "fecha_inicio": "2026-06-15T09:00:00Z",
        "fecha_limite": "2026-07-10T17:00:00Z",
        "progreso_porcentaje": 65,
    }


def _success_response(body: dict) -> dict:
    """Format successful response for AgentCore Gateway."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "BPMSActions",
            "function": "consultar_estado_proceso",
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
            "function": "consultar_estado_proceso",
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps({"error": message}, ensure_ascii=False)
                    }
                }
            },
        },
    }
