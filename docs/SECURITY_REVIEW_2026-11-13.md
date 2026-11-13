# Auditoría de seguridad y validación — 13/11/2026

Base revisada: `01251b21f62330ba3a1278fa142e34e0037cfcb3`.
Cambios propuestos en rama `fix/security-backup-audit-20261113`; sin despliegue.

## Implementación y evidencia

- Límite persistente compartido por login, registro y recuperación: 20 solicitudes
  por identificador de cuenta y 100 por dirección de conexión en 15 minutos.
  Incluye intentos exitosos; responde 429 antes del hash costoso. Contadores en una
  transacción separada sobreviven al rollback de credenciales inválidas. Se prueban
  concurrencia, normalización y reapertura de ventana. No confía en X-Forwarded-For.
- Recuperación: un uso, reemplazo, 30 días, revocación de sesiones tras restablecer.
  Migración repetible invalida códigos antiguos sin fecha. Comunicar este cambio
  antes de aplicar sobre cuentas existentes; regenerarlos desde Perfil.
- Logs de solicitudes sin URL ni query string. No registrar cuerpos ni credenciales.
- Cierre explícito de conexión al inicializar SQLite y en pruebas (compatibilidad Windows).
- Backup consistente, integridad, restauración en archivo nuevo y revocación de
  credenciales restauradas: ver [procedimiento](BACKUP_RESTORE.md).

Pruebas locales Windows/Python 3.12: 15 tests de aplicación, seguridad, restauración
y límites monetarios, todos satisfactorios. Con las tres pruebas del PR #33:
18 satisfactorios. `node --check static/app.js`: satisfactorio.
Windows requiere `tzdata` si no dispone de base IANA; se instaló en entorno aislado.

PR #33 (`f8b11b6737fb89fdc1fe891c748832dbc340ba4d`): revisado; prueba headers públicos
y rechazo de POST sin Origin o desde otro origen. No prueba por sí solo aislamiento,
expiración, límites ni recuperación. CI [43510589605](https://github.com/anaesposito/nagora-salud/actions/runs/43510589605)
y visual [43510589482](https://github.com/anaesposito/nagora-salud/actions/runs/43510589482)
terminaron en success. Se conserva borrador y no se hizo merge.

## Límites que bloquean la salida comercial

- Proxy: el límite por dirección puede agrupar usuarios detrás del mismo proxy;
  configurar protección en el ingreso y validar confianza del proxy antes de escalar.
  La solución no reemplaza protección DDoS ni un servidor HTTP endurecido.
- No hay verificación de correo ni recuperación sin código previamente emitido.
  El registro de correo duplicado sigue diferenciándose; resolver el flujo de
  verificación antes de prometer resistencia completa a enumeración.
- Falta política aprobada de retención/eliminación, respaldo remoto programado,
  cifrado y ensayo RPO/RTO. No se accedió a bases reales.
- Consulta de protección de main devolvió 403, `Resource not accessible by integration`.
  CI verde no demuestra que los merges estén bloqueados si falla.
- GitHub Projects no tiene acciones disponibles en el conector. Acceso al navegador
  venció esperando autorización; tablero y vinculación sin verificar.
- WCAG 2.2 AA, lector de pantalla, dispositivos físicos y usabilidad con profesionales
  requieren validación adicional. No se declara conformidad ni producción lista.
