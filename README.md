# PoC 3 — MCP Prompt Templates Server

Tercera PoC de la serie "Aprender MCP en profundidad". Server MCP que expone el
primitivo **Prompts**: plantillas parametrizadas que el usuario invoca a
propósito (a diferencia de Tools, que decide el modelo, o Resources, que
expone la aplicación).

Un Prompt no ejecuta nada ni devuelve data: arma una lista de mensajes
(`role` + `content`) lista para inyectar en la conversación.

## Estructura

```
.
├── server.py               # el MCP server — solo orquesta y registra
├── prompts/
│   ├── __init__.py
│   └── templates.py        # las 4 plantillas, como funciones puras
├── pyproject.toml
└── .gitignore
```

`templates.py` no depende del SDK `mcp`: recibe argumentos primitivos y
devuelve `dict`s con `role`/`content`. `server.py` es el único lugar que
importa `mcp`, define los tipos de cada argumento (con `Annotated` + `Field`
para que el cliente muestre buenas descripciones) y valida el resto.

## Instalación

Requiere Python 3.11+ y [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Correr el server directo (para probar por stdio)

```bash
uv run server.py
```

El server habla MCP sobre stdio y loguea a **stderr** (nunca a stdout, que
está reservado para el protocolo).

## Registrar en Claude Desktop

Editar `claude_desktop_config.json` (en Windows:
`%APPDATA%\Claude\claude_desktop_config.json`) y agregar:

```json
{
  "mcpServers": {
    "poc3-mcp-prompts": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\PoC\\MCP\\MPC-PoC-3-PromptTemplatesServer",
        "run",
        "server.py"
      ]
    }
  }
}
```

Reiniciar Claude Desktop. Los prompts registrados por un server MCP aparecen
como **slash commands** en el input del chat (escribiendo `/` se despliega el
picker), agrupados bajo el nombre del server. Cada argumento definido se
pide como campo en un formulario antes de invocar el prompt.

> Nota de esta sesión: la implementación se validó con un cliente MCP
> automatizado sobre stdio (`ClientSession` del SDK, ejercitando
> `prompts/list`, `prompts/get`, `resources/list` y los casos de error), no
> con Claude Desktop instalado en esta máquina. Verificá en tu propio Claude
> Desktop que el picker muestra los 4 prompts y actualizá esta sección con
> dónde te aparecieron exactamente (versión de la app, ubicación del menú).

## Los 4 prompts

### 1. `code_review` — argumentos requeridos + opcionales
- **Args**: `code` (requerido), `language` (opcional), `focus` (opcional:
  `security` | `performance` | `readability`).
- **Patrón**: argumentos opcionales con default y lógica condicional — sin
  `focus` da una revisión general, con `focus` cambia la instrucción.

### 2. `explain_modismo` — prompt de dominio, single-message
- **Args**: `modismo` (requerido), `contexto` (opcional).
- **Patrón**: el caso más simple — un prompt de dominio bien acotado, un solo
  mensaje `user`.

### 3. `debug_session` — multi-mensaje
- **Args**: `error_message` (requerido), `stack_trace` (opcional).
- **Devuelve 3 mensajes**: `user` (describe el error) → `assistant` (primer
  paso de diagnóstico ya establecido) → `user` (la pregunta concreta).
- **Patrón**: un Prompt no es un string, es una conversación pre-armada. Es
  el que más vale la pena inspeccionar en el cliente para confirmar que
  llegan como 3 mensajes con roles alternados y no como un solo bloque de
  texto concatenado.

### 4. `analyze_sheet` — composición con Resource
- **Args**: `sheet_uri` (requerido), `pregunta` (requerido).
- **Devuelve 2 mensajes**: el primero con un content block `type: resource`
  que embebe el contenido de la planilla; el segundo con la pregunta.
- **Patrón**: un Prompt puede traer data adentro, no solo texto. Acá se
  conecta con la PoC 2 (Resources).
- **Mock**: en vez de reusar `sheets_client.py` de la PoC 2, `server.py`
  registra un Resource mock (`sheet://ventas-demo`, un CSV de ventas
  hardcodeado) para no arrastrar la dependencia de Google Sheets — el punto
  de aprendizaje es la composición, no la API externa. `analyze_sheet` valida
  que el `sheet_uri` recibido sea ese mock; cualquier otro URI devuelve un
  error legible.

## Validación de argumentos

El SDK `mcp` valida los argumentos requeridos automáticamente a partir del
`Annotated`/`Field` de cada función registrada: si falta uno, `prompts/get`
devuelve un error MCP legible (`Missing required arguments: {...}`) en vez de
crashear el server. Se comprobó con el cliente automatizado.

## Qué aprendí

- Un **Prompt** no es "un template de texto": es una lista de mensajes con
  roles, y `debug_session` deja claro por qué eso importa — poder pre-armar
  un turno de `assistant` (un diagnóstico ya asumido) cambia el punto de
  partida de la conversación de una forma que una Tool no puede replicar.
- La frontera entre Prompt y Tool no es "qué hace" sino **quién decide
  invocarlo**. `analyze_sheet` podría ser una Tool que el modelo llama solo
  o un Prompt que el usuario dispara a propósito; elegirlo como Prompt tiene
  sentido cuando el usuario ya sabe qué quiere preguntar y no hace falta que
  el modelo decida si vale la pena leer la planilla.
- Un Prompt es mejor UX que una Tool cuando la intención es **repetible y
  la persona la reconoce de antemano** (revisar código con cierto foco,
  iniciar una sesión de debugging con un formato fijo): ahí un slash command
  con argumentos tipados vale más que confiar en que el modelo infiera la
  intención desde lenguaje natural.
- Separar `templates.py` (funciones puras, sin `mcp`) de `server.py`
  (registro, tipos, validación) hizo trivial testear las plantillas con un
  cliente MCP real sin nada mockeado del lado del protocolo — la lógica de
  negocio no sabe que existe MCP.

## Siguiente en la serie

**PoC 4** — Sampling-driven Agent: el server le pide al LLM del host que
genere, invirtiendo el flujo.
