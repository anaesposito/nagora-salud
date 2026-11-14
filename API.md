# API de Nagora Salud

Todas las rutas están bajo `/api`. Las escrituras usan POST con JSON y deben incluir el origen configurado. Las operaciones autenticadas usan una cookie de sesión. Las mutaciones de movimientos, convenios, recordatorios y perfil requieren una clave UUID `key` por operación. Para reintentar la misma operación, reutilizá la clave.

| Método y ruta | Datos |
|---|---|
| POST /register | email, name, password |
| POST /login | email, password |
| POST /demo | objeto vacío |
| POST /logout | objeto vacío |
| POST /recovery | password. Devuelve un código de recuperación una sola vez |
| POST /reset | email, code, password. Revoca las sesiones existentes |
| GET /state?month=AAAA-MM | Devuelve perfil, entidades, recordatorios, movimientos, totales y fechas |
| POST /movements | kind (income o expense), source, concept, amount, day. Opcionales payer, due, reference, paid, paid_day, recurrence, confirm_duplicate |
| POST /movements/{id}/edit | Campos editables del movimiento. Mantiene su historial de pagos |
| POST /movements/{id}/settle | amount, day, reason (Pago, Descuento, Retención, Débito o Ajuste) |
| POST /movements/{id}/payments/{payment}/correct | key, version, note, amount, day |
| POST /movements/{id}/payments/{payment}/reverse | key, version, note |
| POST /liquidations | key, payer, reference, day, received, method, allocations |
| POST /liquidations/{id}/correct | Los mismos campos más version, token, note |
| POST /movements/{id}/void | note |
| POST /movements/{id}/remind | day, note |
| POST /reminders/{id} | Marca un recordatorio como completado |
| POST /payers | kind, name, days, terms |
| POST /profile | name |

Las fechas usan AAAA-MM-DD. Las entradas monetarias son texto en formato argentino, por ejemplo `70.000,50`. Las salidas monetarias se expresan en centavos. Los errores incluyen un campo `error` con mensaje. Una sesión ausente devuelve 401, un origen no permitido 403 y un recurso inexistente o ajeno 404. Las validaciones devuelven 400.

Los cobros de ingresos se corrigen por importe o fecha y se revierten de forma
individual. `payment` es el ID del cobro activo en `settlements` y `version` su
versión actual (0 para el original). `note` es un motivo administrativo obligatorio
de hasta 120 caracteres. Evitá datos de pacientes. Una versión desactualizada, un
cobro reversado, un movimiento anulado o una clave reutilizada con otro cambio
devuelven 409. El reintento del cambio ya aplicado devuelve el mismo éxito.

`settlements` contiene los pagos y ajustes vigentes. `payment_history` incluye
los originales y sus revisiones en orden, incluyendo la reversión con `amount`
y `day` nulos. La caja se recalcula en los meses de los cobros efectivos. Los
honorarios devengados y los ajustes de liquidación conservan su propio cálculo.

`allocations` contiene de 1 a 30 objetos con `movement` entero; `allocated`,
`cash`, `discount`, `retained`, `difference` como texto monetario (admite `"0"`);
`discount_kind`, `retention_kind` y `note` cuando corresponden. `received` debe
igualar la suma exacta de `cash`. `allocated` debe igualar los cuatro componentes
y caber en el saldo disponible. La respuesta es `{id, version}`. El estado incluye
`liquidations` con `token` para corregir, asignaciones efectivas e historial.
Reintentos iguales devuelven la misma respuesta; claves/referencias repetidas con
otra carga o huellas desactualizadas devuelven 409. Recursos de otra cuenta: 404.

`totals.generated` y `totals.discounts` corresponden al mes consultado;
`totals.retained` es el acumulado vigente de retenciones, separado de caja y
resultado. Las retenciones ya no reducen `activity`. Las nuevas se registran sólo
por Liquidaciones para exigir clasificación. Ver [reglas y ejemplos](docs/LIQUIDATIONS.md).
