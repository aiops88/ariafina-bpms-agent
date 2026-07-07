# Evidencias de Despliegue — Ariafina BPMS Agent

**Proyecto:** Agente Conversacional Inteligente para Gestión de Procesos de Negocio  
**Fecha de despliegue:** 7 de julio de 2026  
**Región AWS:** us-east-1  
**Cuenta AWS:** 145405817802  
**Case de soporte activo:** #178345165800122 (throttling de tokens)

---

## 1. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USUARIO / FRONTEND                          │
│                    (HTML + Cognito Auth + JWT)                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS + Bearer Token
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Amazon Bedrock AgentCore Runtime                        │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  agent.py   │  │  Guardrails  │  │  Amazon Nova Lite (LLM)  │  │
│  │  (Strands)  │──│  n45cp9ulfxgk│──│  us.amazon.nova-lite-v1  │  │
│  └──────┬──────┘  └──────────────┘  └──────────────────────────┘  │
│         │                                                           │
│         ├── Tool: consultar_estado_proceso (inline mock)            │
│         ├── Tool: identificar_tipo_documental (inline mock)         │
│         ├── Tool: cerrar_tarea (inline mock)                        │
│         ├── Tool: consultar_base_conocimiento (KB retrieve)         │
│         └── MCP Client: Exa AI (web search)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│ AgentCore Gateway│ │  Knowledge Base │ │   Cognito Pool   │
│ BPMSGatewayAuth  │ │   RGU2WF39WW   │ │ us-east-1_mgbNY  │
│ (MCP + JWT Auth) │ │  (Retrieve API) │ │   QYnd           │
└────────┬─────────┘ └─────────────────┘ └──────────────────┘
         │
         ├── Lambda: consultar_estado_proceso
         ├── Lambda: identificar_tipo_documental
         └── Lambda: cerrar_tarea
```

---

## 2. Recursos Desplegados en AWS

### 2.1 AgentCore Runtime

| Campo | Valor |
|-------|-------|
| Nombre | MyAgent |
| ARN | `arn:aws:bedrock-agentcore:us-east-1:145405817802:runtime/ariafinabpmsagent_MyAgent-dalPn7CeJ3` |
| Estado | **READY** |
| Build | CodeZip |
| Runtime | Python 3.14 |
| Protocolo | HTTP |
| Red | PUBLIC |
| Entrypoint | `agent.py` |
| Framework | Strands Agents SDK v1.15+ |
| Modelo LLM | `us.amazon.nova-lite-v1:0` |
| URL Invocación | `https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A145405817802%3Aruntime%2Fariafinabpmsagent_MyAgent-dalPn7CeJ3/invocations` |

### 2.2 AgentCore Gateway (MCP)

| Campo | Valor |
|-------|-------|
| Nombre | BPMSGatewayAuth |
| ID | `ariafinabpmsagent-bpmsgatewayauth-zmbixotlun` |
| Protocolo | MCP |
| Authorizer | CUSTOM_JWT (Cognito) |
| Targets | 3 Lambda functions |

### 2.3 Lambda Functions

| Función | ARN | Runtime | Timeout | Tags |
|---------|-----|---------|---------|------|
| consultar_estado_proceso | `arn:aws:lambda:us-east-1:145405817802:function:consultar_estado_proceso` | Python 3.12 | 30s | proyecto=ariafina-bpms |
| identificar_tipo_documental | `arn:aws:lambda:us-east-1:145405817802:function:identificar_tipo_documental` | Python 3.12 | 30s | proyecto=ariafina-bpms |
| cerrar_tarea | `arn:aws:lambda:us-east-1:145405817802:function:cerrar_tarea` | Python 3.12 | 30s | proyecto=ariafina-bpms |

**Permisos:** Cada Lambda permite invocación desde `bedrock-agentcore.amazonaws.com`.

### 2.4 Bedrock Guardrail

| Campo | Valor |
|-------|-------|
| Nombre | ariafina-bpms-guardrail |
| ID | `n45cp9ulfxgk` |
| Versión | 1 |
| ARN | `arn:aws:bedrock:us-east-1:145405817802:guardrail/n45cp9ulfxgk` |

**Políticas configuradas:**
- Content filters: VIOLENCE, HATE, SEXUAL, INSULTS, MISCONDUCT (HIGH)
- PII: Anonimiza email/phone/name; Bloquea SSN, tarjetas, AWS keys
- Topics: Deniega off-topic, programación, consejos personales
- Profanity: Lista gestionada activa

### 2.5 Amazon Cognito

| Campo | Valor |
|-------|-------|
| User Pool ID | `us-east-1_mgbNyQYnd` |
| Pool Name | ariafina-bpms-users |
| App Client ID | `3alvujai8q7lv51on73p1da0i3` |
| Auth Flows | USER_PASSWORD_AUTH, REFRESH_TOKEN, SRP |

### 2.6 Knowledge Base

| Campo | Valor |
|-------|-------|
| ID | `RGU2WF39WW` |
| Región | us-east-1 |
| Integración | Directa vía boto3 (Retrieve API) |
| Top-K | 5 resultados |

### 2.7 IAM Roles

| Rol | Propósito |
|-----|-----------|
| `ariafina-bpms-lambda-role` | Execution role para las 3 Lambdas |
| `AgentCore-ariafinabpmsage-ApplicationAgentMyAgentRu-kvjFsrh94ZZF` | Runtime execution role (auto-generado por CDK) |

### 2.8 CloudFormation Stack

| Campo | Valor |
|-------|-------|
| Stack Name | `AgentCore-ariafinabpmsagent-default` |
| Estado | CREATE_COMPLETE |
| Recursos | 15 |

---

## 3. Herramientas del Agente

### 3.1 Tools Inline (Strands @tool)

| Herramienta | Función | Estado |
|-------------|---------|--------|
| `consultar_estado_proceso` | Consulta estado de instancia de proceso | Mock (TODO: integrar API BPMS) |
| `identificar_tipo_documental` | Clasifica documentos según TRD | Mock (TODO: integrar clasificador) |
| `cerrar_tarea` | Cierra tareas en flujos de trabajo | Mock (TODO: integrar motor workflow) |
| `consultar_base_conocimiento` | Retrieve semántico en KB de Bedrock | **Funcional** (conectado a RGU2WF39WW) |

### 3.2 MCP Client Externo

| Servidor | Endpoint | Protocolo |
|----------|----------|-----------|
| Exa AI | `https://mcp.exa.ai/mcp` | Streamable HTTP MCP 2025-11-25 |

---

## 4. Pruebas Realizadas

### 4.1 Pruebas de Lambdas (9/9 ✅)

```
Resultados locales: 9 pasaron / 0 fallaron / 9 total
Resultados AWS:     9 pasaron / 0 fallaron / 9 total
```

Casos cubiertos:
- Caso normal por cada Lambda
- Validación de parámetros obligatorios
- Validación de longitud mínima (descripción)
- Formato alternativo inputText (JSON string)

### 4.2 Prueba End-to-End (Runtime)

| Aspecto | Resultado |
|---------|-----------|
| Runtime inicia | ✅ |
| Credenciales IAM | ✅ (Found credentials from IAM Role: execution_role) |
| MCP Client conecta | ✅ (Exa AI session, protocol 2025-11-25) |
| System prompt enviado | ✅ |
| User message procesado | ✅ |
| Modelo responde | ❌ ThrottlingException (caso soporte #178345165800122) |

### 4.3 Validación de Configuración

```bash
$ agentcore validate
Valid
```

---

## 5. Decisiones Técnicas

| Decisión | Justificación |
|----------|---------------|
| Strands Agents SDK | Framework oficial AWS para agentes en Bedrock AgentCore |
| Amazon Nova Lite | Modelo propio AWS, sin suscripción Marketplace, cuota separada |
| Guardrails integrados en modelo | Protección nativa sin latencia extra (vs hook externo) |
| JWT Auth en Gateway | Seguridad zero-trust; solo usuarios autenticados acceden a tools |
| Lambdas separadas del runtime | Escalabilidad independiente, versionado por tool |
| camelCase en tool schemas | Formato requerido por CDK L3 construct (validado tras 3 iteraciones) |
| Logging estructurado JSON | Compatible con CloudWatch Insights para queries analíticos |

---

## 6. Estructura del Proyecto

```
ariafinabpmsagent/
├── agentcore/
│   ├── agentcore.json              ← Configuración principal
│   ├── aws-targets.json            ← Target: us-east-1:145405817802
│   ├── guardrails.json             ← Referencia local del guardrail
│   └── cdk/                        ← CDK L3 constructs
├── app/MyAgent/
│   ├── agent.py                    ← Entrypoint BPMS agent
│   ├── model/load.py               ← Modelo + Guardrail config
│   ├── mcp_client/client.py        ← MCP Exa AI
│   ├── memory/session.py           ← Session manager
│   ├── lambdas/
│   │   ├── consultar_estado_proceso.py
│   │   ├── identificar_tipo_documental.py
│   │   ├── cerrar_tarea.py
│   │   ├── test_lambdas.py         ← Suite de pruebas
│   │   └── schemas/                ← Tool schemas (camelCase)
│   ├── pyproject.toml
│   └── README.md
├── docs/
│   ├── EVIDENCIAS_DPI.md           ← Este documento
│   └── frontend/                   ← Demo UI
└── AGENTS.md
```

---

## 7. Próximos Pasos

| # | Tarea | Prioridad | Bloqueador |
|---|-------|-----------|-----------|
| 1 | Resolución throttling AWS | Alta | Caso #178345165800122 |
| 2 | Test end-to-end con respuesta real | Alta | Depende de 1 |
| 3 | Subir documentos a Knowledge Base | Media | Juan (H3) |
| 4 | Reactivar Memory con estrategias | Media | Post-validación |
| 5 | Integrar Lambdas con API BPMS real | Media | Endpoint backend |
| 6 | Frontend demo conectado | Baja | Post throttling |
| 7 | Evaluator + Online Eval | Baja | Post pruebas funcionales |

---

## 8. Comandos Útiles

```bash
# Estado del despliegue
agentcore status

# Invocar agente
agentcore invoke "¿Cuál es el estado del proceso PROC-2024-001?"

# Continuar sesión
agentcore invoke --session-id <session-id> "Siguiente pregunta"

# Ver logs del runtime
agentcore logs -n 50 --since 10m --json

# Probar Lambdas localmente
cd app/MyAgent/lambdas && python test_lambdas.py

# Probar Lambdas en AWS
cd app/MyAgent/lambdas && python test_lambdas.py --aws

# Validar configuración
agentcore validate

# Redesplegar
agentcore deploy
```

---

*Documento generado el 7 de julio de 2026. Proyecto Ariafina BPMS Agent — DPI.*
