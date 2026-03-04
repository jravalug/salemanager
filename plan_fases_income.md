# Plan maestro de implementación por fases (Income)

Fecha de actualización: 2026-03-04
Estado: vigente

## 1) Propósito

Este archivo es la fuente de control para ejecutar y auditar el plan de fases acordado:

1. Evento único de ingreso.
2. Doble vista contable (financiera/fiscal).
3. Pendientes por acreditar (transitorio bancario).
4. Documento mínimo de cobro.
5. Reportes esenciales.
6. Integración con el sistema actual.

## 2) Criterios de ejecución

- Cambios por fase, sin mezclar entregables de fases futuras.
- Cada fase cierra con validación técnica (errores + smoke mínimo).
- Toda tarea debe quedar marcada en este archivo (`[ ]` pendiente / `[x]` completada).
- Las reglas globales del sistema deben poder administrarse desde la aplicación (no solo por variable de entorno).

## 2.1) Contexto país (Cuba)

Este plan se ejecuta bajo contexto operativo y fiscal de Cuba. La implementación debe respetar:

- Segmentación de contribuyentes usada en el sistema (`TCP`, `MIPYME`).
- Régimen contable gestionado por cliente (`fiscal` / `financiera`).
- Aplicación de régimen por cliente (o condición especial), no por comparación entre regímenes.
- Parámetros configurables de transición anual de régimen.
- Operación monetaria principal en `CUP` y formato local `es_CU`.

## 2.2) Decisiones cerradas (acuerdo funcional)

- El sistema registra **solo el libro del régimen activo** del cliente.
- La “condición especial” no es override manual por operación: se determina por regla anual existente:
  - Cliente `TCP` en fiscal que supera `500000 CUP` de ingresos brutos anuales pasa a financiera al año siguiente.
- El estado `pending -> collected` se cierra por **conciliación manual**.
- El comprobante mínimo de cobro en Fase 4 será el **número de operación bancaria** (con fecha y banco).
- El umbral de `500000 CUP` debe convertirse en **configuración global editable en UI**.

Referencias internas activas para este contexto:

- `app/models/client.py`
- `app/models/business.py`
- `app/services/client_accounting_service.py`
- `app/services/business_rules_service.py`
- `app/filters.py`
- `config.py`

---

## 3) Mapa de referencias internas (inventario útil)

### 3.1 Modelos y persistencia

- `app/models/income_event.py` → entidad base de evento de ingreso (F1, F2, F3).
- `app/models/daily_income.py` → base fiscal temporal y resúmenes diarios (F5, F6).
- `app/models/sale.py` → documento operacional actual usado por capa `income` (F6).
- `app/models/business.py` → configuración de modo de ingreso por negocio.
- `migrations/versions/ab42c3d9e1f0_add_income_event_model.py` → migración F1.

### 3.2 Servicios de negocio

- `app/services/income_management_service.py` → punto principal de creación/actualización de ingresos y evento.
- `app/services/business_rules_service.py` → generación de resumen diario (`SOURCE_SALES_SUMMARY`).
- `app/services/income_report_service.py` → base de reportes para extensión F5.
- `app/services/client_service.py` → agregados mensuales que hoy usan `DailyIncome`.
- `app/services/client_accounting_service.py` → transición anual fiscal/financiera por umbral.

### 3.5 Configuración global

- `config.py` → valores globales actuales vía entorno (`ACCOUNTING_FISCAL_THRESHOLD`, etc.).
- Pendiente: mover configuraciones críticas a persistencia editable desde la aplicación.

### 3.3 Rutas y API

- `app/routes/income.py` → flujo web de ingresos.
- `app/routes/api/income.py` → exposición API de ingresos.
- `app/routes/reports.py` → endpoints actuales de reportes (base para F5).

### 3.4 Formularios y templates

- `app/forms/income.py` y `app/forms/business.py` → entradas de datos operativos.
- `app/templates/income/*` y `app/templates/report/*` → interfaz y reportes actuales.

---

## 4) Referencias externas de criterio (funcionales)

Estas referencias son guía conceptual para reglas de negocio y nomenclatura contable:

- Devengo (base conceptual de reconocimiento financiero):
  - https://es.wikipedia.org/wiki/Devengo

Pendiente para validación funcional en siguiente iteración (según jurisdicción/criterio fiscal aplicable al negocio):

- [ ] Confirmar fuente normativa fiscal local para reconocimiento por cobro (base caja).
- [ ] Confirmar criterios mínimos de conciliación bancaria aplicables al flujo “pendiente -> cobrado”.
- [ ] Incorporar referencia oficial aplicable de Cuba (ONAT/Gaceta) para cierre de criterios de F2-F5.

Avance de investigación:

- Se confirmó acceso a Gaceta Oficial como fuente válida de publicidad normativa:
  - https://www.gacetaoficial.gob.cu/es
- ONAT y sitios bancarios no devolvieron contenido extraíble con la herramienta en esta sesión; mantener pendiente su validación directa por normativa/documentación interna del negocio.

---

## 5) Estado por fase y objetivos concisos

## Fase 1 — Evento único de ingreso

Objetivo: consolidar `income_event` como origen normalizado de ingreso.

### Entregables
- [x] Modelo `IncomeEvent` completo.
- [x] Restricciones de valores válidos.
- [x] Migración y tabla creadas.
- [x] Escritura de evento en flujo manual diario.

### Evidencia
- `app/models/income_event.py`
- `migrations/versions/ab42c3d9e1f0_add_income_event_model.py`
- `app/services/income_management_service.py`

## Fase 2 — Doble vista contable

Objetivo: registrar en dos libros (financiero y fiscal) desde cada `income_event`.

Nota de negocio: ambos libros existen en la plataforma, pero se registra únicamente el libro del régimen activo del cliente.

Regla funcional:
- Cobro inmediato: financiero y fiscal en `event_date`.
- Transferencia pendiente: financiero en `event_date`; fiscal en `collected_date`.

### Entregables
- [ ] Modelo `FinancialLedgerEntry`.
- [ ] Modelo `FiscalIncomeEntry`.
- [ ] Migración de ambas tablas con índices por negocio/fecha.
- [ ] Servicio de posting idempotente desde `IncomeEvent`.
- [ ] Regla de selección de libro por régimen activo del cliente.
- [ ] Prueba de regla inmediato vs pendiente.

### Dependencia previa (F0)

- [x] Parametrizar umbral global de transición de régimen (`500000 CUP`) en almacenamiento editable por UI.
- [x] Exponer pantalla/endpoint de administración de configuraciones globales.

### Objetivos de cambio concisos
1. Persistencia de libro financiero.
2. Persistencia de libro fiscal.
3. Motor de posting por evento.
4. Garantía de no duplicidad de asientos.

## Fase 3 — Pendientes por acreditar

Objetivo: gestionar transitorio bancario y conciliación de cobros pendientes.

### Entregables
- [ ] Consulta de pendientes por acreditar.
- [ ] Operación de transición `pending -> collected`.
- [ ] Registro de conciliación manual del cobro (usuario + fecha + referencia bancaria).
- [ ] Actualización automática de impacto fiscal al conciliar.

## Fase 4 — Documento mínimo de cobro

Objetivo: cerrar pendientes mediante comprobante/confirmación de cobro.

### Entregables
- [ ] Entidad `CollectionReceipt` (o equivalente mínima).
- [ ] Relación con `IncomeEvent`.
- [ ] Flujo de confirmación y cierre de pendiente por número de operación bancaria.

## Fase 5 — Reportes esenciales

Objetivo: cubrir visibilidad del régimen aplicable y sus obligaciones de reporte.

### Entregables
- [ ] Libro de ingresos para clientes en régimen financiero (fecha de operación).
- [ ] Libro de ingresos para clientes en régimen fiscal (fecha de cobro).
- [ ] Pendientes por acreditar con aging simple.
- [ ] Reporte de cumplimiento por régimen (fiscal o financiera) por período.

### Criterios de aceptación
- [ ] Filtro por negocio y rango de fechas.
- [ ] Filtro por régimen contable aplicable del cliente.
- [ ] Totales consistentes con libros.
- [ ] Exportación básica alineada con patrón actual de reportes.

## Fase 6 — Integración con lo actual

Objetivo: convivencia limpia con flujos actuales.

### Entregables
- [x] Reuso de `DailyIncome` como base fiscal temporal.
- [x] Capa `income` operativa sin romper navegación activa.
- [x] Compatibilidad de servicios/rutas durante transición.

---

## 6) Tablero de ejecución activo

### Bloque inmediato (siguiente sprint técnico)

- [x] F0.1 Crear módulo de configuración global persistente (clave/valor + metadatos).
- [x] F0.2 Migrar `ACCOUNTING_FISCAL_THRESHOLD` a configuración editable en aplicación.
- [x] F0.3 Ajustar `ClientAccountingService` para leer umbral desde configuración global persistente.
- [x] F0.4 Crear UI mínima de administración para configuración global (solo umbral 500000 en esta fase).
- [ ] F2.1 Crear modelos `financial_ledger_entry` y `fiscal_income_entry`.
- [ ] F2.2 Crear migración Alembic.
- [ ] F2.3 Implementar `IncomePostingService`.
- [ ] F2.4 Integrar posting en flujo de `IncomeEvent`.
- [ ] F2.5 Validar smoke end-to-end en `webdev`.

### Bloque siguiente

- [ ] F3.1 Endpoint/servicio de pendientes por acreditar.
- [ ] F3.2 Endpoint/servicio de conciliación de pendiente.
- [ ] F4.1 Modelo y migración de comprobante de cobro.
- [ ] F0.x Agregar nuevas configuraciones globales transversales (por definir).

---

## 7) Bitácora de avance

- 2026-03-04: Se consolidó Fase 1 (`IncomeEvent`) y su migración.
- 2026-03-04: Se alineó capa `income` en rutas/servicios y compatibilidad operativa.
- 2026-03-04: Se rectificó este plan con matriz de referencias internas/externas y tablero de ejecución.
- 2026-03-04: Se añadió contextualización explícita para Cuba (tipos de cliente, regímenes, umbral y moneda local).
- 2026-03-04: Se cerraron decisiones funcionales: libro por régimen activo, transición anual TCP>500000, conciliación manual y comprobante bancario mínimo.
- 2026-03-04: Se agregó requisito de configuración global editable desde la aplicación para umbral de 500000 y base para futuras configuraciones globales.
- 2026-03-04: Se completó F0 (configuración global persistente + UI de umbral) y se validó smoke test funcional en `conda webdev` (`GET /clients/settings` 200, `GET /clients/list` 200, `POST /clients/settings` 302 y persistencia de umbral).
