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
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """AWS Lambda handler for AgentCore Gateway."""
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        # --- Input extraction & validation ---
        parameters = _extract_parameters(event)
        tarea_id = parameters.get("tarea_id", "").strip()
        comentario = parameters.get("comentario", "").strip()

        if not tarea_id:
            return _error_response("El parámetro 'tarea_id' es obligatorio.")

        # --- Business logic ---
        resultado = _cerrar_tarea(tarea_id, comentario)

        # --- Success response ---
        return _success_response(resultado)

    except Exception as e:
        logger.exception("Error inesperado en cerrar_tarea")
        return _error_response(f"Error interno: {str(e)}")


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
    # TODO: Implementar integración real con el motor de workflow del BPMS
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
