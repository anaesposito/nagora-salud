# Respaldo y recuperación

Herramienta local: `python backup.py backup origen.sqlite copia-nueva.sqlite`.
Usa la API de SQLite (incluye transacciones confirmadas en WAL), verifica integridad
y claves foráneas y rechaza destinos existentes. No copiar únicamente el archivo
principal mientras la aplicación está activa. La copia contiene datos privados:
guardarla fuera del repositorio y del directorio público, con permisos restringidos
y cifrado del disco/almacenamiento. En Windows verificar ACL del directorio;
los permisos POSIX no sustituyen ese control.

## Restauración ensayada

1. Detener el servicio de destino. Conservar la base anterior para rollback.
2. Ejecutar `python backup.py restore copia.sqlite restaurada-nueva.sqlite`.
3. La restauración verifica integridad y relaciones, y elimina sesiones y códigos
   de recuperación para no resucitar credenciales revocadas desde el respaldo.
4. Iniciar el servidor apuntando `NAGORA_DB` al archivo restaurado; comprobar login,
   cuentas, movimientos, pagos, ajustes y totales. Regenerar códigos de recuperación.
5. Medir duración y pérdida de datos respecto del último respaldo verificado.

Prueba automatizada: `test_restore_preserves_finances_and_revokes_credentials`
restaura una base ficticia y comprueba centavos, sesiones y códigos. También se
comprueba rechazo de sobrescritura y eliminación de una copia corrupta fallida.
Esto no constituye un ensayo sobre infraestructura productiva.

## Automatización y decisiones pendientes

El comando puede ejecutarse desde el programador del servidor con un nombre nuevo
por ejecución. Todavía NO se configuró ningún cron ni almacenamiento externo.
Antes de habilitar producción deben acordarse y probarse: frecuencia (RPO), tiempo
de restauración (RTO), destino externo cifrado, retención y eliminación, responsables,
alertas por fallos y revisión de ACL. No se eliminan respaldos automáticamente sin
una política aprobada. Una copia en el mismo disco no protege ante pérdida del host.
