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

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """AWS Lambda handler for AgentCore Gateway."""
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        # --- Input extraction & validation ---
        parameters = _extract_parameters(event)
        proceso_id = parameters.get("proceso_id", "").strip()

        if not proceso_id:
            return _error_response("El parámetro 'proceso_id' es obligatorio.")

        # --- Business logic ---
        resultado = _consultar_estado(proceso_id)

        # --- Success response ---
        return _success_response(resultado)

    except Exception as e:
        logger.exception("Error inesperado en consultar_estado_proceso")
        return _error_response(f"Error interno: {str(e)}")


def _extract_parameters(event: dict) -> dict:
    """Extract tool input parameters from the AgentCore Gateway event."""
    # AgentCore Gateway sends parameters in the 'inputText' or 'parameters' field
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
    # TODO: Implementar integración real con el BPMS
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
