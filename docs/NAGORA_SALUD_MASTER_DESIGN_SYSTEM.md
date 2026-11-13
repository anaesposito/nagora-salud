# NAGORA SALUD — Master Design System

**Versión:** 1.1 · **Estado:** especificación normativa con paleta y tipografía documentadas; componentes pendientes de auditoría en código · **Aplicación:** web responsive/mobile-first

**Documentos rectores:** [Master de Producto](NAGORA_SALUD_MASTER_PRODUCT_DESIGN.md) y manual de marca Nagora. Si hay conflicto, detener la implementación y pedir decisión de Product Owner. **No inventar valores de marca.**

## 1. Filosofía y criterios de diferenciación
**Calma visual + claridad financiera + acción concreta.** El usuario es un profesional de salud de 30+ años que puede no conocer software administrativo. La interfaz debe transmitir control, no complejidad ni ansiedad. Nagora Salud no es un HIS/EMR: nunca pedir diagnósticos, tratamientos ni historia clínica.

**Cinco invariantes:** (1) una acción primaria por pantalla, (2) máximo tres cifras protagonistas en Inicio, (3) información adicional bajo demanda, (4) texto cotidiano y amable, (5) ningún dato financiero estimado se presenta como confirmado.

## 2. Fuente de verdad y tokens
La guía de identidad Nagora recuperada indica **Aptos Display Semibold para títulos y Aptos Regular para interfaz**; Inter y sans-serif del sistema son alternativas. Esto corrige la referencia previa a Lato, que no coincide con esa guía. Antes de cerrar la implementación, contrastar con el archivo original del manual si hay versiones posteriores. La paleta oficial documentada es: teal oscuro #267B7E, teal principal #3A9898, menta #8ADCAE, blanco cálido #F8F7F2 y coral #F08A78. Iconografía: línea redondeada de 2 px. Grilla: 8 px; ritmo principal: 24–32 px. El logo conserva proporciones originales, sin efectos inventados.

### 2.1 Tokens ejecutables — propuesta de implementación
Los **cinco colores de marca** provienen de la guía. Los colores de texto, bordes, superficies y radios adicionales son **tokens funcionales propuestos**, no colores oficiales nuevos. Validar contraste de cada combinación y estados antes de publicar.

```css
:root {
  --brand-teal-dark: #267B7E;
  --brand-teal: #3A9898;
  --brand-mint: #8ADCAE;
  --brand-warm-white: #F8F7F2;
  --brand-coral: #F08A78;
  --font-body: "Aptos", "Inter", system-ui, sans-serif;
  --font-heading: "Aptos Display", "Aptos", "Inter", system-ui, sans-serif;
  --color-bg: var(--brand-warm-white);
  --color-surface: #FFFFFF;
  --color-text: #19383A;
  --color-text-muted: #405A5B;
  --color-border: #D5DFDA;
  --color-primary: var(--brand-teal-dark);
  --color-on-primary: #FFFFFF;
  --color-focus: #19383A;
  --color-positive-bg: #E5F7EC;
  --color-warning-bg: #FFF2E8;
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}
```

**Regla de contraste:** el teal principal #3A9898 es un color de marca, pero no se presupone que funcione con texto blanco pequeño. Para botones con texto blanco, usar teal oscuro #267B7E solo tras comprobar contraste; mantener estados hover/focus/disabled igualmente accesibles. Menta y coral son acentos, no colores predeterminados de texto sobre blanco. Nunca depender solo del color para indicar estado.

**Fuentes:** usar Aptos únicamente si hay licencia/disponibilidad válida en el entorno; no subir archivos de fuentes sin autorización. Fallback Inter/system-ui. No descargar ni distribuir fuentes propietarias desde Codex.

### 2.2 Jerarquía tipográfica propuesta
- Título de pantalla: 24–28px, peso 700, interlineado 1.2.
- Título de bloque: 18–20px, peso 700.
- Cuerpo: 16–18px, peso 400/500, interlineado >=1.45.
- Ayuda/metadata: 14–16px, nunca como único texto indispensable.
- Cifra protagonista: 28–36px, con etiqueta y período. Usar números tabulares para montos.
- No usar mayúsculas sostenidas para instrucciones, no comprimir texto para que entre.

### 2.3 Accesibilidad
Objetivo WCAG 2.2 AA: contraste texto normal >=4.5:1; texto grande >=3:1; foco visible; teclado completo; etiquetas explícitas; estados anunciados a tecnologías asistivas; zoom 200%; objetivos táctiles de preferencia >=44×44 CSS px; sin información transmitida únicamente por color o posición. Validar en navegador real y lectores de pantalla.

## 3. Layout y navegación
- Mobile-first; una columna para formularios y tareas principales. Desktop: ancho de lectura acotado, sin llenar espacio con widgets.
- Cabecera: título que responda «¿Dónde estoy?» y contexto temporal cuando corresponda.
- Navegación primaria propuesta: **Inicio · Movimientos · Personas · Más**. No añadir pestañas por cada tipo de cobro; usar filtros progresivos.
- Inicio: «Este mes», **Ya cobraste**, **Te falta cobrar**, **Te quedaría al cierre**; una CTA contextual «Registrar movimiento» o «Revisar cobros». Detalle de fórmula mediante «Cómo se calcula».
- Espacio en blanco intencional, agrupación clara, separadores suaves. Evitar tablas extensas, múltiples columnas de métricas, carruseles automáticos, banners y gráficos decorativos.
- Estados vacíos: explicar qué falta y ofrecer un primer paso, nunca mostrar ceros como si hubiera datos confiables.

## 4. Biblioteca mínima de componentes
Todos deben soportar teclado, estados de carga/error, texto accesible, responsive y tokens semánticos.

| Componente | Contrato |
|---|---|
| AppShell | Encabezado, navegación estable, área principal, sin distracciones |
| PageHeader | Título humano + período + ayuda opcional |
| SummaryAmount | Etiqueta, monto ARS, período, estado Confirmado/Estimado, explicación |
| PrimaryAction | Solo una por vista, verbo específico: «Registrar cobro» |
| SecondaryAction | Alternativa discreta, nunca compite visualmente |
| SimpleCard | Una idea, máximo 3–5 datos o acciones |
| MoneyField | ARS, separadores locales, decimales, validación, precisión decimal |
| DateField | Fecha legible argentina y calendario accesible |
| PayerSelector | Particular/obra social/prepaga/institución; búsqueda opcional |
| StatusChip | Texto + símbolo; no solo color |
| EmptyState | Qué pasa + cómo empezar |
| InlineFeedback | Mensaje claro y recuperación, sin códigos técnicos |
| ConfirmDialog | Solo para operaciones destructivas/irreversibles |
| DetailDisclosure | Explicación opcional de fórmula, descuentos o liquidación |
| AccessibleList | Filas escaneables y resumen, alternativa a tablas complejas |
| ConsentControl | Opt-in explícito por canal, fácil revocación |

No introducir componentes genéricos complejos sin un caso de uso real.

## 5. Patrones obligatorios
### 5.1 Registrar ingreso
Idealmente tres pasos: **Qué hiciste → Cuánto y quién paga → Cuándo esperás cobrar**. Campos opcionales ocultos en «Agregar detalles». Mostrar revisión antes de guardar, confirmación posterior y opción «Corregir». No exigir datos identificatorios del paciente.

### 5.2 Registrar cobro
Seleccionar ingreso esperado (o «Cobro sin ingreso previo»), monto acreditado, fecha, medio y descuentos si aplican. Permitir cobros parciales, conciliación y diferencias explicadas. Nunca asumir que facturar equivale a cobrar.

### 5.3 Registrar gasto
«¿En qué gastaste?», importe, fecha y «¿Se repite todos los meses?». Sugerir categorías: monotributo, matrícula, alquiler/fee de consultorio, comisiones, insumos, servicios, contador, otros. Permitir gasto previsto vs pagado.

### 5.4 Proyección
Mostrar «Si se cumplen los cobros previstos, te quedarían $X al cierre de noviembre». Separar confirmados, estimados y sin fecha. Acceso «Ver cómo se calcula». Si faltan datos: «Todavía no podemos calcularlo bien» + acción para completar. Mostrar fecha de actualización.

### 5.5 Cartera administrativa
«Personas» con nombre/alias, contacto opcional, pagador, saldos administrativos y consentimiento. Sin campos clínicos ni texto libre que incentive cargar diagnósticos. Mensajería siempre con vista previa y confirmación humana.

### 5.6 Recomendaciones útiles y éticas
Una recomendación contextual por vez: «Hay una liquidación pendiente de revisar», «Podrías comparar el costo de tus consultorios». Explicar evidencia, incertidumbre y acción. Nunca sugerir prestaciones clínicas innecesarias ni marketing basado en diagnósticos.

## 6. Sistema de contenido y voz
**Tono:** optimista, resolutivo, cercano, respetuoso, sin infantilizar ni culpar.
- Éxito: «Listo, registramos el cobro».
- Vacío: «Todavía no registraste ingresos. Empezá con el primero».
- Pendiente: «Tenés 2 cobros para revisar».
- Estimación: «Podrías cobrar $… este mes, si se cumplen las fechas previstas».
- Error: «No pudimos guardar. Tus datos siguen acá; intentá otra vez».
- Evitar: «Error 500», «optimización de revenue», «pacientes rentables», «¡urgente!», «ganancias garantizadas».

Microcopy: botones con verbo + objeto, etiquetas persistentes (no solo placeholders), ayudas breves, números con contexto. Evitar emojis como única señal de estado.

## 7. Reglas visuales para dinero y estados
- ARS: `$ 1.234,56` (convención consistente); nunca ocultar centavos cuando cambien el resultado. Formatear con locale es-AR.
- Diferenciar **Cobrado** (confirmado), **Por cobrar** (esperado), **Gastos pagados**, **Gastos previstos** y **Proyección**.
- No usar verde/rojo para afirmar rentabilidad sin explicar supuestos; el estado «estimado» debe ser explícito.
- No redondear internamente; formatear solo en presentación. Valores negativos con signo y descripción.
- Una alerta solo si habilita una acción; no notificar por cada evento administrativo.

## 8. Estados de interfaz
Cada pantalla implementa: inicial/vacío, cargando, éxito, error recuperable, sin conexión cuando corresponda, permisos insuficientes y datos parciales. No borrar formularios ante errores de red. Confirmar antes de acciones irreversibles. Evitar spinners sin explicación o esperas indefinidas.

## 9. Responsive y rendimiento
- Probar al menos 320, 375, 768 y 1280 CSS px; sin scroll horizontal en tareas básicas.
- Navegación y CTA visibles en móvil sin cubrir campos o teclado.
- Cargar solo datos necesarios; paginar listas, evitar bibliotecas gráficas pesadas, animaciones no esenciales y fuentes redundantes.
- Respetar `prefers-reduced-motion`; medir Core Web Vitals en equipos modestos. No establecer umbrales ficticios de rendimiento como si estuvieran medidos.

## 10. Privacidad aplicada al diseño
- Minimización de datos desde formularios. Nunca pedir historia clínica ni diagnóstico.
- Consentimiento de comunicaciones granular, no premarcado, reversible y con canal identificado.
- Datos de distintos profesionales estrictamente separados; mensajes administrativos sin detalles clínicos.
- Ocultar datos personales innecesarios en capturas, logs, analytics y herramientas externas.
- Evitar patrones oscuros, upselling agresivo y recomendaciones que comprometan el bienestar del paciente.

## 11. Antipatrones: bloquear en revisión
- Dashboard de 8–12 KPIs, gráficos múltiples y menús extensos.
- Formularios de 20 campos obligatorios o términos como «devengamiento» sin traducción.
- Estimaciones presentadas como saldo disponible.
- «Guardar» que no persiste; botones decorativos; estados sin salida.
- Pantallas distintas para la misma acción sin necesidad.
- Colores/tipografía no derivados de marca aprobada.
- Cobros, descuentos y comisiones sumados dos veces.
- Mensajes automáticos a pacientes sin consentimiento.
- Funcionalidades clínicas o segmentación por condiciones de salud.

## 12. Definition of Done visual y de experiencia
Una PR de frontend debe incluir:
- [ ] Capturas mobile (375px) y desktop (1280px), sin datos reales.
- [ ] Una CTA principal y jerarquía visible en 5 segundos.
- [ ] Máximo tres cifras protagonistas en Inicio; detalles progresivos.
- [ ] Aptos Display/Aptos (o fallback autorizado), tokens semánticos, contraste y foco comprobados.
- [ ] Texto comprensible sin jerga, tono optimista y amable.
- [ ] Flujo completo y reversible; persistencia real; errores recuperables.
- [ ] Montos y estados financieros correctamente diferenciados.
- [ ] Prueba manual con persona no técnica o evidencia de usabilidad pendiente registrada.
- [ ] Sin datos clínicos ni marketing invasivo.
- [ ] Tests automatizados pertinentes y validación responsive.
- [ ] Sin nuevos servicios pagos o API de IA sin aprobación.

## 13. Validación con usuarios
En entrevistas y tests: pedir «Registrá un ingreso», «Encontrá cuánto te falta cobrar», «Explicame qué significa te quedaría». Observar sin enseñar. Registrar tiempo, dudas, errores, comprensión de estimaciones y necesidad de ayuda. Si una persona confunde proyección con saldo real, **bloquear el release** hasta corregirlo.

## 14. Gobierno y evolución
Cada cambio al sistema visual requiere motivo, impacto en accesibilidad y consistencia, capturas comparativas, validación con marca y aprobación de Product Owner. Los nuevos patrones se documentan aquí antes de replicarse. **Pendientes expresos:** cotejar la guía recuperada con el manual original y cualquier versión más reciente, confirmar archivos de logo y licencias tipográficas; auditar frontend existente; implementar tokens en código; probar contraste real y comprensión con usuarios.
