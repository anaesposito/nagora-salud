# Liquidaciones manuales — Issues #8 y #18

Decisión de producto del 14/11/2026: carga manual simple, sin importadores ni reglas de tasas automáticas. Una liquidación identifica un pagador y una referencia, y distribuye importes sobre **prestaciones ya registradas**. No crea honorarios nuevos ni agrega el total de cabecera a caja otra vez.

## Uso

En **Ingresos → Liquidaciones de pagadores → Cargar liquidación**:

1. Identificar pagador, referencia, dinero efectivamente recibido, fecha y medio de cobro.
2. Elegir prestaciones del pagador y asignar importes. Descuentos y retenciones están en un detalle opcional; la diferencia se calcula en centavos y necesita explicación.
3. Revisar el desglose y confirmar. Un error conserva el formulario. Volver al paso anterior conserva las asignaciones.

Admite una a treinta prestaciones por carga. La referencia es única dentro de la cuenta y el pagador. Se puede registrar cero recibido si hay importes retenidos o diferencias. No admite fechas futuras, gastos, prestaciones anuladas, repetidas ni de otra cuenta/pagador. El cuerpo HTTP sigue limitado a 16 KiB: si hay muchas explicaciones largas, cargar grupos más pequeños con referencias distintas de documentos reales; no dividir ni inventar documentos para eludir controles.

## Qué significa cada importe

| Concepto | Tratamiento |
|---|---|
| Honorarios generados | Importe de la prestación existente. No se vuelve a generar al liquidar. Se conserva también la cifra al cargar cada versión. |
| Importe incluido | Parte del saldo que abarca esta liquidación; permite pagos/liquidaciones parciales. |
| Recibido | Dinero acreditado. Único componente que aumenta caja, en la fecha del cobro vigente. |
| Descuento aceptado | Descuento, comisión o débito que la persona acepta. Reduce saldo y resultado; se exige clasificación y explicación. |
| Retenido | Se clasifica como tributario, contractual o por clasificar. Reduce el saldo exigible al pagador, pero se expone aparte como retención pendiente de tratamiento: no aumenta caja ni reduce resultado como pérdida. |
| Diferencia por resolver | Parte del importe incluido que no es recibido, descuento ni retención. Continúa dentro del saldo pendiente, no genera un segundo ajuste. |

Por prestación: `incluido = recibido + descuento aceptado + retenido + diferencia`.
Por liquidación: `recibido de cabecera = suma de recibido asignado`.
El incluido no puede superar el saldo disponible. Las sumas usan enteros en centavos; no hay división proporcional ni redondeo automático. La API exige texto monetario argentino con hasta dos decimales, nunca floats.

Ejemplo: honorarios $100,01; recibido $80,01; descuento $5; retención $10; diferencia $5. Caja sube $80,01; resultado baja sólo $5; quedan $5 exigibles y $10 identificados como retenidos. Con una segunda prestación de $200,02 que recibe $130,01, los totales son: generado $300,03, caja $210,02, descuento $5, retenido $10 y pendiente $75,01.

Los pendientes actuales se calculan por prestación considerando **todos** sus cobros. Una diferencia de una liquidación anterior puede quedar pagada posteriormente: el detalle conserva la diferencia informada y muestra el pendiente actual, y advierte que no deben sumarse. No se suman diferencias históricas como nuevas deudas. Los honorarios por mes y los cobros por mes usan sus fechas respectivas.

Las retenciones históricas del registro anterior también dejan de restarse del resultado; no se altera ni borra su registro. Su clasificación histórica no se inventa. Las nuevas retenciones se ingresan por Liquidaciones; el formulario de ajustes individuales ya no las ofrece. Esta corrección de semántica puede aumentar el resultado histórico respecto del cálculo anterior, sin cambiar caja. Se debe comunicar al revisar la entrega.

## Correcciones y PR #42

Este PR se apila sobre `feat/issue-9-payment-corrections` (PR #42, `936b624`). No fusiona esa rama en main ni duplica su implementación. Revisados también #32 (cobro parcial), #33 (frontera HTTP), #34 (autenticación/backups) y #35 (zona horaria/UX). No se incorporan sus cambios aún abiertos. Si se integran primero, reconciliar `server.py`, `domain.py`, `static/app.js` y CI y repetir las pruebas.

- **Corregir liquidación** guarda una nueva versión completa con motivo obligatorio. Pagador y referencia conservan la identidad; asignaciones, clasificación, fecha y recibidos se pueden corregir. La confirmación explica que todos sus cobros pasan a la nueva fecha y se recalculan los meses afectados.
- Las versiones y asignaciones anteriores permanecen inmutables. La vista `effective_settlement` cuenta sólo las entradas de la última versión del grupo, y sobre ellas aplica las revisiones individuales de #42. Cabecera no participa como segundo cobro.
- **Modificar/revertir cobro** conserva los endpoints y control de versión de #42. Una reducción/reversión aumenta la diferencia del grupo y el pendiente de la prestación. Un aumento no puede invadir el descuento, la retención ni el importe fuera de la asignación: para cambiar esos componentes se corrige el grupo.
- Para liberar una retención, corregir el grupo con el dinero acreditado y menor retenido; para aceptar una diferencia como descuento, clasificarla explícitamente en una corrección. Ninguna decisión se toma automáticamente.
- La huella de corrección incluye la versión del grupo, cobros efectivos y saldo actual. Si otra pestaña cobró o corrigió entretanto, devuelve 409 antes de escribir. Una versión antigua no se puede volver a corregir como si fuera un cobro vigente.
- Anular una prestación conserva su historial y la excluye de los totales como antes; la liquidación conserva el desglose histórico y no suma ese cobro anulado al recibido vigente. No permite corregir el grupo mientras contiene una prestación anulada.

## Integridad y privacidad

Migración aditiva `003_liquidations.sql`: cabecera, revisiones, asignaciones y enlaces a cobros. Claves foráneas compuestas con `owner`, unicidad y checks de centavos. Triggers bloquean UPDATE/DELETE, incluso reemplazos con triggers recursivos activados. Auditoría también inmutable (migración 002).

El endpoint usa la sesión vigente y la misma transacción `BEGIN IMMEDIATE` del servidor. Lectura de saldo, idempotencia, nueva versión, registros de cobro y auditoría se confirman juntos. Una excepción revierte todo. No hay escrituras de saldo fuera de esa transacción. La inmutabilidad no protege contra un administrador que cambie el esquema/archivo SQLite: siguen siendo necesarios permisos y backups.

Una clave idempotente se vincula a la carga normalizada (incluida versión/huella para correcciones). Mismo contenido devuelve el ID/versión original; otra carga con esa clave devuelve 409. Se impide reutilizar claves de otras operaciones. La referencia evita guardar nuevamente el mismo documento con una clave nueva. La aplicación no puede identificar un mismo pago bancario si alguien le da deliberadamente otra referencia: no hay integración bancaria.

No se solicitan datos clínicos, no se usan servicios externos ni IA, no hay reglas tributarias o porcentajes codificados. Plazos y términos por pagador siguen siendo los configurados en Convenios; esta entrega registra importes efectivamente informados, no un motor de estimaciones por contrato.

## Evidencia y límites

- `python -m unittest -q`: 27 pruebas unitarias/integración locales, incluidas concurrencia real, pagos parciales, centavos, reintentos, cuentas ajenas, sesión vencida, rollback por fallo de auditoría, migración repetible, clasificación/liberación de retenciones y compatibilidad con #42.
- `node --check static/app.js` y `node --check static/liquidations.js`.
- `python tests/run_liquidation_local.py`: servidor y SQLite temporales, Chromium real; pasos completos a 320/375/768/1280 px, validación sin perder datos, dos pestañas, corrección de cobro y recarga. Requiere Playwright 1.58.0 y Chromium; en Windows, tzdata.
- Capturas ficticias en `artifacts/visual/liquidacion-*`; CI las adjunta en `nagora-visual-smoke`. Revisión visual local de escritorio y móvil realizada.
- CI mantiene los recorridos visuales previos y el de corrección/reversión de #42. Habilita el disparador para la rama base del PR apilado.
- Pendiente: prueba de usabilidad con una persona no técnica, auditoría completa de accesibilidad y aprobación de producto. No se declara listo para producción ni se cierran issues automáticamente.
