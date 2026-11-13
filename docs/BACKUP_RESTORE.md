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

## Automatización horaria y retención

Product Owner eligió el 13/11/2026 respaldo cada hora y retención de 30 días.
Ejecutor: `python backup_worker.py origen.sqlite directorio-protegido --loop`.
Sin `--loop` ejecuta una vez y puede usarse con un programador horario externo.
Tras generar una copia verificada elimina solo archivos propios con el patrón
estricto generado por el ejecutor, mayores a 30 días. No recorre subdirectorios,
no sigue enlaces y nunca elimina el origen. Si falla la copia, no rota respaldos
y finaliza con código 1 para alertar al supervisor.

Todavía NO se activó el proceso en un alojamiento ni se configuró almacenamiento
externo. El RPO objetivo es una hora mientras el ejecutor opere correctamente;
no es un RPO medido ni garantizado. Faltan RTO, destino externo cifrado,
responsables, alertas por fallo/ausencia de copia y revisión de ACL. Una copia
en el mismo disco no protege ante pérdida del host. El supervisor debe reiniciar
el ejecutor y avisar ante fallos; no ocultar una cadena de fallos con reinicios.
