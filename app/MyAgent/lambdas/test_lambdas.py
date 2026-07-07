"""
Script de prueba local para las Lambdas BPMS.
Simula invocaciones del Gateway sin pasar por Bedrock.

Uso:
    python test_lambdas.py          # Prueba local (importa directamente)
    python test_lambdas.py --aws    # Invoca las Lambdas desplegadas en AWS
"""

import json
import sys
import importlib
from datetime import datetime

# ---------------------------------------------------------------------------
# Colores para output
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def banner(msg):
    print(f"\n{CYAN}{'═' * 60}")
    print(f"  {msg}")
    print(f"{'═' * 60}{RESET}\n")


def result_ok(name, response):
    print(f"  {GREEN}✓ {name}{RESET}")
    body = response.get("response", {}).get("functionResponse", {}).get("responseBody", {}).get("TEXT", {}).get("body", "")
    if body:
        data = json.loads(body)
        for k, v in data.items():
            print(f"    {k}: {v}")
    print()


def result_fail(name, error):
    print(f"  {RED}✗ {name}: {error}{RESET}\n")


# ---------------------------------------------------------------------------
# Test cases — simula el formato que AgentCore Gateway envía a las Lambdas
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "name": "consultar_estado_proceso — caso normal",
        "module": "consultar_estado_proceso",
        "function_name": "consultar_estado_proceso",
        "event": {
            "parameters": [
                {"name": "proceso_id", "value": "PROC-2024-001"}
            ]
        },
        "expect_error": False,
    },
    {
        "name": "consultar_estado_proceso — sin proceso_id (debe fallar)",
        "module": "consultar_estado_proceso",
        "function_name": "consultar_estado_proceso",
        "event": {
            "parameters": []
        },
        "expect_error": True,
    },
    {
        "name": "identificar_tipo_documental — caso normal",
        "module": "identificar_tipo_documental",
        "function_name": "identificar_tipo_documental",
        "event": {
            "parameters": [
                {"name": "descripcion", "value": "Acta de comité directivo del 15 de julio"},
                {"name": "caso_id", "value": "CASO-2024-089"}
            ]
        },
        "expect_error": False,
    },
    {
        "name": "identificar_tipo_documental — descripción muy corta (debe fallar)",
        "module": "identificar_tipo_documental",
        "function_name": "identificar_tipo_documental",
        "event": {
            "parameters": [
                {"name": "descripcion", "value": "doc"}
            ]
        },
        "expect_error": True,
    },
    {
        "name": "identificar_tipo_documental — sin descripción (debe fallar)",
        "module": "identificar_tipo_documental",
        "function_name": "identificar_tipo_documental",
        "event": {
            "parameters": [
                {"name": "caso_id", "value": "CASO-001"}
            ]
        },
        "expect_error": True,
    },
    {
        "name": "cerrar_tarea — caso normal con comentario",
        "module": "cerrar_tarea",
        "function_name": "cerrar_tarea",
        "event": {
            "parameters": [
                {"name": "tarea_id", "value": "TASK-5012"},
                {"name": "comentario", "value": "Documentos verificados correctamente"}
            ]
        },
        "expect_error": False,
    },
    {
        "name": "cerrar_tarea — sin comentario (usa default)",
        "module": "cerrar_tarea",
        "function_name": "cerrar_tarea",
        "event": {
            "parameters": [
                {"name": "tarea_id", "value": "TASK-7788"}
            ]
        },
        "expect_error": False,
    },
    {
        "name": "cerrar_tarea — sin tarea_id (debe fallar)",
        "module": "cerrar_tarea",
        "function_name": "cerrar_tarea",
        "event": {
            "parameters": []
        },
        "expect_error": True,
    },
    {
        "name": "consultar_estado_proceso — formato inputText JSON",
        "module": "consultar_estado_proceso",
        "function_name": "consultar_estado_proceso",
        "event": {
            "inputText": "{\"proceso_id\": \"PROC-2024-555\"}"
        },
        "expect_error": False,
    },
]


# ---------------------------------------------------------------------------
# Ejecución local (importa los módulos Python directamente)
# ---------------------------------------------------------------------------
def run_local_tests():
    banner("Pruebas locales — importando handlers directamente")
    passed = 0
    failed = 0

    for tc in TEST_CASES:
        try:
            mod = importlib.import_module(tc["module"])
            response = mod.handler(tc["event"], None)

            body_str = (
                response.get("response", {})
                .get("functionResponse", {})
                .get("responseBody", {})
                .get("TEXT", {})
                .get("body", "{}")
            )
            body = json.loads(body_str)
            has_error = "error" in body

            if tc["expect_error"] and has_error:
                result_ok(tc["name"], response)
                print(f"    {YELLOW}(Error esperado: {body['error']}){RESET}\n")
                passed += 1
            elif not tc["expect_error"] and not has_error:
                result_ok(tc["name"], response)
                passed += 1
            elif tc["expect_error"] and not has_error:
                result_fail(tc["name"], "Se esperaba error pero no se obtuvo")
                failed += 1
            else:
                result_fail(tc["name"], f"Error inesperado: {body.get('error')}")
                failed += 1

        except Exception as e:
            result_fail(tc["name"], str(e))
            failed += 1

    # Summary
    total = passed + failed
    print(f"\n{'═' * 60}")
    print(f"  Resultados: {GREEN}{passed} pasaron{RESET} / {RED}{failed} fallaron{RESET} / {total} total")
    print(f"{'═' * 60}\n")
    return failed == 0


# ---------------------------------------------------------------------------
# Ejecución remota (invoca Lambdas en AWS)
# ---------------------------------------------------------------------------
def run_aws_tests():
    import boto3

    banner("Pruebas AWS — invocando Lambdas desplegadas en us-east-1")
    client = boto3.client("lambda", region_name="us-east-1")
    passed = 0
    failed = 0

    for tc in TEST_CASES:
        function_name = tc["function_name"]
        try:
            response = client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(tc["event"]),
            )
            payload = json.loads(response["Payload"].read())

            if response.get("FunctionError"):
                result_fail(tc["name"], f"Lambda error: {payload}")
                failed += 1
                continue

            body_str = (
                payload.get("response", {})
                .get("functionResponse", {})
                .get("responseBody", {})
                .get("TEXT", {})
                .get("body", "{}")
            )
            body = json.loads(body_str)
            has_error = "error" in body

            if tc["expect_error"] and has_error:
                result_ok(tc["name"], payload)
                print(f"    {YELLOW}(Error esperado: {body['error']}){RESET}\n")
                passed += 1
            elif not tc["expect_error"] and not has_error:
                result_ok(tc["name"], payload)
                passed += 1
            elif tc["expect_error"] and not has_error:
                result_fail(tc["name"], "Se esperaba error pero no se obtuvo")
                failed += 1
            else:
                result_fail(tc["name"], f"Error inesperado: {body.get('error')}")
                failed += 1

        except Exception as e:
            result_fail(tc["name"], str(e))
            failed += 1

    total = passed + failed
    print(f"\n{'═' * 60}")
    print(f"  Resultados AWS: {GREEN}{passed} pasaron{RESET} / {RED}{failed} fallaron{RESET} / {total} total")
    print(f"{'═' * 60}\n")
    return failed == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"\n{CYAN}Ariafina BPMS — Test Suite Lambda{RESET}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if "--aws" in sys.argv:
        success = run_aws_tests()
    else:
        success = run_local_tests()

    sys.exit(0 if success else 1)
