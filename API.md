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
| POST /movements/{id}/void | note |
| POST /movements/{id}/remind | day, note |
| POST /reminders/{id} | Marca un recordatorio como completado |
| POST /payers | kind, name, days, terms |
| POST /profile | name |

Las fechas usan AAAA-MM-DD. Las entradas monetarias son texto en formato argentino, por ejemplo `70.000,50`. Las salidas monetarias se expresan en centavos. Los errores incluyen un campo `error` con mensaje. Una sesión ausente devuelve 401, un origen no permitido 403 y un recurso inexistente o ajeno 404. Las validaciones devuelven 400.
