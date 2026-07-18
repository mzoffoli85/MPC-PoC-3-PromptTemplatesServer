"""Plantillas de Prompts, como funciones puras.

Cada función recibe argumentos primitivos y devuelve una lista de mensajes
(dicts con "role" y "content") lista para que server.py la registre como
Prompt de MCP. No hacen I/O ni dependen del SDK `mcp`: solo arman texto.
"""

from __future__ import annotations

from typing import Any

Message = dict[str, Any]

FOCUS_INSTRUCTIONS: dict[str, str] = {
    "security": (
        "Enfocate en seguridad: identificá vulnerabilidades (inyección, validación de "
        "entrada, manejo de secretos, condiciones de carrera, permisos) y priorizá los "
        "hallazgos por severidad."
    ),
    "performance": (
        "Enfocate en performance: identificá complejidad algorítmica innecesaria, "
        "operaciones costosas dentro de loops, N+1 queries, uso de memoria y "
        "oportunidades de caching."
    ),
    "readability": (
        "Enfocate en legibilidad y mantenibilidad: naming, tamaño de funciones, "
        "duplicación, y qué tan fácil sería para otra persona entender este código "
        "sin contexto adicional."
    ),
}

DEFAULT_FOCUS_INSTRUCTION = (
    "Hacé una revisión general: correctitud, casos borde no manejados, y cualquier "
    "problema de seguridad, performance o legibilidad que te parezca relevante."
)


def code_review(
    code: str,
    language: str | None = None,
    focus: str | None = None,
) -> list[Message]:
    """Revisión de código con foco opcional (security | performance | readability)."""
    lang_note = f" en {language}" if language else " (detectá el lenguaje a partir del código)"
    instruction = FOCUS_INSTRUCTIONS.get((focus or "").strip().lower(), DEFAULT_FOCUS_INSTRUCTION)

    text = (
        f"Revisá el siguiente código{lang_note}.\n\n"
        f"{instruction}\n\n"
        f"```\n{code}\n```"
    )
    return [{"role": "user", "content": text}]


def explain_modismo(modismo: str, contexto: str | None = None) -> list[Message]:
    """Explicación de un modismo chileno para un hablante no nativo."""
    contexto_line = f"\n\nContexto en el que se escuchó: \"{contexto}\"" if contexto else ""

    text = (
        f'Explicame el modismo chileno "{modismo}" para alguien que no es hablante '
        f"nativo de español chileno.{contexto_line}\n\n"
        "Incluí:\n"
        "- Origen o etimología, si se conoce\n"
        "- Registro (formal / informal / vulgar / regional)\n"
        "- Un ejemplo de uso en una oración\n"
        "- Un equivalente aproximado en español neutro o inglés, si aplica"
    )
    return [{"role": "user", "content": text}]


def debug_session(error_message: str, stack_trace: str | None = None) -> list[Message]:
    """Arma un intercambio inicial de depuración (user -> assistant -> user)."""
    problem = f"Me está saltando este error:\n\n{error_message}"
    if stack_trace:
        problem += f"\n\nStack trace:\n{stack_trace}"

    diagnostic = (
        "Antes de sacar conclusiones, arranquemos por lo básico: ¿en qué línea exacta "
        "ocurre, qué tipo de excepción es, y qué la dispara -un input inesperado, un "
        "estado nulo, una dependencia externa que falló? Contame también qué esperabas "
        "que pasara en ese punto del código."
    )

    question = (
        "Con esa información: ¿cuál es la causa raíz más probable y qué cambios "
        "concretos harías para solucionarlo?"
    )

    return [
        {"role": "user", "content": problem},
        {"role": "assistant", "content": diagnostic},
        {"role": "user", "content": question},
    ]


def analyze_sheet(
    sheet_uri: str,
    pregunta: str,
    resource_text: str,
    resource_mime_type: str = "text/csv",
) -> list[Message]:
    """Embebe el contenido de un Resource y agrega la pregunta del usuario."""
    return [
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": sheet_uri,
                    "mimeType": resource_mime_type,
                    "text": resource_text,
                },
            },
        },
        {
            "role": "user",
            "content": f"Con los datos de la planilla de arriba: {pregunta}",
        },
    ]
