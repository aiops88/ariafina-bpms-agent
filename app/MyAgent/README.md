# Ariafina BPMS — Agente Conversacional

Agente conversacional inteligente para la gestión de procesos de negocio (BPMS) de Ariafina. Construido con [Strands Agents SDK](https://github.com/strands-agents/sdk-python) y desplegado en Amazon Bedrock AgentCore.

## Funcionalidades

| Herramienta | Descripción |
| --- | --- |
| `consultar_estado_proceso` | Consulta el estado actual de una instancia de proceso |
| `identificar_tipo_documental` | Identifica el tipo documental según la descripción o caso |
| `cerrar_tarea` | Cierra (completa) una tarea pendiente en el flujo de trabajo |
| `consultar_base_conocimiento` | Búsqueda semántica en la Knowledge Base de Bedrock (`RGU2WF39WW`) |

## Requisitos previos

- Python 3.10 o superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (gestor de paquetes)
- AWS CLI configurado con credenciales que tengan acceso a Bedrock y a la Knowledge Base
- AgentCore CLI instalado (`npm i -g @aws/agentcore-cli`)

## Instalación

```bash
# Clonar el repositorio y navegar al directorio del agente
cd app/MyAgent

# Crear entorno virtual e instalar dependencias
uv venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
uv pip install -e .
```

## Variables de entorno

Crear un archivo `.env.local` en la raíz del proyecto (`agentcore/.env.local`) con las claves necesarias:

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `LOCAL_DEV` | No | Establecer en `1` para usar `.env.local` en lugar de AgentCore Identity |

## Desarrollo local

```bash
# Activar el entorno virtual
source .venv/bin/activate   # En Windows: .venv\Scripts\activate

# Iniciar el servidor local (puerto 8080)
agentcore dev

# En otra terminal, invocar el agente
agentcore invoke --dev "¿Cuál es el estado del proceso PROC-2024-001?"
```

## Despliegue

```bash
# Validar la configuración
agentcore validate

# Desplegar en Amazon Bedrock AgentCore
agentcore deploy

# Verificar el estado
agentcore status

# Invocar el agente desplegado
agentcore invoke "Necesito cerrar la tarea TASK-5012"
```

## Estructura del proyecto

```
app/MyAgent/
├── agent.py            # Punto de entrada principal del agente BPMS
├── main.py             # Entrypoint original (referencia)
├── model/
│   └── load.py         # Configuración del modelo LLM
├── mcp_client/
│   └── client.py       # Cliente MCP para herramientas externas
├── memory/
│   └── session.py      # Gestión de sesiones con memoria
├── skills/
│   └── fetcher.py      # Skills adicionales
├── pyproject.toml      # Dependencias del proyecto
└── README.md           # Este archivo
```

## Base de conocimiento

El agente está conectado a la Knowledge Base de Bedrock con ID `RGU2WF39WW` en la región `us-east-1`. La herramienta `consultar_base_conocimiento` realiza búsquedas semánticas y devuelve los 5 fragmentos más relevantes con su puntuación y fuente.

## Personalización

Los tools de BPMS (`consultar_estado_proceso`, `identificar_tipo_documental`, `cerrar_tarea`) actualmente devuelven respuestas mock. Para conectarlos al sistema real:

1. Buscar los comentarios `# TODO` en `agent.py`
2. Reemplazar las respuestas mock con llamadas al API del BPMS
3. Configurar las credenciales necesarias en `.env.local`
