# F11.1 — Levantamiento de vistas relacionadas con income

Fecha: 2026-03-04
Estado: completado (inventario y matriz inicial)

## 1) Alcance revisado

### Rutas web
- `app/routes/income.py`
  - `GET/POST /income/list`
  - `GET/POST /income/<sale_id>`
  - `POST /income/events/<income_event_id>/reconcile`
  - `GET/POST /income/funds/settings`

### Rutas API vinculadas a income/cash-flow
- `app/routes/api/income.py`
  - Registros/pending/reconcile (`/records`, `/pending`, `/events/<id>/reconcile`)
  - Cash-flow (`/cash-flow/*`): balances, transferencias, card-payment, payroll, change-fund
  - Configuración de fondos (`/cash-flow/funds/config`, `/cash-flow/funds/custom`)
  - Reportes cash-flow (`/cash-flow/reports/*` + export)
  - Reportes contables (`/reports/*` + export)

### Vistas/templates
- `app/templates/income/list.html`
- `app/templates/income/details.html`
- `app/templates/income/funds_settings.html`

### Formularios
- `app/forms/income.py`
  - `IncomeForm`
  - `IncomeDetailForm`
  - `UpdateIncomeDetailForm`
  - `RemoveIncomeDetailForm`
  - `DailyManualIncomeForm`

### Servicios núcleo
- `app/services/income_service.py` (facade actual)
- `app/services/income_management_service.py` (lógica principal)
- `app/services/cash_flow_service.py` (cash-flow + fondos)
- `app/services/income_report_service.py` (reportes)

## 2) Hallazgos clave (UX/UI)

1. **Duplicación alta de markup en modales**
   - `details.html` concentra múltiples modales grandes (update sale, add product, update product, add sale), con formularios extensos repetidos.

2. **Dos patrones de interacción mezclados**
   - Flujo sincrónico clásico (submit + redirect + flash) convive con modales Flowbite.
   - No hay HTMX en vistas `income` actualmente.

3. **Acoplamiento fuerte vista-servicio**
   - `income.py` resuelve muchos casos en un solo endpoint por pantalla (especialmente `details`), dificultando fragmentación incremental.

4. **Unificación fiscal/financiera parcial**
   - Existe unificación funcional en backend, pero la UI aún no expresa claramente un modelo único para ambos regímenes.

5. **Nueva vista F10 agregada (funds_settings)**
   - Útil y operativa, pero todavía en patrón full-page POST/redirect y sin partials.

## 3) Matriz de depuración (mantener/refactor/eliminar/crear)

| Elemento | Estado propuesto | Acción |
|---|---|---|
| `income/list.html` | Mantener + refactor | Separar en partials (toolbar, tabla diaria, tabla detallada, modales). Migrar filtros/acciones a HTMX. |
| `income/details.html` | Mantener + refactor fuerte | Extraer modales y tabla de productos a partials; migrar CRUD de detalle a endpoints API + HTMX. |
| `income/funds_settings.html` | Mantener + refactor incremental | Convertir formularios por fila a swaps HTMX, feedback inline por bloque. |
| `routes/income.py` | Mantener + refactor | Reducir handlers monolíticos, delegar acciones a API y devolver fragmentos para HTMX. |
| `forms/income.py` | Mantener + ajustar | Estandarizar campos entre fiscal/financiera; preparar uso en modales parciales. |
| Vistas legacy adicionales de ingresos | Candidatas a eliminar | Confirmar en barrido final de rutas/templates no referenciadas tras migración HTMX. |

## 4) Nuevas vistas/partials recomendadas (F11.2/F11.3)

### Partials a crear
- `app/templates/income/partials/_income_toolbar.html`
- `app/templates/income/partials/_income_daily_table.html`
- `app/templates/income/partials/_income_detailed_table.html`
- `app/templates/income/partials/_sale_summary_card.html`
- `app/templates/income/partials/_sale_products_table.html`
- `app/templates/income/partials/modals/_income_create_modal.html`
- `app/templates/income/partials/modals/_sale_update_modal.html`
- `app/templates/income/partials/modals/_sale_detail_create_modal.html`
- `app/templates/income/partials/modals/_sale_detail_update_modal.html`
- `app/templates/income/partials/_fund_config_table.html`
- `app/templates/income/partials/_fund_custom_form.html`

### Vistas nuevas (solo si aportan)
- No crear páginas nuevas por defecto.
- Priorizar fragmentos HTMX sobre páginas completas.
- Única excepción sugerida: una vista consolidada de operaciones de cash-flow si en F11.4 se demuestra alta fricción de navegación.

## 5) Modelo visual único propuesto (fiscal/financiera)

- **Cabecera común**: negocio, régimen activo, mes/filtro.
- **Bloque común de KPIs**: total ingresos, pendientes, saldo banco, saldo caja.
- **Listado principal único**: mismo layout, con columnas condicionales por régimen cuando aplique.
- **Acciones uniformes**: crear/editar/conciliar/transferir siempre en modales.
- **Errores y alertas**: mensajes inline por bloque + flash global de respaldo.

## 6) Estrategia HTMX + API

1. Usar `app/routes/api/income.py` como backend principal de acciones.
2. Incorporar endpoints de fragmentos HTML ligeros en `routes/income.py` solo para render de partials.
3. Implementar por etapas:
   - Etapa A: filtros/listados en `list` (swap de tabla)
   - Etapa B: CRUD de productos en `details` (swap de tabla resumen)
   - Etapa C: fondos settings por fila (update/create sin full reload)
   - Etapa D: conciliación y transferencias en modales HTMX

## 7) Checklist de consistencia visual

- Reutilizar componentes y clases existentes (Flowbite/Tailwind actuales).
- Evitar nuevas páginas cuando una modal + partial sea suficiente.
- Unificar encabezados, botones primarios, estados vacíos y mensajes de error.
- Mantener soporte desktop/móvil en los mismos fragmentos.

## 8) Riesgos y mitigación

- **Riesgo**: romper formularios existentes en migración parcial.
  - Mitigación: mantener fallback POST tradicional mientras se activa HTMX por bloque.
- **Riesgo**: fragmentación excesiva de partials.
  - Mitigación: convención de nombres y límite de responsabilidades por partial.
- **Riesgo**: inconsistencias entre API y formularios web.
  - Mitigación: reutilizar validaciones de servicio y mensajes de error unificados.

## 9) Recomendación inmediata (siguiente paso)

Iniciar F11.2 con prototipo sobre `income/list`:
- extraer toolbar + tabla diaria/detallada en partials,
- aplicar HTMX en filtro de mes,
- mantener fallback sin JS.

## 10) Estado actualizado de ejecución (2026-03-04)

### Implementado
- `income/list`: partials `_income_toolbar` + `_income_list_content`, filtro por mes con HTMX y fallback clásico.
- `income/details`: partials `_sale_detail_panel`, `_sale_products_summary`, y modales extraídos (`_add_product_modal`, `_update_product_modal`, `_update_sale_modal`, `_add_sale_modal`).
- `income/funds/settings`: partials `_fund_config_table`, `_fund_custom_form`, `_funds_settings_content`.
- HTMX activo en operaciones clave:
  - `details`: agregar/editar/eliminar producto y actualizar venta con refresh parcial de `#sale-detail-panel` + mensaje inline.
  - `funds/settings`: update/create con swap parcial de `#funds-settings-content` + mensaje inline.
  - `income/list`: conciliación de pendientes (`/events/<id>/reconcile`) con `hx-post` y refresh parcial de `#income-list-content`.
  - `funds/settings`: transferencia interna entre fondos (`action=transfer`) con `hx-post` y refresh parcial de `#funds-settings-content`.

### Pendiente para F11.5 (cierre)
- Ejecutar barrido final de vistas legacy no referenciadas y documentar eliminación si aplica.
- Completar smoke UX consolidado desktop/móvil sobre rutas `income/list`, `income/<id>`, `income/funds/settings`.
- Cerrar checklist de regresión básica con evidencia (status/contains) por flujo HTMX y fallback tradicional.

### Nota técnica adicional (F11.4 cash-flow)
- En entorno local de smoke, la validación automática de transferencias puede quedar limitada si no existe la tabla `business_cash_fund_config` (migraciones incompletas en DB de prueba).
- La ruta y el render HTMX quedan implementados; para verificar E2E de transferencia se requiere base con migraciones de fondos aplicadas.

### Smoke E2E con DB migrada completa (2026-03-04)
- DB usada: `instance/e2e_smoke_migrated.db` (copia de `bookkeeply.db` + `flask db upgrade` hasta `head`).
- Verificación de migración: tabla `business_cash_fund_config` disponible tras upgrade.
- Resultado smoke E2E (`webdev`):
  - `list_get_status: 200` + `id="income-list-content"` presente.
  - `reconcile_htmx_status: 200` + refresh parcial de `income-list-content` confirmado.
  - `funds_get_status: 200` + formulario de transferencia visible.
  - `transfer_htmx_status: 200` + refresh parcial de `funds-settings-content` + feedback inline confirmado.

## 11) Evidencia de cierre técnico F11.5 (2026-03-04)

### Barrido legacy
- No se detectaron rutas legacy activas de `income` en templates/rutas actuales.
- Coincidencias de "deprecated" encontradas fueron en librerías de terceros (`app/static/js/chart.js`), sin impacto en flujo `income`.

### Smoke consolidado (webdev)
- `status-main -> 200 200 200`
  - `GET /income/list`
  - `GET /income/<sale_id>`
  - `GET /income/funds/settings`
- `status-htmx -> 200 200 200 200`
  - `GET` HTMX de `income/list`
  - `POST` HTMX update en fondos
  - `POST` HTMX update en detalle de venta
  - `POST` HTMX add de producto
- `status-fallback -> 302 302`
  - `POST` tradicional de fondos (redirect esperado)
  - `POST` tradicional en detalle (redirect esperado)
- `contains -> True True True True`
  - Fragmento `#income-list-content` presente
  - Fragmento `#funds-settings-content` presente
  - Fragmento `#sale-detail-panel` presente
  - Mensaje inline de agregado de producto presente

### Estado de cierre
- Cierre técnico F11.5: **completado** para cobertura funcional server-render + HTMX + fallback.
- Pendiente no automatizado: validación visual manual completa desktop/móvil (UI responsive) en navegador.

## 12) Saneo de valores legacy (2026-03-04)

- Se consolidó el catálogo interno de `payment_method` en `cash`, `transfer`, `check`.
- Se aplicó migración de saneo `e3b6a4d1f9c2_normalize_legacy_payment_methods_to_catalog.py` para normalizar variantes legacy en `sale.payment_method`.
- Mapeos legacy cubiertos: `cheque`, `transferencia`, `bank`, `card`, `mix`, `other`, `tarjeta`, `mixto`, `otro` y valores vacíos.
