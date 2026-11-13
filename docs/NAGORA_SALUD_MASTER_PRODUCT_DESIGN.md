# NAGORA SALUD — Master de producto, diferenciación y diseño

**Versión:** 1.0 · **Estado:** norma rectora para diseño, desarrollo y QA · **Mercado inicial:** Argentina

> **Promesa:** «Entendé cuánto ganás, cuánto te falta cobrar y cuánto te va a quedar; sin planillas ni complicaciones».

## 1. Propósito y límites
Nagora Salud ayuda a profesionales independientes de salud (30+ años, especialmente con baja familiaridad digital) a gestionar la economía de su actividad y una cartera administrativa de pacientes/clientes. No es un sistema clínico. No administra historias clínicas, diagnósticos, tratamientos, recetas ni resultados de estudios. Tampoco reemplaza asesoramiento contable, tributario o profesional.

**Resultado principal:** en menos de un minuto, la persona debe entender cuánto cobró, cuánto espera cobrar, qué gastos tiene y cuál es su resultado proyectado al cierre del mes, con incertidumbre visible.

**Principio de producto:** primero resolver; después explicar. Cada pantalla debe responder una pregunta concreta y proponer una acción clara.

## 2. Diferenciación irrenunciable
1. **Del registro a la decisión:** no solo guarda operaciones; señala qué cobro revisar o qué gasto registrar hoy.
2. **Lenguaje humano:** «Te falta cobrar» en vez de «Cuentas por cobrar»; «Lo que te quedaría» en vez de «EBITDA».
3. **Realidad argentina de salud:** particulares, obras sociales, prepagas, instituciones, copagos cuando correspondan, aranceles, retenciones, débitos, comisiones, honorarios, matrícula, monotributo y alquiler/fee de consultorio.
4. **Proyección explicable:** distingue efectivo recibido, honorarios devengados y pagos esperados. Nunca presenta estimaciones como certezas.
5. **Cartera respetuosa:** contacto administrativo y comunicaciones consentidas, sin presión comercial ni explotación de información clínica.
6. **Interfaz serena:** pocos números, sin dashboards saturados, sin gráficos decorativos ni múltiples CTA compitiendo.
7. **Valor desde el primer uso:** puede empezar con un ingreso y un gasto, sin configurar toda la contabilidad.

## 3. Persona y contextos de uso
- Profesional mayor de 30 años, autónomo o con práctica mixta; puede trabajar en varios consultorios, instituciones o modalidades.
- Puede cobrar directamente de pacientes o por intermediarios, con liquidaciones diferidas, comisiones y descuentos.
- Usa celular, dispone de poco tiempo, teme equivocarse y no domina Excel ni sistemas de gestión.
- No debe conocer términos financieros ni configurar reglas complejas para obtener valor.
- Debe poder corregir datos sin miedo y saber qué cambió.

**Jobs to be done:** «¿Cuánto dinero me queda este mes?», «¿Quién me debe?», «¿Por qué cobré menos?», «¿Qué tengo que pagar?», «¿Puedo afrontar los gastos del mes que viene?», «¿Cómo puedo mejorar mi ingreso sin afectar la atención?».

## 4. Reglas UX/UI obligatorias
### 4.1 Pantallas
- Una pregunta principal y **una acción primaria** por pantalla; acciones secundarias discretas.
- Home: como máximo **tres cifras protagonistas**: Cobrado, Por cobrar, Te quedaría al cierre. Mostrar período y acceso a desglose.
- No más de 3–5 opciones visibles por bloque. Revelar detalles progresivamente.
- Sin menú extenso: navegación primaria pequeña (Inicio, Movimientos, Personas, Más), revisable en tests.
- Texto corto, cotidiano, positivo, concreto. No jerga técnica sin explicación.
- Mostrar estados vacíos útiles: «Todavía no registraste cobros. Empezá con uno».
- No usar gráficos si una frase o número resuelve mejor la necesidad.
- No usar modales encadenados, banners invasivos, confeti, urgencia artificial ni notificaciones excesivas.
- Respetar manual de marca Nagora (Lato, paleta y símbolo); adaptar a salud con serenidad, **sin inventar colores oficiales**. Verificar contraste WCAG 2.2 AA.
- Mobile-first, objetivos táctiles cómodos, tipografía legible, foco visible, navegación por teclado, lectores de pantalla, errores asociados a campos, soporte de zoom 200%.
- Velocidad: pantallas rápidas en redes móviles modestas; carga diferida, estados de espera comprensibles, sin animaciones pesadas.

### 4.2 Formularios y acciones
- Registro de ingreso en máximo tres pasos lógicos: **qué fue → cuánto y quién paga → cuándo esperás cobrar**. Permitir completar luego datos opcionales.
- Campos con ejemplos argentinos y valores sugeridos editables; nunca inventar importes.
- Confirmación clara al guardar; deshacer/corregir; evitar pérdida de datos.
- Validación inmediata amable: «Revisá el importe: no puede ser negativo».
- No exigir nombre del paciente para registrar una prestación; permitir operación anónima o agregada.
- Siempre explicar consecuencias antes de eliminar, enviar mensajes o modificar pagos.
- Si hay voz, pedir revisión y confirmación explícita antes de guardar; alternativa manual equivalente.

### 4.3 Tono y microcopy
**Personalidad:** optimista, resolutiva, cálida, respetuosa, sin infantilizar.
- Sí: «Bien, ya registraste este cobro»; «Hay 2 pagos para revisar»; «Si se cumplen los cobros previstos, te quedarían $…».
- No: «¡Estás perdiendo plata!»; «Debés optimizar tu funnel»; «Error fatal»; «Tus pacientes inactivos son oportunidades».
- No felicitar por facturar más a costa de procedimientos innecesarios.
- Ante incertidumbre: «Todavía no sabemos cuándo se acreditará este pago».

## 5. Modelo financiero: reglas no negociables
### 5.1 Conceptos separados
- **Prestación realizada:** trabajo facturable; no implica factura emitida ni cobro recibido.
- **Importe bruto esperado:** valor acordado antes de descuentos.
- **Descuentos y débitos:** aranceles, glosas, retenciones, comisiones, honorarios institucionales u otros, con tipo, origen y fecha.
- **Neto esperado:** bruto menos descuentos aplicables; no mezclar con dinero acreditado.
- **Cobro real:** dinero efectivamente recibido, con fecha y medio de cobro.
- **Saldo pendiente:** neto exigible menos cobros aplicados, ajustado por notas y diferencias justificadas.
- **Gasto:** obligación o egreso vinculado a actividad, distinguido entre previsto y pagado.
- **Resultado operativo estimado:** ingresos netos estimados del período menos gastos atribuibles; **no equivale al saldo de caja**.
- **Caja proyectada:** saldo inicial + cobros esperados en el período − pagos esperados; mostrar supuestos y faltantes.

### 5.2 Proyección al cierre
Mostrar separadamente:
1. **Ya cobraste:** acreditaciones confirmadas del mes.
2. **Esperás cobrar:** pagos pendientes con fecha estimada dentro del mes.
3. **Vas a pagar / ya pagaste:** egresos del mes (sin duplicarlos).
4. **Te quedaría:** caja proyectada, con fórmula y supuestos accesibles.

Cada estimación debe incluir fecha de actualización y grado de certeza (Confirmado, Estimado, Sin fecha). Si faltan datos, mostrar «Proyección incompleta» y la acción más útil para completarla. No mezclar cobros de otros meses con honorarios del mes sin etiquetar la diferencia.

### 5.3 Reglas argentinas configurables
- Pagadores: particular, obra social, prepaga, clínica, consultorio, institución y otros.
- Contratos/planes por pagador, **vigencia** y modalidad de prestación; nomenclador y arancel si el usuario los conoce.
- Demoras típicas de liquidación configurables, nunca presentadas como plazos universales.
- Deducciones: porcentaje, monto fijo, combinaciones, topes y reglas por convenio; evitar doble descuento.
- Diferenciar débito/glosa, retención tributaria, comisión del intermediario y copago.
- Gastos recurrentes: monotributo (categoría e importe ingresado o fuente actualizada), matrícula/colegio profesional, seguro, alquiler, fee de clínica, servicios, insumos, contador, software y otros.
- Monotributo, ARCA, facturación y reglas de convenios cambian: **no codificar tasas, categorías o aranceles como constantes permanentes**. Requieren fuente, fecha de vigencia y revisión especializada.
- Moneda ARS por defecto, formato argentino; si hay múltiples monedas, no sumar sin tipo de cambio identificado.
- Evitar redondeos silenciosos; usar aritmética decimal exacta, trazabilidad y pruebas de casos límite.

## 6. Cartera de pacientes/clientes (administrativa, no clínica)
Datos mínimos opcionales: nombre/alias, contacto, consentimiento y preferencias de contacto, pagador asociado, estado administrativo de cobros y últimas interacciones administrativas. Evitar diagnóstico, motivo de consulta, evolución, especialidad clínica individual, medicación, historia o notas clínicas libres. No incluir campos libres que inviten a cargar información de salud.

- Distinguir paciente, pagador y entidad contratante.
- Permitir búsqueda, duplicados, edición, exportación y eliminación conforme políticas aplicables.
- Registrar origen del consentimiento, canal permitido y fecha; revocación fácil.
- Acceso por roles y aislamiento estricto entre profesionales/consultorios.

## 7. Marketing ético y mejora de ingresos
**Regla superior:** bienestar, autonomía y confianza del paciente prevalecen sobre facturación.

### Permitido, sujeto a consentimiento y normativa aplicable
- Recordatorios administrativos de pagos o turnos cuando se incorpore agenda externa, sin detalles clínicos.
- Información sobre canales de contacto, horarios, modalidades y cobertura aceptada.
- Mensajes educativos generales, sobrios y opt-in, revisados por el profesional.
- Sugerir mejoras operativas: reclamar liquidaciones vencidas, revisar débitos, reducir ausentismo con comunicaciones apropiadas, evaluar costo de consultorio, corregir honorarios contractuales, identificar gastos innecesarios.
- Ayudar a detectar concentración de ingresos en un pagador y retrasos recurrentes.

### Prohibido
- Sugerir consultas, tratamientos, estudios o frecuencia de atención para elevar ingresos sin justificación clínica.
- Segmentar campañas por diagnósticos, vulnerabilidades, condiciones de salud o inferencias sensibles.
- Mensajería masiva sin consentimiento; presión, culpa, urgencia artificial, promesas de resultados clínicos o testimonios no autorizados.
- Compartir datos de pacientes con plataformas publicitarias o modelos externos sin base legal y controles apropiados.
- Envíos automáticos de marketing sin aprobación del profesional y posibilidad de baja.

**Toda recomendación debe explicar:** oportunidad, fundamento, beneficio estimado (si existe evidencia), impacto potencial en pacientes, y acción reversible. Nunca prometer aumento de ingresos.

## 8. Privacidad, seguridad y cumplimiento
- Diseñar para minimizar datos personales; información de salud es especialmente sensible. Aplicar normativa argentina de protección de datos personales y reglas profesionales pertinentes; validar con asesoría legal antes del lanzamiento.
- Autenticación segura, permisos por usuario/organización, cifrado en tránsito, gestión segura de secretos, respaldos y recuperación.
- Registro auditable de cambios financieros, sin exponer datos personales innecesarios en logs.
- Política de retención y eliminación; exportación de datos; consentimiento y transparencia de comunicaciones.
- No enviar información personal a servicios de IA por defecto. Cualquier función de IA requiere evaluación de proveedor, base legal, minimización y controles.
- Separar entornos de desarrollo/pruebas/producción; datos ficticios en pruebas.
- Revisión de amenazas y pruebas automatizadas antes de cada release.

## 9. Experiencias mínimas del MVP
1. Alta simple de cuenta y configuración básica de actividad.
2. Registro de prestación/ingreso esperado (particular o institución).
3. Registro de cobro total/parcial y conciliación de diferencias.
4. Gestión de pagadores, planes y descuentos configurables.
5. Registro de gastos, incluidos recurrentes.
6. Inicio con tres cifras, alertas útiles y proyección explicable.
7. Cartera administrativa mínima con consentimiento para contactos.
8. Exportación y corrección de movimientos.
9. Seguridad, persistencia, auditoría y pruebas.

**Fuera del MVP por defecto:** historia clínica, recetas, turnero clínico completo, integración ARCA no validada, campañas automáticas, IA por voz, recomendaciones comerciales basadas en datos sensibles, analítica compleja. Repriorizar con entrevistas.

## 10. Evidencia de discovery y decisiones
Encuesta exploratoria inicial (n=10; noviembre 2026): 6 reportaron revisar varias fuentes para calcular ingresos, 5 dificultades para identificar gastos, 4 demoras en pagos y 3 diferencias en liquidaciones. Ocho indicaron recibir al menos parte de sus honorarios de obras sociales/prepagas/instituciones. **No generalizar estos porcentajes al mercado.**

**Hipótesis por validar en entrevistas:** la principal ventaja será reducir la incertidumbre del ingreso neto mensual y el esfuerzo de seguimiento, no agregar más funciones contables. Investigar métodos actuales, excepciones por especialidad, términos comprensibles, disposición a pagar y confianza en proyecciones.

## 11. Criterios de aceptación transversales para CADA tarea de Codex
Una funcionalidad **NO está terminada** si falla cualquiera de estos puntos:

- [ ] Resuelve una necesidad real y describe el resultado esperado en lenguaje de usuario.
- [ ] Una acción primaria por pantalla; información esencial visible sin saturación.
- [ ] Mobile-first, legible, accesible y usable sin conocimiento técnico.
- [ ] Tono amable, concreto, optimista, sin culpabilizar ni infantilizar.
- [ ] Datos persistidos; estados vacío, cargando, error y éxito implementados.
- [ ] Validaciones, edición, prevención de duplicados y corrección de errores.
- [ ] Cálculos monetarios exactos, supuestos visibles y pruebas de casos límite.
- [ ] Cobrado, esperado, facturado, gasto y caja no se confunden.
- [ ] Se respeta la realidad de pagadores, descuentos y gastos argentinos cuando aplique.
- [ ] No recoge ni expone datos clínicos ni habilita marketing invasivo.
- [ ] Permisos, privacidad, seguridad y aislamiento entre cuentas comprobados.
- [ ] Tests unitarios/integración y recorrido de usuario pasan en CI.
- [ ] No introduce dependencias pagas ni llamadas a APIs de IA sin aprobación.
- [ ] Documentación y decisiones técnicas actualizadas.
- [ ] Cambio entregado en Pull Request, sin despliegue productivo sin aprobación.

## 12. Instrucción permanente para agentes / Codex
> Antes de diseñar o implementar, leé este archivo y el manual de marca. Si una solicitud contradice estas reglas, detenete, explicá el conflicto y proponé una alternativa. Priorizá claridad, utilidad inmediata, confianza financiera, privacidad y bienestar del paciente sobre cantidad de funcionalidades. No inventes normativas, tasas, aranceles, datos clínicos ni resultados. Cada PR debe incluir: problema del usuario, solución, capturas mobile/desktop, casos de prueba, riesgos, impacto en cálculos, seguridad y checklist de este documento. Ante incertidumbre de negocio, creá una pregunta para Product Owner en lugar de asumir.

## 13. Métricas de producto (sin incentivos clínicos perversos)
- Tiempo hasta registrar primer ingreso y primer gasto.
- Porcentaje de usuarios que comprenden correctamente la proyección en prueba de usabilidad.
- Tasa de finalización de tareas sin ayuda y errores de registro.
- Porcentaje de cobros conciliados y diferencia entre proyección y caja real.
- Tiempo administrativo ahorrado declarado y confianza en la información.
- Tasa de revocación de consentimiento y quejas por comunicaciones.
- **Nunca:** cantidad de tratamientos indicados por paciente como KPI de crecimiento.

## 14. Gobierno de cambios
Este documento es fuente rectora. Cambios requieren: motivo, evidencia (entrevista, prueba o necesidad legal), impacto UX/finanzas/privacidad, decisión de Product Owner y versión. Si hay conflicto con un prompt aislado, prevalece este master hasta aprobación explícita.
