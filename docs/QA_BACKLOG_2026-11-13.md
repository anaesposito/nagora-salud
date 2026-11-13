# Revisión de los 25 issues y evidencia

13/11/2026. Lectura directa de issues y código. 24 abiertos; #11 ya estaba cerrado.
No se cerraron issues en esta revisión. Estado sugerido para un futuro Kanban,
no una afirmación de que GitHub Projects esté configurado.

| Issue | Evaluación y estado propuesto | Evidencia / pendiente para cierre |
|---|---|---|
| #2 QA móvil | En revisión parcial | Inicio/Ingresos/Gastos a 320/360/375/390/768/1280/1366 px; sin overflow. Faltan dispositivos físicos y aprobación. |
| #3 Home/navegación | En revisión parcial | Tres cifras existentes; navegación reducida a Inicio/Ingresos/Gastos/Más. Validar comprensión con profesionales. |
| #4 Proyección | Por hacer | El Home distingue neto cobrado de proyección; no existe cálculo de cierre ni saldo inicial. No se presenta como implementado. |
| #5 Seguridad | En revisión parcial | PR #34: límites, sesiones, recuperación, respaldo. Falta revisión independiente y entorno de staging operativo. |
| #6 Ingresos | En revisión parcial | Tests de pagos parciales, idempotencia concurrente y centavos. PR #32 agrega prueba UI aún no integrada. |
| #7 Gastos | En revisión parcial | Alta/edición UI, recurrencia febrero bisiesto y materialización repetida. Falta probar todas las correcciones de series. |
| #8 Liquidaciones | Backlog | Ajustes individuales existentes; faltan reglas configurables de comisiones/retenciones y estimado versus liquidado. |
| #9 Reversión individual | Backlog | No existe: solo anulación del movimiento completo. Requiere modelo y trazabilidad de reversión. |
| #10 Exportación | Backlog | No hay endpoint CSV ni acción de exportar. Debe cubrir filtros, aislamiento e inyección de fórmulas. |
| #11 CI | Cerrado previamente; validación parcial | Actions verdes verificados. Protección main devuelve 403; no afirmar bloqueo de merge validado. Se agrega Windows a CI. |
| #12 Accesibilidad | En revisión parcial | Axe sin infracciones automáticas en 3 pantallas × 7 anchos, error de gasto, login y recuperación × 2 anchos. No certifica WCAG; faltan lector y zoom real 200%. |
| #13 Autenticación | En revisión parcial | PR #34: límites, expiración, revocación y uso único. Falta correo verificado y flujo sin código previo; registro diferencia duplicados. |
| #14 Backups | En revisión parcial | Copia/restauración probadas; ejecutor horario y 30 días aprobados e implementados. Falta destino cifrado externo, activación, alertas y RTO medido. |
| #15 Onboarding | En revisión parcial | Demo y cuenta vacía aisladas probadas. Se corrige dependencia IANA faltante en Windows. Falta prueba con usuarios. |
| #16 Cartera | Backlog | No hay entidad de contacto/consentimiento; mantener fuera datos clínicos. |
| #17 Convenios | Backlog | Pagadores con plazo y texto; sin tarifas estructuradas ni vigencia. |
| #18 Conciliación múltiple | Backlog | Cada pago se asocia a un movimiento; distribución entre varios no implementada. |
| #19 Mensajes/estados | En revisión parcial | Error de formulario conserva datos, recibe foco y descripción accesible. Falta auditoría completa offline/carga/confirmación. |
| #20 Cálculos | En revisión parcial | Centavos, límites de entrada, caja versus fecha de prestación, ajustes, bisiesto y concurrencia probados. Falta cobertura exhaustiva y revisión del producto. |
| #21 Profesionales | Bloqueado por participantes | Preparar y ejecutar sesiones con personas reales; no reemplazar con pruebas automáticas ni inventar métricas. |
| #22 Voz | En revisión parcial | Existe dictado del navegador y revisión en formulario; falta auditoría de privacidad/proveedor/costos y escenarios de consentimiento. |
| #23 ARCA | Bloqueado por discovery especializado | No hay integración; normativa, credenciales y homologación requieren validación específica. |
| #24 Recordatorios | Backlog | Recordatorios internos existentes; no hay mensajería externa ni consentimiento por canal. |
| #25 Reportes | Backlog | Resultado de un período existente; comparativos/tendencias no implementados. |
| #26 Escalabilidad | Backlog | SQLite/servidor local; falta infraestructura comercial, concurrencia objetivo, observabilidad y recuperación operativa. |

## QA reproducible

- `python -m pip install -r requirements.txt` instala IANA también en Windows.
- `python -m unittest -v`; `node --check static/app.js`.
- Instalar Playwright 1.58.0 y Chromium; `python tests/run_visual_local.py` usa
  una base temporal y detiene su servidor al finalizar.
- Axe 4.11.0: definir `NAGORA_AXE_PATH` al archivo axe.min.js para que se ejecute
  la auditoría. CI lo instala y exige cero infracciones automáticas detectadas.
- `NAGORA_QA_DEMO_ONLY=0` y `NAGORA_QA_SCRIPT=tests/auth_visual.py` prueban login
  y recuperación con cuentas ficticias. No se usan credenciales reales.
- Capturas y resultados de Axe quedan en el artefacto `nagora-visual-smoke` de Actions.

## Hallazgo de zona horaria reportado por la usuaria

El primer acceso a datos de ejemplo fallaba en Windows sin datos IANA. Se reprodujo
`ZoneInfoNotFoundError`, se agregó requirements.txt con tzdata y se verifica la zona
al iniciar, antes de abrir base/socket. Se mantiene America/Argentina/Buenos_Aires;
no se sustituye por zona local ni offset fijo. En Python local se instaló tzdata
y pasaron dos pruebas de zona y el ingreso HTTP a demo con totales reconciliados.

## Bloqueos de acceso y validación

Projects no tiene herramientas en el conector; el acceso al navegador venció por
autorización. No se crearon columnas ni se vincularon issues. Protección de main:
403 de integración, pendiente de alguien con administración. No hubo despliegue,
merge ni nuevos cierres. Las capturas inspeccionadas de 375/1280 px tienen datos
ficticios. No equivalen a usabilidad validada ni a preparación productiva.
