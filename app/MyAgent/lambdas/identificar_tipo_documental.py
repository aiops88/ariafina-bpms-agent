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

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """AWS Lambda handler for AgentCore Gateway."""
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        # --- Input extraction & validation ---
        parameters = _extract_parameters(event)
        descripcion = parameters.get("descripcion", "").strip()
        caso_id = parameters.get("caso_id", "").strip()

        if not descripcion:
            return _error_response("El parámetro 'descripcion' es obligatorio.")

        if len(descripcion) < 5:
            return _error_response(
                "La descripción debe tener al menos 5 caracteres para una clasificación precisa."
            )

        # --- Business logic ---
        resultado = _identificar_tipo(descripcion, caso_id)

        # --- Success response ---
        return _success_response(resultado)

    except Exception as e:
        logger.exception("Error inesperado en identificar_tipo_documental")
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


def _identificar_tipo(descripcion: str, caso_id: str) -> dict:
    """Clasifica el documento según su descripción.

    TODO: Reemplazar con llamada real al clasificador documental.
    - Conectar al servicio de clasificación (ML o reglas).
    - Consultar la Tabla de Retención Documental (TRD) vigente.
    - Validar contra el caso_id si se proporcionó.
    """
    # TODO: Implementar integración real con el clasificador documental
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
