# Agentes y base de conocimiento

Este repositorio contiene dos flujos de agente distintos. Comparten archivos
de contexto, pero no son el mismo agente ni se ejecutan juntos.

## 1. Agente de desarrollo en VS Code

El agente **Conciliacion y auditoria contable** se selecciona manualmente en
Copilot Chat, en el selector **Agents**. No lo inicia `src/orchestrator.py`.
Usa el modelo y la autenticacion que tenga configurados Copilot en VS Code;
`OPENAI_API_KEY`, Ollama y la configuracion `.env` de la aplicacion no controlan
ese chat.

Su contexto de proyecto se compone de:

1. [`.github/copilot-instructions.md`](../.github/copilot-instructions.md):
   instrucciones generales de Copilot para este repositorio.
2. [`.github/agents/conciliacion-auditoria.agent.md`](../.github/agents/conciliacion-auditoria.agent.md):
   rol y comportamiento del agente personalizado.
3. [`.github/skills/reconciliation-engineering/SKILL.md`](../.github/skills/reconciliation-engineering/SKILL.md):
   skill de VS Code descubierta en `.github/skills/` y cargada bajo demanda
   cuando es pertinente. El agente la instruye a cargar para tareas financieras.
4. [`CONTEXT.md`](../CONTEXT.md), codigo, pruebas, fixtures y documentos que el
   agente consulte al trabajar.

La skill enlaza las reglas runtime para que el agente de desarrollo las pueda
consultar, pero eso no las convierte en skills de Copilot. Al pedirle al agente
que lea archivos del workspace, su contenido puede formar parte del contexto
enviado al servicio de Copilot conforme a la configuracion y politicas de esa
cuenta. La proteccion `ALLOW_REMOTE_ENDPOINT` de la aplicacion no gobierna el
chat de Copilot.

## 2. Auditor de excepciones de la aplicacion

Este flujo es el programa Python ejecutado manualmente:

```bash
python src/orchestrator.py
```

Secuencia actual:

1. Lee `.env` y carga tres reportes JSON desde `data/` (o desde
   `RECONCILIATION_DATA_DIR`): banco, pasarela y libro mayor.
2. Valida identificadores, importes, monedas y marcas de tiempo, y construye
   DataFrames en memoria.
3. Ejecuta las reglas deterministas implementadas en
   [`src/orchestrator.py`](../src/orchestrator.py): screening AML ilustrativo,
   cruce banco-libro mayor y cruce de liquidaciones banco-pasarela.
4. Si quedan excepciones no resueltas y no aisladas, envia esas excepciones al
   endpoint OpenAI-compatible configurado, en lotes acotados. Por defecto el
   endpoint es Ollama local en `localhost`; un endpoint remoto se rechaza salvo
   que `ALLOW_REMOTE_ENDPOINT=true` lo habilite explicitamente.
5. Valida el JSON del modelo y sus referencias contra los registros de origen,
   combina sus excepciones con los resultados deterministas y guarda un reporte
   JSON en `output/` (o en `AUDIT_OUTPUT_DIR`).

Si no quedan excepciones que necesiten interpretacion, no se requiere llamar al
modelo. El modelo no calcula conciliaciones deterministas ni reglas AML. Para
cada solicitud al endpoint se construye contexto textual leyendo estos
documentos:

- [`agent_config/system_prompt.md`](../agent_config/system_prompt.md): rol del
  auditor runtime y contrato de salida JSON.
- [`agent_config/skills/reconciliation_analysis.md`](../agent_config/skills/reconciliation_analysis.md):
  esquema de entrada, límites de evidencia por lote y guía de análisis de
  excepciones.
- [`agent_config/skills/fuzzy_matching.md`](../agent_config/skills/fuzzy_matching.md):
  referencia de comisiones y liquidaciones.
- [`agent_config/skills/aml_fraud_detection.md`](../agent_config/skills/aml_fraud_detection.md):
  explicacion de las alertas AML calculadas por la aplicacion.
- [`docs/compliance_aml_rules.md`](compliance_aml_rules.md): reglas AML
  ilustrativas usadas por el codigo y documentacion.

`src/orchestrator.py` concatena estos textos en memoria como mensaje de sistema;
no hay base de datos vectorial, busqueda RAG, entrenamiento ni una base de
conocimiento institucional conectada. Los reportes fuente se envian como
mensaje separado solo cuando hay excepciones. El envio a un endpoint remoto
puede sacar esos registros de la maquina; no se deben usar datos financieros
reales sin aprobacion y controles adecuados. Ollama local tampoco garantiza por
si solo que no haya persistencia en logs.

## Fuentes de verdad y limites

- El **codigo y las pruebas** determinan el comportamiento ejecutable actual.
- `CONTEXT.md` resume ese comportamiento y sus limitaciones; no implementa
  reglas por si mismo.
- Los fixtures en `data/` son sinteticos. No definen formatos oficiales de
  bancos, pasarelas, libros mayores o bancos centrales.
- Las instrucciones AML son ejemplos del PoC, no politica regulatoria
  aprobada.
- El objetivo del producto incluye extractos del banco central, pero todavia
  no se especifican institucion, formato externo, reglas contables aprobadas,
  volumen objetivo, controles productivos ni criterios completos de aceptacion.
- No existe interfaz de analista ni gestion de casos implementada. El reporte
  JSON requiere revision posterior.

No se deben confundir los prompts runtime de `agent_config/` con la
configuracion de Copilot en `.github/`, ni describir el PoC como sistema de
produccion o de procesamiento masivo.
