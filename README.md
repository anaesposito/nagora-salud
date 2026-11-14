# Nagora Salud
Es momento de gestionar.

## Cómo ejecutarlo

1. Descomprimí el ZIP y abrí una terminal dentro de la carpeta `nagora-salud`.
2. Ejecutá `python server.py` con Python 3.11 o posterior y datos de zona horaria de IANA disponibles.
3. Abrí http://127.0.0.1:8000 y elegí **Probar con datos de ejemplo** o **Crear cuenta**.

La aplicación se ejecuta en loopback y crea `nagora.sqlite3` en el directorio de trabajo. Podés elegir el archivo con `NAGORA_DB` y el puerto con `NAGORA_PORT`. Para TLS local usá `NAGORA_CERT` y `NAGORA_KEY` y abrí la dirección HTTPS impresa por el servidor. `NAGORA_ORIGIN` permite indicar el origen exacto si configurás un acceso distinto. No requiere instalación de paquetes externos.

## Arquitectura y componentes

Monolito modular en Python y SQLite, con HTML, CSS responsive y JavaScript sin dependencias. Se eligió esta alternativa para entregar un ejecutable verificable y reproducible con el entorno disponible. La API aplica reglas del lado del servidor y la interfaz consume los resultados calculados por el dominio.

| Ruta | Responsabilidad |
|---|---|
| `server.py` | HTTP, autenticación, sesiones, permisos y transacciones |
| `domain.py` | Dinero exacto, ingresos, pagos, ajustes, gastos, recurrencias, indicadores y demo |
| `migrations/001.sql` | Esquema relacional inicial, repetible |
| `static/` | Inicio, tarjetas de indicadores, navegación, fichas de movimientos, formularios guiados y ayuda |
| `test_app.py` | Pruebas de integración HTTP contra una base aislada |
| `API.md` | Operaciones y contrato de la API |

## Modelo y reglas

Cada cuenta posee su espacio privado y perfil. Las entidades pagadoras, los movimientos y los recordatorios se limitan a ese espacio. El modelo compacto representa honorarios por cobrar y gastos en `movement`. Los pagos y ajustes quedan como registros separados en `settlement`, asignados a un único movimiento mediante clave foránea compuesta. Un gasto mensual genera una obligación por mes y su pago se registra sobre esa obligación. La recurrencia se materializa hasta el mes siguiente al consultar el estado. Cada mutación financiera conserva su registro de auditoría. Las escrituras se serializan en transacciones SQLite y usan una clave de idempotencia.

Los montos son ARS en centavos enteros. La entrada acepta hasta dos decimales sin redondeo implícito. La fecha de caja es la del pago. El saldo pendiente es actual e incluye todos los meses. El resultado de la actividad toma la fecha del movimiento y descuenta ajustes en la fecha del ajuste. Las anulaciones conservan el historial y excluyen el movimiento completo de los indicadores.

La demo usa un espacio aislado por sesión y reconcilia $2.450.000 cobrados, $780.000 pendientes, $920.000 pagados y $1.530.000 restantes. Las cuentas nuevas comienzan vacías.

## Verificación

Ejecutá `python -m unittest -v` y `node --check static/app.js`. Las pruebas cubren registro cobrado y pendiente, persistencia, login, recuperación por código, cobros completos y parciales, descuentos, edición, anulación, importes inválidos, recurrencias, duplicados, período, demo, origen de escrituras y aislamiento entre cuentas.

La interfaz incorpora diseño adaptable, navegación mediante controles nativos, diálogo modal y foco visible. La experiencia en navegador, teclado y dispositivos móviles y la conformidad WCAG 2.2 AA requieren validación específica. La medición de comprensión en 10 segundos y carga en 30 segundos requiere pruebas con usuarios.

## Alcance y límites de esta versión

- Identidad visual basada en la guía de Nagora y la paleta Salud. Se conserva el claim del encargo y Lato con fuente de sistema de respaldo. El isotipo visible es temporal.
- Cada cuenta tiene un espacio personal. Los equipos, múltiples consultorios, perfiles profesionales estructurados, convenios con tarifas por prestación y liquidaciones que distribuyen un pago entre múltiples honorarios requieren ampliar el modelo. Hoy se admite una liquidación consolidada como un solo ingreso. Los datos pactados del convenio son texto.
- Recuperación por código de un solo uso generado desde Perfil. Quien perdió su contraseña necesita un código emitido previamente. No hay envío de correo ni proveedor externo de identidad.
- La edición corrige el movimiento. Para corregir un pago ya asentado en esta versión se anula el movimiento completo y se registra de nuevo. No existe reversión individual de pagos ni deshacer inmediato.
- El calendario admite vencimientos y recordatorios internos. Los impuestos se registran como gastos. No se calculan tributos ni se envían avisos externos. ARCA, bancos y billeteras quedan para una fase posterior.
- El servidor incluido se entrega para ejecución local. Para operación comercial quedan pendientes infraestructura de producción, limitación de intentos, verificación de correo, políticas de retención, backups automáticos con restauración ensayada y revisión de seguridad. SQLite permite respaldo consistente con su API de backup. Un despliegue de mayor concurrencia puede migrar a PostgreSQL conservando el contrato de dominio.

## Respaldo y entorno Windows

En Windows, instalar `tzdata` en un entorno virtual si no hay base IANA disponible:
`python -m pip install tzdata`. No reemplazar la zona argentina por la del equipo.

La propuesta de endurecimiento agrega límites persistentes de acceso y recuperación
con código de un uso que vence en 30 días. Los códigos previos sin vencimiento
se invalidan al migrar; regenerarlos desde Perfil antes de depender de ellos.

Ver [respaldo horario, retención de 30 días y restauración](docs/BACKUP_RESTORE.md).
El ejecutor está implementado; falta activarlo en infraestructura con destino
externo cifrado, alertas y ensayo de recuperación. No implica producción lista.
