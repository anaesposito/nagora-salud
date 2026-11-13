# Ejecución del backlog — Nagora Salud

Actualizado: 2026-11-13. Este documento es un tablero provisional **hasta vincular los Issues en GitHub Projects**. No representa pruebas ejecutadas ni tareas completadas.

## Columnas de GitHub Projects
Backlog → Por hacer → En curso → En revisión → Hecho. No cerrar Issues sin evidencia de pruebas y aprobación de Product Owner.

## Primer bloque de ejecución
| Orden | Issue | Estado propuesto | Evidencia / siguiente paso |
|---|---|---|---|
| 1 | #11 CI: tests automáticos y JavaScript | En revisión | Ya existe `.github/workflows/ci.yml` con tests Python y chequeo JS; verificar ejecuciones de Actions y protección de rama antes de cerrar |
| 2 | #5 Seguridad y entorno de pruebas | Por hacer | Revisar amenazas, configuración, aislamiento de cuentas y exposición pública |
| 3 | #13 Autenticación y recuperación | Por hacer | Verificar límites de intentos, recuperación sin enumeración y expiración |
| 4 | #14 Backups y restauración | Por hacer | Definir RPO/RTO, respaldo automático y ensayo de recuperación |
| 5 | #2 QA visual y funcional móvil | Por hacer | Probar anchos 320/375/768/desktop, flujos y capturas |
| 6 | #3 Simplificar navegación y Home | Por hacer | Aplicar criterios de baja alfabetización digital y reducir espacios vacíos |
| 7 | #12 Accesibilidad WCAG 2.2 AA | Por hacer | Teclado, foco, contraste, zoom, errores y lector de pantalla |
| 8 | #4 Proyección explicable de cierre mensual | Por hacer | Verificar fórmulas y trazabilidad de estimaciones |

## Segundo bloque: exactitud financiera y adopción
#6 ingresos y cobros parciales; #7 gastos y recurrencias; #8 liquidaciones; #9 corrección de pagos; #10 exportación; #15 onboarding; #16 cartera administrativa; #17 convenios; #18 conciliación múltiple; #19 errores y estados vacíos; #20 auditoría de cálculos; #21 pruebas con profesionales.

## Tercer bloque: evolutivos
#22 voz; #23 ARCA; #24 recordatorios; #25 reportes; #26 escalabilidad.

## Definition of Done
- Código/PR enlazado al Issue y revisado.
- Tests automatizados ejecutados y resultado registrado.
- QA manual mobile y desktop con evidencia cuando corresponda.
- Exactitud de importes y aislamiento de cuentas comprobados.
- Privacidad, accesibilidad y regresiones revisadas.
- Aprobación explícita del Product Owner para cerrar.

## Pendientes de infraestructura del tablero
- Crear o localizar GitHub Project y agregar los 25 Issues.
- Configurar vistas Kanban por estado y filtros P0/P1/P2.
- Verificar estado real de cada Issue contra código, Actions y despliegue antes de mover a Hecho.
