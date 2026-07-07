"""
BPMS Conversational Assistant Agent
====================================
Provides tools for interacting with a Business Process Management System (BPMS):
- consultar_estado_proceso: Check process instance status
- identificar_tipo_documental: Identify document type for a case
- cerrar_tarea: Close/complete a task

Also integrates a Bedrock Knowledge Base (RGU2WF39WW) for retrieval-augmented answers.
"""

import json
import boto3
from typing import Any
from strands import Agent, tool
from strands.agent.conversation_manager.null_conversation_manager import NullConversationManager
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from mcp_client.client import get_streamable_http_mcp_client
from memory.session import get_memory_session_manager

app = BedrockAgentCoreApp()
log = app.logger

# ---------------------------------------------------------------------------
# Knowledge Base configuration
# ---------------------------------------------------------------------------
KNOWLEDGE_BASE_ID = "RGU2WF39WW"
KNOWLEDGE_BASE_REGION = "us-east-1"

_kb_client = boto3.client("bedrock-agent-runtime", region_name=KNOWLEDGE_BASE_REGION)

# ---------------------------------------------------------------------------
# MCP clients
# ---------------------------------------------------------------------------
mcp_clients = [get_streamable_http_mcp_client()]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
DEFAULT_SYSTEM_PROMPT = """
Eres el asistente virtual de Ariafina BPMS. Tu función es ayudar a los empleados a
interactuar con el sistema de gestión de procesos sin necesidad de navegar manualmente
por la plataforma.

Capacidades:
- Consultar el estado de procesos e instancias activas.
- Identificar el tipo documental requerido para un trámite o expediente.
- Cerrar tareas pendientes en los flujos de trabajo asignados.
- Responder preguntas sobre procedimientos y normativas usando la base de conocimiento.

Reglas:
- Responde siempre en español.
- Sé conciso y profesional. Ve directo a la información solicitada.
- Usa las herramientas disponibles antes de responder con suposiciones.
- Si no tienes información suficiente, pide al usuario los datos que faltan.
- No inventes datos. Si una herramienta devuelve un error, informa al usuario.
"""

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
tools: list[Any] = []


@tool
def consultar_estado_proceso(proceso_id: str) -> str:
    """Consulta el estado actual de una instancia de proceso en el BPMS.

    Args:
        proceso_id: Identificador único de la instancia de proceso (ej: "PROC-2024-001").

    Returns:
        JSON con el estado actual del proceso, incluyendo etapa, responsable y fechas.
    """
    # TODO: Reemplazar con llamada real al API del BPMS
    mock_response = {
        "proceso_id": proceso_id,
        "estado": "En curso",
        "etapa_actual": "Revisión documental",
        "responsable": "Juan Pérez",
        "fecha_inicio": "2026-06-15T09:00:00Z",
        "fecha_limite": "2026-07-10T17:00:00Z",
        "progreso_porcentaje": 65,
    }
    return json.dumps(mock_response, ensure_ascii=False)


@tool
def identificar_tipo_documental(descripcion: str, caso_id: str = "") -> str:
    """Identifica el tipo documental apropiado según la descripción del documento o caso.

    Args:
        descripcion: Descripción del documento o contexto del trámite.
        caso_id: (Opcional) Identificador del caso asociado para mayor precisión.

    Returns:
        JSON con el tipo documental identificado y metadatos asociados.
    """
    # TODO: Reemplazar con llamada real al clasificador documental
    mock_response = {
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
    return json.dumps(mock_response, ensure_ascii=False)


@tool
def cerrar_tarea(tarea_id: str, comentario: str = "") -> str:
    """Cierra (completa) una tarea pendiente en el flujo de trabajo del BPMS.

    Args:
        tarea_id: Identificador único de la tarea a cerrar (ej: "TASK-5012").
        comentario: (Opcional) Comentario o nota de cierre.

    Returns:
        JSON con la confirmación de cierre y datos de la tarea.
    """
    # TODO: Reemplazar con llamada real al API del BPMS
    mock_response = {
        "tarea_id": tarea_id,
        "estado": "Cerrada",
        "comentario": comentario or "Tarea completada satisfactoriamente.",
        "fecha_cierre": "2026-07-06T14:30:00Z",
        "cerrada_por": "Asistente BPMS",
    }
    return json.dumps(mock_response, ensure_ascii=False)


@tool
def consultar_base_conocimiento(consulta: str) -> str:
    """Busca información relevante en la base de conocimiento del BPMS usando retrieval semántico.

    Args:
        consulta: Pregunta o texto de búsqueda en lenguaje natural.

    Returns:
        Texto con los fragmentos más relevantes encontrados en la base de conocimiento.
    """
    try:
        response = _kb_client.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": consulta},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                }
            },
        )
        results = response.get("retrievalResults", [])
        if not results:
            return "No se encontraron resultados relevantes en la base de conocimiento."

        fragments = []
        for i, result in enumerate(results, 1):
            content = result.get("content", {}).get("text", "")
            score = result.get("score", 0)
            source = result.get("location", {}).get("s3Location", {}).get("uri", "desconocido")
            fragments.append(
                f"[{i}] (relevancia: {score:.2f}) Fuente: {source}\n{content}"
            )
        return "\n\n---\n\n".join(fragments)

    except Exception as e:
        log.error(f"Error al consultar la base de conocimiento: {e}")
        return f"Error al consultar la base de conocimiento: {str(e)}"


# Register all tools
tools.append(consultar_estado_proceso)
tools.append(identificar_tipo_documental)
tools.append(cerrar_tarea)
tools.append(consultar_base_conocimiento)

# Add MCP clients
for mcp_client in mcp_clients:
    if mcp_client:
        tools.append(mcp_client)

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def _make_conversation_manager():
    return NullConversationManager()


def agent_factory():
    cache = {}

    def get_or_create_agent(session_id, user_id):
        actor_id = user_id
        key = f"{session_id}/{actor_id}"
        if key not in cache:
            cache[key] = Agent(
                model=load_model(),
                session_manager=get_memory_session_manager(session_id, actor_id),
                conversation_manager=_make_conversation_manager(),
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                tools=tools,
                hooks=[],
            )
        return cache[key]

    return get_or_create_agent


get_or_create_agent = agent_factory()

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

_INLINE_FUNCTION_NAMES: set[str] = set()


def _extract_prompt(payload: dict):
    """Accept harness-style messages[], tool_results[], or plain prompt string payloads."""
    if "messages" in payload:
        return payload["messages"]
    if "tool_results" in payload:
        return [{"role": "user", "content": [{"toolResult": {
            "toolUseId": tr["toolUseId"],
            "status": tr.get("status", "success"),
            "content": tr.get("content", []),
        }} for tr in payload["tool_results"]]}]
    return payload.get("prompt", "")


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking BPMS Agent...")

    session_id = getattr(context, "session_id", "default-session")
    user_id = getattr(context, "user_id", "default-user")
    agent = get_or_create_agent(session_id, user_id)

    prompt = _extract_prompt(payload)

    async for event in agent.stream_async(prompt):
        if not isinstance(event, dict) or "event" not in event:
            continue
        cbs = event["event"].get("contentBlockStart")
        if cbs is not None and not cbs.get("start"):
            continue
        yield event


if __name__ == "__main__":
    app.run()
