---
applyTo: "**/plan_fases_*.md"
description: "Estandar para planes por fases de modulos (mismo marco de plan_fases_income)."
---

# Estandar de planes por fases

Cuando se cree o actualice un archivo `plan_fases_*.md`, seguir este formato:

## 1) Propósito

- Definir claramente alcance, objetivo operativo y valor del plan.

## 2) Criterios de ejecución

- Cambios por fase, sin mezclar entregables de fases futuras.
- Cierre de fase con validación tecnica minima (errores + smoke minimo).
- Tareas trazables con checklist (`[ ]` pendiente, `[x]` completada).
- Reglas globales parametrizables desde la aplicacion cuando sean del negocio.

## 2.1) Contexto operativo

- Incluir contexto pais/moneda/regimen cuando afecte reglas funcionales.

## 2.2) Decisiones cerradas

- Listar decisiones funcionales confirmadas y restricciones acordadas.
- Si algo no esta cerrado, declararlo como pendiente explicito.

## 3) Mapa de referencias internas

- Enumerar modelos, servicios, rutas, formularios/templates y migraciones impactadas.
- Referenciar rutas reales del proyecto para facilitar auditoria.

## 4) Referencias externas de criterio (si aplica)

- Normas, guias o fuentes funcionales usadas para definir reglas.

## 5) Estado por fase y objetivos concisos

- Una seccion por fase con: objetivo, entregables y criterios de aceptacion.
- Mantener fases pequenas, verificables y orientadas a valor.

## 6) Tablero de ejecucion activo

- Bloque inmediato y bloque siguiente con tareas operables por sprint.

## 7) Bitacora de avance

- Registrar fecha, cambio realizado y evidencia tecnica resumida.

## Reglas de redaccion

- Escribir en espanol tecnico claro.
- Priorizar consistencia con `plan_fases_income.md` en estructura y detalle.
- Evitar objetivos vagos; usar verbos accionables y medibles.
