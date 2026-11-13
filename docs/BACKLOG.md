# Backlog de Nagora Salud

Fuente de verdad: [GitHub Issues](https://github.com/anaesposito/nagora-salud/issues).

## Vistas por prioridad
- [P0 — bloqueantes](https://github.com/anaesposito/nagora-salud/issues?q=is%3Aissue+is%3Aopen+in%3Atitle+P0)
- [P1 — MVP](https://github.com/anaesposito/nagora-salud/issues?q=is%3Aissue+is%3Aopen+in%3Atitle+P1)
- [P2 — evolución](https://github.com/anaesposito/nagora-salud/issues?q=is%3Aissue+is%3Aopen+in%3Atitle+P2)
- [Cerrados](https://github.com/anaesposito/nagora-salud/issues?q=is%3Aissue+is%3Aclosed)

## Flujo acordado
Backlog → Listo → En desarrollo → En QA → Terminado.

**Nota:** este flujo es la definición operativa. El tablero GitHub Projects aún NO está creado, por falta de acción de creación de Projects en la integración disponible. No confundir vistas filtradas de Issues con Kanban.

## Reglas de trabajo
1. Cada cambio se vincula a un Issue.
2. Máximo dos tareas en desarrollo simultáneamente.
3. El PR describe alcance, tests, riesgos y evidencia visual.
4. QA valida móvil y escritorio en la aplicación real.
5. Solo cerrar un Issue tras validar criterios de aceptación y obtener aprobación.
6. No desplegar a producción sin aprobación explícita.

## Incidencias detectadas en pruebas de usuario
- [#36 — P0 Recuperación de contraseña por email y mensajes claros de registro](https://github.com/anaesposito/nagora-salud/issues/36): el flujo actual exige un código previamente generado, no permite solicitarlo por correo y confunde errores de integridad con registros duplicados. Pendiente de implementación; vinculado con #13 y #2.

## Seguridad y cumplimiento legal argentino — Bloqueante para usuarios reales
- [#37 — EPIC P0 Seguridad, privacidad y cumplimiento legal argentino](https://github.com/anaesposito/nagora-salud/issues/37).
- [#38 — P0 Seguridad de aplicación, autenticación y aislamiento](https://github.com/anaesposito/nagora-salud/issues/38).
- [#39 — P0 Privacidad, Ley 25.326 y evaluación de obligaciones AAIP](https://github.com/anaesposito/nagora-salud/issues/39).
- [#40 — P0 Backups, retención, incidentes y proveedores cloud](https://github.com/anaesposito/nagora-salud/issues/40).
- [#41 — P1 Términos comerciales y alcance ARCA/regulatorio](https://github.com/anaesposito/nagora-salud/issues/41).

**Gate de lanzamiento:** mantener la demo pública solo con datos ficticios. No habilitar cuentas reales ni información financiera real sin controles P0 verificados y revisión jurídica argentina. La verificación técnica no equivale a certificación legal.

## Orden sugerido de ejecución
1. #2 QA visual y funcional; #3 navegación/Home.
2. #11 CI; #12 accesibilidad.
3. #4 proyección de cierre; #20 auditoría de cálculos.
4. #5 seguridad y entorno; #13 autenticación; #14 backups.
5. #6–#10 y #15–#21 funcionalidad MVP.
6. #22–#26 evolución.

## Configuración pendiente de GitHub Projects
Crear un Project en la cuenta propietaria del repositorio con vista Board y columnas Backlog, Listo, En desarrollo, En QA y Terminado. Agregar los Issues #2–#26. El enlace definitivo se genera al crear ese Project; no inventar URL.
