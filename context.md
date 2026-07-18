# PoC 3 — MCP Prompt Templates Server

> Inicializador para Claude Code. Tercera PoC de la serie "Aprender MCP en profundidad".
> Objetivo: dominar el primitivo **Prompts** — plantillas parametrizadas reutilizables.

---

## Contexto para Claude Code

Soy Marco. Ya terminé la PoC 1 (Echo Server / Tools sobre stdio) y la PoC 2 (Resource Provider sobre Google Sheets). Manejo la arquitectura MCP, el handshake, Tools y Resources.

**No expliques teoría de MCP a menos que la pida.** Esta PoC es sobre el tercer primitivo del server: **Prompts**.

---

## Objetivo de esta PoC

Construir un MCP server que exponga **prompts parametrizados** que el usuario invoca explícitamente. El server no ejecuta nada ni devuelve data: devuelve **mensajes pre-armados** que se inyectan en la conversación.

### Distinción clave a interiorizar

Los tres primitivos del server, por quién los controla:

| Primitivo | Controlado por | Qué es |
|-----------|----------------|--------|
| **Tools** | El modelo | Funciones que el LLM decide invocar |
| **Resources** | La aplicación | Data que el cliente expone como contexto |
| **Prompts** | El usuario | Plantillas que la persona elige a propósito |

Un Prompt devuelve una lista de mensajes (`role` + `content`) lista para inyectar. Puede componer texto, e **incluir Resources embebidos** — ahí está lo interesante.

### Puntos de aprendizaje que cubre
- Primitivo **Prompts**: definición, argumentos, `prompts/list`, `prompts/get`
- Argumentos requeridos vs opcionales
- Prompts multi-mensaje (armar un intercambio, no solo un bloque de texto)
- **Composición**: embeber un Resource dentro de un Prompt
- Cómo se exponen en el cliente (slash commands en Claude Desktop)

---

## Stack

- **Python 3.11+**
- SDK oficial `mcp`
- Transporte **stdio**
- `uv`
- Sin dependencias externas (salvo el prompt que compone Resources — ver más abajo)

---

## Estructura del proyecto

​```
poc3-mcp-prompts/
├── README.md
├── pyproject.toml
├── server.py               # el MCP server
├── prompts/
│   ├── __init__.py
│   └── templates.py        # las plantillas, separadas de la lógica del server
├── .gitignore
​```

---

## Especificación de los Prompts

Cuatro prompts, cada uno ejercitando un patrón distinto:

### 1. `code_review` — argumentos requeridos + opcionales
- **Args**: `code` (requerido), `language` (opcional, default autodetect), `focus` (opcional: `security` | `performance` | `readability`)
- **Devuelve**: un mensaje `user` con instrucciones de review adaptadas al `focus`.
- **Patrón**: manejo de argumentos opcionales con defaults y lógica condicional.

### 2. `explain_modismo` — prompt de dominio, single-message
- **Args**: `modismo` (requerido), `contexto` (opcional)
- **Devuelve**: instrucción para explicar un modismo chileno a un hablante no nativo — origen, registro, ejemplo de uso.
- **Patrón**: el caso más simple. Prompt de dominio bien acotado.

### 3. `debug_session` — multi-mensaje
- **Args**: `error_message` (requerido), `stack_trace` (opcional)
- **Devuelve**: **varios mensajes** que arman un intercambio inicial:
  - `user`: descripción del problema
  - `assistant`: un primer paso de diagnóstico ya establecido
  - `user`: la pregunta concreta
- **Patrón**: un Prompt no es un string — es una conversación pre-armada. Este es el patrón que más se subestima.

### 4. `analyze_sheet` — composición con Resource
- **Args**: `sheet_uri` (requerido), `pregunta` (requerido)
- **Devuelve**: un mensaje que **embebe el contenido de un Resource** (tipo `resource` en el content block) más la pregunta del usuario.
- **Patrón**: acá se conecta con la PoC 2. Un Prompt puede traer data adentro, no solo texto.

> Para el prompt 4: podés reusar el `sheets_client.py` de la PoC 2, o mockear un resource local (un CSV de ejemplo) si no querés arrastrar la dependencia de Google. **Mockear está bien** — el punto de aprendizaje es la composición, no la API de Sheets.

---

## Requisitos de implementación

1. Plantillas en `prompts/templates.py`, separadas del registro en `server.py`. El server solo orquesta.
2. Cada prompt con **descripción clara** y **argumentos bien descritos** — el cliente los muestra al usuario en el picker. Una descripción mala hace un prompt inusable.
3. Validación de argumentos requeridos: si falta uno, error MCP legible.
4. Logging a **stderr**.
5. Los prompts no deben ejecutar efectos secundarios. Solo arman mensajes.

---

## Pasos de trabajo (en orden)

1. **Scaffolding**: estructura, `pyproject.toml` con `mcp`, `.gitignore`.
2. **prompts/templates.py**: las 4 plantillas como funciones puras que reciben args y devuelven mensajes.
3. **server.py**: registrar los 4 prompts.
4. **README.md**: cómo registrar en Claude Desktop, cómo invocar cada prompt desde el cliente, y qué patrón ejercita cada uno.
5. Probar en Claude Desktop: aparecen los 4, se invocan con args, el multi-mensaje se inyecta bien.

---

## Criterios de aceptación (definición de "listo")

- [ ] `prompts/list` muestra los 4 prompts con sus descripciones y argumentos.
- [ ] `code_review` funciona con y sin los args opcionales.
- [ ] `explain_modismo` devuelve una instrucción bien formada.
- [ ] `debug_session` inyecta **múltiples mensajes** con roles alternados — verificable en el cliente.
- [ ] `analyze_sheet` embebe contenido de un resource dentro del prompt.
- [ ] Argumento requerido faltante → error legible, no crash.
- [ ] Los prompts son accesibles desde el cliente (slash command / picker).
- [ ] README permite levantar todo desde cero.

---

## Notas

- **Verificá la firma actual del SDK `mcp`** para registrar prompts y para el content block de tipo `resource` antes de codear.
- En Claude Desktop los prompts MCP aparecen como slash commands o en el menú de adjuntos según versión. Documentá en el README dónde te aparecieron a vos.
- El prompt `debug_session` es el más valioso didácticamente: comprobá en el cliente que efectivamente se inyectan los 3 mensajes y no uno concatenado.
- Al terminar, apartado "Qué aprendí" (3-4 bullets), con foco en **cuándo un Prompt es mejor UX que una Tool** — hay overlap y elegir bien es la gracia.

---

## Siguiente en la serie

**PoC 4** — Sampling-driven Agent: el server le pide al LLM del host que genere, invirtiendo el flujo.