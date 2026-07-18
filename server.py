"""MCP server que expone 4 Prompts parametrizados (PoC 3).

El server solo orquesta: registra los prompts y delega el armado de los
mensajes a `prompts/templates.py`. No ejecuta efectos secundarios.
"""

from __future__ import annotations

import logging
import sys
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from prompts import templates

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("poc3-mcp-prompts")

mcp = FastMCP("poc3-mcp-prompts")

# --- Resource mock, usado por analyze_sheet para demostrar composición ---
# (En una PoC real esto sería sheets_client.py de la PoC 2. Acá se mockea
# un CSV local para no arrastrar la dependencia de Google.)

MOCK_SHEET_URI = "sheet://ventas-demo"
MOCK_SHEET_MIME_TYPE = "text/csv"

MOCK_SHEET_CSV = (
    "producto,mes,unidades_vendidas,ingreso_usd\n"
    "Teclado mecanico,enero,120,3600\n"
    "Mouse inalambrico,enero,340,5100\n"
    "Monitor 27 pulgadas,enero,45,13500\n"
    "Teclado mecanico,febrero,98,2940\n"
    "Mouse inalambrico,febrero,410,6150\n"
    "Monitor 27 pulgadas,febrero,52,15600\n"
)


@mcp.resource(
    MOCK_SHEET_URI,
    name="ventas_demo",
    title="Ventas demo (mock)",
    description="CSV mock de ventas mensuales, usado como Resource embebible en analyze_sheet.",
    mime_type=MOCK_SHEET_MIME_TYPE,
)
def get_ventas_demo() -> str:
    logger.info("Sirviendo resource mock %s", MOCK_SHEET_URI)
    return MOCK_SHEET_CSV


# --- Prompts ---


@mcp.prompt(
    name="code_review",
    description=(
        "Genera instrucciones de revisión de código, con foco opcional en "
        "seguridad, performance o legibilidad."
    ),
)
def code_review(
    code: Annotated[str, Field(description="El código fuente a revisar.")],
    language: Annotated[
        str | None,
        Field(
            description=(
                "Lenguaje del código (ej: python, javascript). Si se omite, se le "
                "pide al modelo que lo detecte."
            )
        ),
    ] = None,
    focus: Annotated[
        Literal["security", "performance", "readability"] | None,
        Field(
            description=(
                "Foco de la revisión: security, performance o readability. "
                "Si se omite, es una revisión general."
            )
        ),
    ] = None,
) -> list[dict]:
    logger.info("code_review invocado (language=%s, focus=%s)", language, focus)
    return templates.code_review(code=code, language=language, focus=focus)


@mcp.prompt(
    name="explain_modismo",
    description="Explica un modismo chileno a un hablante no nativo: origen, registro y ejemplo de uso.",
)
def explain_modismo(
    modismo: Annotated[
        str, Field(description="El modismo chileno a explicar (ej: 'al tiro', 'cachai').")
    ],
    contexto: Annotated[
        str | None,
        Field(
            description=(
                "Frase u oración donde se escuchó el modismo, para ajustar la "
                "explicación al contexto."
            )
        ),
    ] = None,
) -> list[dict]:
    logger.info("explain_modismo invocado (modismo=%s)", modismo)
    return templates.explain_modismo(modismo=modismo, contexto=contexto)


@mcp.prompt(
    name="debug_session",
    description=(
        "Arma una conversación inicial de depuración: describe el error, propone un "
        "primer paso de diagnóstico y pregunta por la causa raíz. Devuelve múltiples "
        "mensajes con roles alternados."
    ),
)
def debug_session(
    error_message: Annotated[str, Field(description="El mensaje de error tal como aparece.")],
    stack_trace: Annotated[
        str | None, Field(description="Stack trace completo, si está disponible.")
    ] = None,
) -> list[dict]:
    logger.info("debug_session invocado (con stack_trace=%s)", stack_trace is not None)
    return templates.debug_session(error_message=error_message, stack_trace=stack_trace)


@mcp.prompt(
    name="analyze_sheet",
    description=(
        "Embebe el contenido de un Resource (una planilla) dentro del prompt y agrega "
        "una pregunta puntual sobre esos datos."
    ),
)
def analyze_sheet(
    sheet_uri: Annotated[
        str,
        Field(
            description=(
                f"URI del Resource a analizar. En esta PoC solo existe el mock "
                f"'{MOCK_SHEET_URI}'."
            )
        ),
    ],
    pregunta: Annotated[
        str, Field(description="La pregunta concreta a responder sobre los datos de la planilla.")
    ],
) -> list[dict]:
    logger.info("analyze_sheet invocado (sheet_uri=%s)", sheet_uri)
    if sheet_uri != MOCK_SHEET_URI:
        raise ValueError(
            f"Resource desconocido: '{sheet_uri}'. Esta PoC solo mockea '{MOCK_SHEET_URI}'."
        )
    return templates.analyze_sheet(
        sheet_uri=sheet_uri,
        pregunta=pregunta,
        resource_text=get_ventas_demo(),
        resource_mime_type=MOCK_SHEET_MIME_TYPE,
    )


if __name__ == "__main__":
    logger.info("Iniciando poc3-mcp-prompts (stdio)")
    mcp.run()
