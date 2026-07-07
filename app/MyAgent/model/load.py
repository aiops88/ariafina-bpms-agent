from strands.models.bedrock import BedrockModel


# ---------------------------------------------------------------------------
# Guardrail configuration
# ---------------------------------------------------------------------------
GUARDRAIL_ID = "n45cp9ulfxgk"
GUARDRAIL_VERSION = "1"


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials with guardrails enabled."""
    return BedrockModel(
        model_id="us.amazon.nova-lite-v1:0",
        guardrail_id=GUARDRAIL_ID,
        guardrail_version=GUARDRAIL_VERSION,
        guardrail_trace="enabled",
        guardrail_redact_input=True,
        guardrail_redact_input_message="[Contenido bloqueado por políticas de seguridad]",
    )
