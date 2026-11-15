# Verificación de correcciones y reversiones — PR #42

La corrección cambia importe y fecha de un cobro individual, conserva el original y exige motivo. La reversión requiere una confirmación separada y devuelve el importe a pendiente. No elimina la prestación ni modifica otros cobros.

## Evidencia técnica

- 14 pruebas Python: centavos, saldos, fechas, aislamiento de cuentas, sesión vencida, concurrencia, idempotencia, migración y rollback.
- Navegador Chromium a 320, 375, 768 y 1280 px: motivo obligatorio, cancelación sin escritura, error de conexión con formulario conservado, reintento, corrección, reversión, historial y persistencia tras recargar.
- El error de conexión no asegura que el servidor haya rechazado la operación: invita a reintentar con la misma clave idempotente, sin duplicar cambios.
- Revisión visual de capturas móviles y escritorio con datos ficticios. Capturas reproducibles en `artifacts/visual/issue-9-*`, adjuntas por CI.
- Cierre explícito de la conexión SQLite de una prueba para permitir eliminar la base temporal en Windows.

Ejecución local: `python -m unittest -q` y `python tests/run_payment_revision_local.py` (Playwright y Chromium instalados; tzdata en Windows). El navegador usa una base temporal, sin credenciales ni datos reales.

## Validación de uso y aprobación

La prueba con una persona no técnica no se sustituye por tests automáticos ni se declara realizada sin observarla. Recorrido de aceptación propuesto, en la demo:

1. En Ingresos, abrir «Liquidación con pago parcial» y modificar el cobro de $300.000 a $299.999,99, con un motivo.
2. Verificar que falta cobrar un centavo más y que el historial conserva el cobro original.
3. Abrir «Revertir cobro» y volver al detalle sin confirmar: nada debe cambiar.
4. Volver a revertir, indicar motivo y confirmar: el saldo vuelve a pendiente; el historial sigue visible después de recargar.

Registrar si la persona encuentra las acciones sin ayuda y entiende que revertir corrige el registro, no devuelve dinero por el banco. Si hay confusión, corregirla antes de aprobar. Esta observación y la aprobación de producto siguen siendo pasos humanos explícitos; no se fusiona, despliega ni cierra #9 automáticamente.

## Compatibilidad

El PR #43 se apila sobre #42 y prueba las correcciones individuales dentro de liquidaciones. Después de actualizar #42, integrar sus cambios en la rama de #43 y ejecutar nuevamente sus controles. Los PR #34 y #35 siguen siendo propuestas separadas; si cambian main antes de integrar, reconciliar y repetir las pruebas.
