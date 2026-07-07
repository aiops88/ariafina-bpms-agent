# Frontend Demo — Ariafina BPMS Agent

## Uso rápido

### Modo Demo (sin backend)
Abre `index.html` directamente en el navegador. Descomentar la última línea del JS:
```javascript
showChat(); // Auto-inicia sin login
```
Las respuestas son simuladas localmente — ideal para presentaciones del DPI.

### Modo Producción (con Cognito + AgentCore)
1. Crear un usuario en Cognito:
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_mgbNyQYnd \
  --username usuario@ariafina.com \
  --temporary-password TempPass123! \
  --region us-east-1
```

2. Confirmar usuario (establecer contraseña permanente):
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_mgbNyQYnd \
  --username usuario@ariafina.com \
  --password MiPassword2026! \
  --permanent \
  --region us-east-1
```

3. Abrir `index.html` y hacer login con las credenciales.

## Configuración

Las variables están al inicio del bloque `<script>`:
```javascript
const CONFIG = {
    COGNITO_REGION: 'us-east-1',
    USER_POOL_ID: 'us-east-1_mgbNyQYnd',
    CLIENT_ID: '3alvujai8q7lv51on73p1da0i3',
    AGENT_ENDPOINT: 'https://bedrock-agentcore.us-east-1.amazonaws.com/...',
};
```

## Funcionalidades

- Login con Cognito (USER_PASSWORD_AUTH)
- Chat streaming con el agente
- Botones de acción rápida
- Respuestas formateadas (markdown-like)
- Modo demo con respuestas simuladas
- Responsive (móvil + desktop)
