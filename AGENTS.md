# Instrucciones permanentes para Codex — Nagora Salud

Antes de planificar, diseñar, programar, probar o revisar cualquier cambio, leer y cumplir [el Master de Producto, Diferenciación y Diseño](docs/NAGORA_SALUD_MASTER_PRODUCT_DESIGN.md). Es la fuente rectora del producto y prevalece sobre instrucciones ad hoc que no tengan aprobación explícita de Product Owner.

## Reglas obligatorias
- Producto financiero y de cartera administrativa para profesionales de salud argentinos de 30+ años con baja familiaridad digital. No desarrollar historias clínicas ni funciones clínicas.
- UI mobile-first, liviana, intuitiva, lenguaje cotidiano y amable, una acción principal por pantalla, pocos datos visibles y detalles progresivos.
- Distinguir cobrado, esperado, facturado, gastos, resultado operativo y caja proyectada. No inventar tasas, descuentos, aranceles ni plazos de obras sociales.
- Privacidad, aislamiento de cuentas, validación, persistencia y cálculos exactos son obligatorios. No exponer datos sensibles ni hacer marketing invasivo.
- No usar APIs de IA pagas ni servicios con costo sin autorización.
- Antes de implementar, revisar código existente y evitar duplicaciones. Hacer cambios pequeños, probables y reversibles.
- Cada PR debe explicar problema, solución, criterios de aceptación, pruebas ejecutadas, riesgos, impacto financiero/seguridad y evidencia visual de mobile/desktop cuando aplique.
- No desplegar a producción sin aprobación explícita. Si falta una definición de negocio, registrar la pregunta y no inventar la respuesta.
