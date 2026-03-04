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
7. Sub-saldos de efectivo por régimen (fiscal/financiera).
8. Movimientos internos y reglas operativas de fondos.
9. Reproceso histórico y reportes operativos de efectivo.
10. Configuración dinámica de fondos por negocio.
11. Consolidación UX/UI de vistas income (auditoría, unificación visual y HTMX).

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
- Se manejarán saldos en `CUP` por negocio y por ubicación principal: **caja** y **banco**.
- Para contabilidad **fiscal**, caja se divide en sub-saldos: `caja_fisica` y `caja_tarjeta_magnetica`.
- La **tarjeta magnética** está vinculada a la cuenta bancaria y se rige por reglas internas:
  - Transferencia interna `banco -> tarjeta`: disminuye banco y aumenta `caja_tarjeta_magnetica`.
  - La tarjeta no recibe transferencias externas directas.
  - La tarjeta solo aumenta por transferencia interna desde banco.
  - La tarjeta disminuye por pagos (tributos, compras y servicios).
- Para contabilidad **financiera**, caja se administra por sub-saldos operativos iniciales:
  - `tarjeta_magnetica`
  - `extraido_para_nomina` (si no se cobra nómina, se revierte a banco)
  - `fondo_para_cambios` (con control por denominaciones)
  - `fondo_para_pagos_menores` (con umbral propio por negocio y respaldo documental obligatorio en cada rebaja)
  - `fondo_para_compras` (con umbral propio por negocio y sin respaldo documental obligatorio)
  - `efectivo_por_depositar`
- Flujo financiero de ingreso y transferencias internas:
  - Cuando el ingreso se cobra en `cash`, aumenta `efectivo_por_depositar`.
  - `efectivo_por_depositar` puede transferirse a cualquier otro sub-saldo de caja o a banco.
  - Banco puede transferirse a cualquier sub-saldo de caja.
- El umbral de cada fondo define el **monto máximo por operación de compra/pago** permitido para ese fondo.
- Si una operación excede el umbral o no existe saldo suficiente, el sistema debe emitir **alerta de fondo insuficiente para la operación** y no ejecutar el movimiento.
- La alerta de fondo insuficiente será **solo informativa en UI/API** y **no se persistirá** como evento de rechazo.
- Debe existir trazabilidad completa de movimientos con fecha/hora de **ingreso** y **extracción** para banco y cada sub-saldo de caja.
- Para `transferencia`/`cheque`, el efectivo en banco **aumenta solo cuando el cobro está conciliado** (`pending -> collected`).
- Debe existir conteo/saldo independiente por sub-saldo y por negocio.
- Se realizará **recálculo histórico completo** para inicializar saldos desde la data existente.

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
- [x] Modelo `FinancialLedgerEntry`.
- [x] Modelo `FiscalIncomeEntry`.
- [x] Migración de ambas tablas con índices por negocio/fecha.
- [x] Servicio de posting idempotente desde `IncomeEvent`.
- [x] Regla de selección de libro por régimen activo del cliente.
- [x] Prueba de regla inmediato vs pendiente.

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
- [x] Consulta de pendientes por acreditar.
- [x] Operación de transición `pending -> collected`.
- [x] Registro de conciliación manual del cobro (usuario + fecha + referencia bancaria).
- [x] Actualización automática de impacto fiscal al conciliar.

## Fase 4 — Documento mínimo de cobro

Objetivo: cerrar pendientes mediante comprobante/confirmación de cobro.

### Entregables
- [x] Entidad `CollectionReceipt` (o equivalente mínima).
- [x] Relación con `IncomeEvent`.
- [x] Flujo de confirmación y cierre de pendiente por número de operación bancaria.

## Fase 5 — Reportes esenciales

Objetivo: cubrir visibilidad del régimen aplicable y sus obligaciones de reporte.

### Entregables
- [x] Libro de ingresos para clientes en régimen financiero (fecha de operación).
- [x] Libro de ingresos para clientes en régimen fiscal (fecha de cobro).
- [x] Pendientes por acreditar con aging simple.
- [x] Reporte de cumplimiento por régimen (fiscal o financiera) por período.

### Criterios de aceptación
- [x] Filtro por negocio y rango de fechas.
- [x] Filtro por régimen contable aplicable del cliente.
- [x] Totales consistentes con libros.
- [x] Exportación básica alineada con patrón actual de reportes.

## Fase 6 — Integración con lo actual

Objetivo: convivencia limpia con flujos actuales.

### Entregables
- [x] Reuso de `DailyIncome` como base fiscal temporal.
- [x] Capa `income` operativa sin romper navegación activa.
- [x] Compatibilidad de servicios/rutas durante transición.

## Fase 7 — Sub-saldos por régimen

Objetivo: modelar y persistir sub-saldos de efectivo según régimen contable.

### Entregables
- [x] Definir entidad de movimientos/saldos por negocio en `CUP` con ubicación y sub-saldo.
- [x] Implementar catálogo base de sub-saldos para régimen fiscal (`caja_fisica`, `caja_tarjeta_magnetica`, `banco`).
- [x] Implementar catálogo base de sub-saldos para régimen financiera (tarjeta, nómina, cambios, pagos menores, compras, por depositar, banco).
- [x] Garantizar actualización idempotente de saldos por evento/movimiento.

## Fase 8 — Reglas operativas y movimientos internos

Objetivo: aplicar reglas de negocio de incrementos/disminuciones por canal y operación interna.

### Entregables
- [x] Registrar `cash` en `caja_fisica`.
- [ ] Registrar `transferencia`/`cheque` en banco solo al conciliar (`pending -> collected`).
- [x] En contabilidad financiera, registrar ingreso `cash` en `efectivo_por_depositar`.
- [x] Permitir transferencia de `efectivo_por_depositar` a banco o a cualquier sub-saldo de caja.
- [x] Permitir transferencia de banco a cualquier sub-saldo de caja.
- [x] Implementar transferencia interna `banco -> tarjeta` (disminuye banco, aumenta sub-saldo tarjeta).
- [x] Implementar disminución de tarjeta por pagos (tributos, compras, servicios).
- [x] Implementar extracción para nómina y reversión a banco de no cobrado.
- [x] Implementar control de fondo para cambios con detalle de denominaciones.
- [ ] Implementar reglas de fondos para pagos menores/compras según umbral máximo por operación.
- [ ] Exigir respaldo documental en rebajas de `fondo_para_pagos_menores`.
- [ ] Permitir rebajas de `fondo_para_compras` sin respaldo documental obligatorio.
- [x] Emitir alerta y bloquear movimiento por fondo insuficiente o por exceder umbral.
- [x] Registrar fecha/hora de ingreso y extracción en cada movimiento de banco/sub-saldo.

## Fase 9 — Reproceso histórico y reportes de efectivo

Objetivo: reconstruir saldos y exponer visibilidad operativa por sub-saldo.

### Entregables
- [x] Script/migración de recálculo histórico completo por negocio y sub-saldo.
- [x] Validación de consistencia entre ingresos/eventos, conciliaciones y saldos resultantes.
- [x] Reporte de saldo actual por negocio (`banco` + sub-saldos de caja).
- [x] Reporte de movimientos por rango de fechas y sub-saldo.
- [x] Reporte cronológico de entradas/salidas (fecha/hora, origen, destino, monto, motivo).
- [x] Endpoint/API y exportación básica para reportes de efectivo.

## Fase 10 — Configuración dinámica de fondos

Objetivo: permitir que cada negocio configure sus fondos operativos y umbrales.

### Entregables
- [x] UI/API para activar/desactivar fondos por negocio.
- [x] Permitir crear fondos adicionales personalizados por negocio.
- [x] Configurar umbral de `fondo_para_pagos_menores` por negocio (máximo por operación).
- [x] Configurar umbral de `fondo_para_compras` por negocio (máximo por operación).
- [x] Configurar política documental por fondo (pagos menores obligatorio, compras no obligatorio).
- [x] Configurar monto objetivo de fondo para cambios por negocio.
- [x] Validaciones y auditoría básica de cambios de configuración.

## Fase 11 — Consolidación de vistas income y modelo visual único

Objetivo: auditar y depurar vistas relacionadas con `income`, unificar diseño fiscal/financiera y migrar interacción a HTMX + API con mínimo de vistas.

### Entregables
- [ ] Levantamiento completo de vistas relacionadas directa/indirectamente con `income` (web + componentes + modales + parciales + endpoints API usados).
- [ ] Matriz de depuración: identificar elementos/vistas innecesarias, duplicadas o de bajo valor y plan de eliminación/refactor.
- [ ] Definir y aplicar un modelo visual único para flujo fiscal y financiera (estructura, componentes, jerarquía y patrones de interacción comunes).
- [ ] Evaluar durante el levantamiento si se requieren vistas nuevas para funcionalidades de F1–F10 y documentar decisión por caso.
- [ ] Garantizar consistencia visual con el sistema actual (tokens, componentes y estilos existentes) sin introducir diseño paralelo.
- [ ] Priorizar formularios en modales y reducir navegación a pantallas separadas cuando no aporte valor.
- [ ] Reutilizar partials/componentes en todas las vistas posibles para evitar duplicación de markup/lógica de UI.
- [ ] Implementar interacciones con HTMX consumiendo API de `income`/`cash-flow` (alta, edición, conciliación, transferencias, configuración de fondos y reportes operativos).
- [ ] Definir guía de convenciones para nuevas vistas/parciales HTMX (nombres, rutas, fragmentos, manejo de errores/flash y estados vacíos).
- [ ] Smoke funcional de UX consolidada (desktop/móvil) y checklist de regresión básica en rutas de ingresos.

---

## 6) Tablero de ejecución activo

### Bloque inmediato (siguiente sprint técnico)

- [x] F0.1 Crear módulo de configuración global persistente (clave/valor + metadatos).
- [x] F0.2 Migrar `ACCOUNTING_FISCAL_THRESHOLD` a configuración editable en aplicación.
- [x] F0.3 Ajustar `ClientAccountingService` para leer umbral desde configuración global persistente.
- [x] F0.4 Crear UI mínima de administración para configuración global (solo umbral 500000 en esta fase).
- [x] F2.1 Crear modelos `financial_ledger_entry` y `fiscal_income_entry`.
- [x] F2.2 Crear migración Alembic.
- [x] F2.3 Implementar `IncomePostingService`.
- [x] F2.4 Integrar posting en flujo de `IncomeEvent`.
- [x] F2.5 Validar smoke end-to-end en `webdev`.

### Bloque siguiente

- [x] F3.1 Endpoint/servicio de pendientes por acreditar.
- [x] F3.2 Endpoint/servicio de conciliación de pendiente.
- [x] F4.1 Modelo y migración de comprobante de cobro.
- [ ] F0.x Agregar nuevas configuraciones globales transversales (por definir).
- [x] F7.1 Modelo de movimientos/saldos por ubicación y sub-saldo.
- [x] F7.2 Catálogo de sub-saldos por régimen (fiscal/financiera).
- [ ] F8.1 Reglas de canal para incrementos/disminuciones de saldos.
- [x] F8.2 Movimiento interno banco->tarjeta y pagos con tarjeta.
- [x] F8.3 Flujo de nómina (extracción y reversión de no cobrado).
- [x] F8.4 Fondo para cambios con denominaciones.
- [x] F8.5 Flujo `efectivo_por_depositar` -> (banco | sub-saldo de caja).
- [x] F8.6 Alertas y bloqueo por fondo insuficiente / umbral excedido.
- [x] F8.7 Trazabilidad fecha/hora en ingresos y extracciones.
- [x] F9.1 Recalcular histórico completo por sub-saldo.
- [x] F9.2 Validar consistencia de saldos históricos.
- [x] F9.3 Exponer reporte/API/export de saldos y movimientos.
- [x] F10.1 Configuración dinámica de fondos por negocio.
- [ ] F11.1 Levantamiento de vistas income y matriz de depuración.
- [ ] F11.2 Modelo visual único fiscal/financiera.
- [ ] F11.3 Refactor de vistas con modales + partials.
- [ ] F11.4 Integración HTMX + API en flujos de income/cash-flow.
- [ ] F11.5 Limpieza final de vistas innecesarias y smoke UX.

---

## 7) Bitácora de avance

- 2026-03-04: Se consolidó Fase 1 (`IncomeEvent`) y su migración.
- 2026-03-04: Se alineó capa `income` en rutas/servicios y compatibilidad operativa.
- 2026-03-04: Se rectificó este plan con matriz de referencias internas/externas y tablero de ejecución.
- 2026-03-04: Se añadió contextualización explícita para Cuba (tipos de cliente, regímenes, umbral y moneda local).
- 2026-03-04: Se cerraron decisiones funcionales: libro por régimen activo, transición anual TCP>500000, conciliación manual y comprobante bancario mínimo.
- 2026-03-04: Se agregó requisito de configuración global editable desde la aplicación para umbral de 500000 y base para futuras configuraciones globales.
- 2026-03-04: Se completó F0 (configuración global persistente + UI de umbral) y se validó smoke test funcional en `conda webdev` (`GET /clients/settings` 200, `GET /clients/list` 200, `POST /clients/settings` 302 y persistencia de umbral).
- 2026-03-04: Se completó F2 técnico inicial en `conda webdev`: modelos `financial_ledger_entry` y `fiscal_income_entry`, migración `9d41e3a2b7f1`, `IncomePostingService` idempotente e integración al crear `IncomeEvent` manual diario.
- 2026-03-04: Se validaron reglas F2 en smoke: régimen financiero publica en libro financiero, régimen fiscal inmediato publica en libro fiscal y fiscal pendiente no publica hasta cobro.
- 2026-03-04: Se completó F3 técnico en `conda webdev`: consulta de pendientes, conciliación manual (`pending -> collected`) y registro de conciliación (`reconciled_by`, `reconciled_at`, `bank_operation_number`).
- 2026-03-04: Se validó impacto fiscal automático al conciliar en smoke de F3 (evento fiscal pendiente conciliado crea `FiscalIncomeEntry` en fecha de cobro).
- 2026-03-04: Se completó F4 técnico en `conda webdev`: entidad `CollectionReceipt`, relación 1:1 con `IncomeEvent` y generación automática del comprobante mínimo al conciliar (`bank_operation_number`, fecha de cobro y banco opcional).
- 2026-03-04: Se validó smoke F4 en `webdev` con pendiente conciliado y comprobante asociado (`receipt -> True`, operación `F4-OP-99`).
- 2026-03-04: Se completó F5 técnico en `conda webdev`: endpoints de reportes para libro financiero, libro fiscal, pendientes con aging y cumplimiento por régimen con filtros por negocio/rango/ régimen aplicable.
- 2026-03-04: Se validó smoke F5 en `webdev` para JSON y exportación Excel (`/reports/*` y `/reports/*/export` con estado `200` en los cuatro reportes).
- 2026-03-04: Se consolidó F6 retirando rutas legacy de transición en `income`; quedaron canónicas `GET/POST /income/list`, `GET/POST /income/<id>` y `GET /income/records` en API.
- 2026-03-04: Se validó smoke de cierre sin rutas legacy en `webdev`: `GET /income/list` 200, `GET /income/sales` 404, `GET /income/<id>` 200, `GET /income/sales/<id>` 404 y `GET /income/records` 200.
- 2026-03-04: Se definió nueva línea de trabajo para efectivo por ubicación: caja y banco independientes en CUP, con mapeo de canales (`cash`/`tarjeta` -> caja; `transferencia`/`cheque` -> banco), impacto de banco al conciliar y recálculo histórico completo.
- 2026-03-04: Se refinó el diseño de efectivo: para fiscal, sub-saldos `caja_fisica` y `caja_tarjeta_magnetica`; para financiera, fondos operativos de caja (tarjeta, nómina, cambios, pagos menores, compras y por depositar) más banco.
- 2026-03-04: Se incorporó regla operativa de tarjeta magnética vinculada al banco: solo aumenta por transferencia interna desde banco y solo disminuye por pagos (tributos/compras/servicios).
- 2026-03-04: Se añadió fase de configuración dinámica de fondos por negocio (incluyendo umbrales y fondos personalizados).
- 2026-03-04: Se cerró criterio de umbrales por fondo: cada umbral define máximo por operación; `fondo_para_pagos_menores` exige respaldo documental en cada rebaja y `fondo_para_compras` no exige respaldo documental obligatorio.
- 2026-03-04: Se definió flujo financiero adicional: ingresos `cash` a `efectivo_por_depositar`, transferencias internas desde `efectivo_por_depositar` y desde banco hacia sub-saldos de caja, con registro de fecha/hora de entradas y extracciones.
- 2026-03-04: Se cerró regla de control operativo: ante fondo insuficiente o umbral excedido, el sistema emite alerta y bloquea la operación.
- 2026-03-04: Se cerró criterio de alerta operativa: aviso manual en UI/API sin guardar intentos rechazados en base de datos.
- 2026-03-04: Se inició implementación F7 en `conda webdev`: nuevos modelos `cash_subaccount_balance` y `cash_subaccount_movement`, servicio `CashFlowService` e integración en creación/conciliación de ingresos.
- 2026-03-04: Se aplicó migración `e8f1a2b3c4d5` y smoke técnico F7 en `webdev` (financiera: `cash_to_deposit=250`, fiscal: `bank=500` tras conciliación, movimientos registrados: `2`).
- 2026-03-04: Se completó tramo inicial F8 en `conda webdev`: transferencias internas manuales entre sub-saldos (`cash_to_deposit -> bank`, `bank -> sub-saldos de caja`) mediante endpoint API y servicio de flujo de efectivo.
- 2026-03-04: Se validó alerta/bloqueo por fondo insuficiente en smoke F8 (`POST /cash-flow/transfer` devuelve `400` con alerta y no altera saldos).
- 2026-03-04: Se completó F8.2 en `conda webdev`: endpoint de pago con tarjeta (`POST /cash-flow/card-payment`) y reglas de operación en sub-cuentas de tarjeta.
- 2026-03-04: Se completó F8.3 en `conda webdev`: endpoints para extracción y reversión de nómina (`POST /cash-flow/payroll/extract`, `POST /cash-flow/payroll/revert`) con validación de fondos y trazabilidad temporal.
- 2026-03-04: Smoke F8.2/F8.3 validado en `webdev`: `status -> 200 200 200 200 200 400`, alerta esperada por fondo insuficiente y balances finales `cash_to_deposit=100`, `bank=100`, `payroll_extracted=50`, `magnetic_card=30`.
- 2026-03-04: Se completó F8.4 en `conda webdev`: modelo/migración `cash_change_denomination`, endpoint `POST /cash-flow/change-fund/transfer` con validación de suma por denominaciones y consulta `GET /cash-flow/change-fund/movements`.
- 2026-03-04: Smoke F8.4 validado en `webdev`: transferencia válida al fondo para cambios (`200`) con 2 denominaciones registradas y bloqueo esperado (`400`) cuando la suma de denominaciones no coincide con el monto.
- 2026-03-04: Se completó F9 en `conda webdev`: recálculo histórico por sub-saldo (`POST /cash-flow/rebuild`), validación de consistencia (`GET /cash-flow/consistency`) y reportes de efectivo con exportación (`/cash-flow/reports/current-balance`, `/cash-flow/reports/movements`, `/cash-flow/reports/chronological` + `/export`).
- 2026-03-04: Se añadió script operativo de reproceso `migrations/migrate_rebuild_cash_subaccount_balances.py` para ejecutar recálculo masivo por negocio.
- 2026-03-04: Smoke F9 validado en `webdev`: consistencia `True -> False -> True` (antes de alterar, tras alterar saldo manualmente y después de recálculo), `updated_count=1` en rebuild y estado `200` en reportes/exportes de efectivo.
- 2026-03-04: Se avanzó F10 backend/API en `conda webdev`: modelo/migración `business_cash_fund_config`, endpoints `GET/POST /cash-flow/funds/config` y `POST /cash-flow/funds/custom` para activación, umbrales, política documental, objetivo y fondos personalizados.
- 2026-03-04: Se integraron reglas dinámicas al flujo de transferencias: bloqueo por umbral excedido, exigencia de `supporting_document_ref` cuando aplica, y bloqueo de movimientos desde sub-cuentas desactivadas.
- 2026-03-04: Smoke F10 backend validado en `webdev`: fondos personalizados operativos, rebaja bloqueada por umbral, rebaja bloqueada por falta de respaldo documental, operación permitida con respaldo, y bloqueo esperado al desactivar fondo (`status -> 200/400` según caso).
- 2026-03-04: Se completó UI mínima de F10 en `income`: vista `GET/POST /income/funds/settings` para editar fondos existentes y crear fondos personalizados, con acceso directo desde la pantalla de ingresos.
- 2026-03-04: Smoke UI F10 validado en `webdev`: `GET` de vista (`200`), `POST` de actualización/creación (`302`) y render de resultados (`200`) con fondo personalizado visible en pantalla.
- 2026-03-04: Se incorporó F11 en el plan: auditoría integral de vistas relacionadas con `income`, definición de modelo visual único fiscal/financiera, reducción de vistas con uso de modales/partials y estrategia de implementación con HTMX consumiendo API.
