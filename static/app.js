'use strict';
const layout = document.querySelector('#layout');
const dialog = document.querySelector('#dialog');
const notice = document.querySelector('#notice');
const sources = ['Obra social','Prepaga','Particular','Otro'];
const categories = ['Alquiler','Servicios','Insumos','Matrícula profesional','Equipamiento','Impuestos','Software','Otros'];
const pages = ['Inicio','Ingresos','Pendientes','Gastos','Convenios','Resultado','Calendario','Perfil'];
let demoOnly=false;
let state, page = 'Inicio', origin = '', status = '', noticeTimer;
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const pesos = cents => {
  const exact = BigInt(cents);
  const absolute = exact < 0n ? -exact : exact;
  const decimal = absolute % 100n;
  return (exact < 0n ? '−' : '') + '$' + (absolute / 100n).toLocaleString('es-AR') +
    (decimal ? ',' + String(decimal).padStart(2,'0') : '');
};
const amountInput = cents => String(BigInt(cents)/100n) + ',' + String(BigInt(cents)%100n).padStart(2,'0');
const sum = (rows,key) => rows.reduce((total,row)=>total+BigInt(row[key]),0n);
const dateText = value => value ? value.split('-').reverse().join('/') : '';
const shapes = {
  coins:'<ellipse cx="15" cy="5" rx="6" ry="3"/><path d="M9 5v5m12-5v12c0 2-3 3-6 3m0-6c3 0 6-1 6-3"/><ellipse cx="8" cy="13" rx="5" ry="3"/><path d="M3 13v6c0 4 10 4 10 0v-6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  wallet:'<rect x="3" y="6" width="18" height="14" rx="3"/><path d="m5 6 12-3v3m4 5h-6a2 2 0 0 0 0 4h6"/>',
  plus:'<circle cx="12" cy="12" r="9"/><path d="M7 12h10m-5-5v10"/>',
  bank:'<path d="m3 9 9-6 9 6H3zm2 12h14M6 10v10m6-10v10m6-10v10"/>',
  shield:'<path d="M12 3 4 6v5c0 5 3 8 8 10 5-2 8-5 8-10V6zM9 11h6m-3-3v6"/>',
  people:'<circle cx="9" cy="8" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3zm13-15a3 3 0 0 1 0 6m2 3a4 4 0 0 1 3 4"/>',
  more:'<circle cx="12" cy="12" r="9"/><path d="M8 12h.01m4 0h.01m4 0h.01"/>',
  filter:'<path d="M3 4h18l-7 8v6l-4 2v-8z"/>',
  home:'<path d="m3 11 9-8 9 8m-16-1v11h14V10m-9 11v-6h4v6"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4m8-4v4"/>',
  chart:'<path d="M3 21h18M5 20v-6h4v6m2 0V9h4v11m2 0V4h4v16"/>',
  check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>'
};
const icon = name => `<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${shapes[name]}</svg>`;
const sourceIcons=['bank','shield','people','more'];
const navIcons=['home','coins','clock','wallet','bank','chart','calendar','people'];
const brand = '<div class="brand"><svg aria-hidden="true" viewBox="0 0 56 44"><path fill="#087f73" d="M2 34 12 10c2-5 6-7 11-7 5 0 8 3 10 7l5 12 6-15c1-3 3-4 6-4h5L44 33c-2 5-5 7-10 7-4 0-7-2-9-6l-6-13-5 13c-1 4-4 6-8 6H0z"/></svg><div>Nagora<br>Salud</div></div>';
const button = (action,label,primary=false) => `<button type="button" data-action="${action}" ${primary?'class="primary"':''}>${label}</button>`;
const options = (items, selected) => items.map(item => {
  const [value,label] = Array.isArray(item) ? item : [item,item];
  return `<option value="${esc(value)}" ${String(value)===String(selected)?'selected':''}>${esc(label)}</option>`;
}).join('');
const field = (label,name,value='',type='text',required=true) =>
  `<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${required?'required':''} ${name==='amount'?'inputmode="decimal"':''}></label>`;
const select = (label,name,items,value) => `<label>${label}<select name="${name}" required>${options(items,value)}</select></label>`;
const heading = (title,sub,action='') => `<header class="head"><div><h1>${title}</h1><p class="muted">${sub}</p></div>${action}</header>`;
const card = (label,amount,style='') => `<article class="card ${style}"><span>${label}</span><strong>${pesos(amount)}</strong></article>`;
const empty = 'Todavía no hay movimientos para mostrar.';
function notify(message) {
  clearTimeout(noticeTimer);
  notice.textContent = message;
  noticeTimer = setTimeout(() => { notice.textContent = ''; },4500);
}
async function api(path, data) {
  const response = await fetch('/api/'+path,data ? {
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)
  } : {});
  const result = await response.json();
  if (!response.ok) {
    if (response.status===401 && state) {
      state = null;
      if (dialog.open) dialog.close();
      auth();
      notify('Tu sesión venció. Volvé a ingresar.');
    }
    throw new Error(result.error);
  }
  return result;
}
async function refresh(month=state?.month) {
  state = await api('state'+(month?'?month='+encodeURIComponent(month):''));
  render();
}
function auth(register=false) {
  if(demoOnly) {
    layout.innerHTML=`<main id="main" class="auth" tabindex="-1">${brand}<section class="panel"><h1>Probá Nagora Salud</h1><p>Usá datos ficticios. Cada sesión de prueba es independiente y los cambios pueden perderse si el servicio se reinicia.</p>${button('demo','Entrar a la demo',true)}</section></main>`;
    return;
  }
  layout.innerHTML = `<main id="main" class="auth" tabindex="-1">${brand}
    <section class="panel"><h1>${register?'Creá tu cuenta':'Ingresá a tu cuenta'}</h1>
    <p class="muted">Tus ingresos, tus gastos y lo que te falta cobrar.</p>
    <form data-endpoint="${register?'register':'login'}">
      ${register?field('Tu nombre','name'):''}${field('Correo electrónico','email','','email')}
      <label>Contraseña<input type="password" name="password" required autocomplete="${register?'new-password':'current-password'}" ${register?'minlength="12"':''}></label>
      ${register?'<small>Usá al menos 12 caracteres.</small>':''}
      <p class="error" role="alert"></p><button class="primary">${register?'Crear cuenta':'Ingresar'}</button>
    </form><div class="toolbar">${button(register?'login':'register',register?'Ya tengo cuenta':'Crear cuenta')}${button('demo','Probar con datos de ejemplo')}${register?'':button('reset','Recuperar contraseña')}</div>
    </section></main>`;
}
function entry(record, mode='') {
  const {id,kind,source,concept,day,due,payer_name,balance,amount,state:tag,void:cancelled,settlements} = record;
  const income = kind==='income';
  return `<article class="entry"><div class="row"><div><h3>${esc(concept)}</h3><p class="muted">${esc(payer_name||source)} · ${dateText(day)}</p></div>
    <div><strong>${pesos(mode==='pending'?balance:amount)}</strong> <span class="badge">${tag}</span></div></div>
    <details ${mode==='pending'?'open':''}><summary>Ver detalle y acciones</summary>
    <p>${balance && !cancelled?'Quedan '+pesos(balance)+(due?' · Fecha estimada '+dateText(due):''):''}</p>
    ${settlements.map(item=>`<p>${esc(item.reason)} · ${dateText(item.day)} · ${pesos(item.amount)}</p>`).join('')}
    ${!cancelled?`<div class="toolbar">
      ${balance?button('settle:'+id,income?'Registrar cobro':'Registrar pago',true):''}
      ${balance && income?button('adjust:'+id,'Registrar diferencia'):''}
      ${balance?button('remind:'+id,'Crear recordatorio'):''}
      ${button('edit:'+id,'Editar')}${button('void:'+id,'Anular')}
    </div>`:''}</details></article>`;
}
function period() {
  return field('Mes','month',state.month,'month');
}
function commitments() {
  const outstanding = state.records.filter(r=>!r.void && r.balance);
  return [
    ...outstanding.filter(r=>r.due).map(r=>({day:r.due,text:r.concept,action:'show:'+r.id,label:'Ver movimiento'})),
    ...state.reminders.filter(r=>outstanding.some(m=>m.id===r.movement))
      .map(r=>({day:r.day,text:r.note,action:'done:'+r.id,label:'Marcar como hecho'}))
  ].sort((a,b)=>a.day.localeCompare(b.day));
}
let allIncome=false;
function incomePage(items,pending,totals) {
  const full=allIncome || Boolean(origin || status);
  return `<div class="income-screen">
    <header class="income-title"><span class="symbol">${icon('coins')}</span><div><h1>Ingresos y honorarios</h1><p>Registrá tus cobros y seguí cuánto te deben.</p></div></header>
    <div class="income-top">
      <article class="income-kpi mint">${icon('wallet')}<div><span>${state.month===state.today.slice(0,7)?'Cobrado este mes':'Cobrado en el mes elegido'}</span><strong>${pesos(totals.received)}</strong></div></article>
      <article class="income-kpi yellow">${icon('clock')}<div><span>Por cobrar</span><strong>${pesos(totals.pending)}</strong><small>${pending.length} ${pending.length===1?'cobro pendiente':'cobros pendientes'}</small></div></article>
      ${button('income',icon('plus')+' Registrar ingreso',true)}
    </div>
    <div class="income-body"><section class="income-list">
      <header class="row"><h2>${full?'Movimientos':'Últimos ingresos'}</h2>${!origin&&!status&&items.length>4?button('income-list',allIncome?'Ver últimos':'Ver todos →'):''}</header>
      ${(full?items:items.slice(0,4)).map(r=>`<button class="income-line" type="button" data-action="show:${r.id}">
        <span class="symbol">${icon(sourceIcons[sources.indexOf(r.source)]||'coins')}</span>
        <span class="income-label"><strong>${esc(r.payer_name||r.source)}</strong><small>${esc(r.concept)}</small></span>
        <time datetime="${r.day}">${new Intl.DateTimeFormat('es-AR',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(r.day+'T00:00:00Z'))}</time>
        <strong>${pesos(r.amount)}</strong><span class="badge ${r.balance&&!r.void?'waiting':''}">${r.state}</span>
      </button>`).join('')||empty}
    </section><section class="income-filters" aria-label="Filtros">
      <h2>${icon('filter')} Filtrar por…</h2>
      ${sources.map((source,i)=>`<button type="button" data-action="origin:${i}" aria-pressed="${origin===source}">${icon(sourceIcons[i])}<span>${source}</span><span aria-hidden="true">›</span></button>`).join('')}
      ${period()}${select('Estado','filter-state',[['','Todos'],'Por cobrar','Cobrado','Parcialmente cobrado','Cerrado con ajuste','Anulado'],status)}
    </section></div></div>`;
}
function renderPage() {
  const {totals,records,payers,profile} = state;
  const pending = records.filter(r=>r.kind==='income' && !r.void && r.balance);
  if (page==='Inicio') {
    const first = commitments()[0];
    const pendingLabel = pending.length===1?'1 cobro pendiente':pending.length+' cobros pendientes';
    return heading('Hola, '+esc(profile.name.split(' ')[0]),'Tu actividad, sin complicaciones.') +
      `<section class="home-overview" aria-label="Resumen de tu actividad">
        <div class="toolbar">${period()}</div>
        <div class="home-metrics">
          ${card('Ya cobraste este mes',totals.received)}
          ${card('Te falta cobrar',totals.pending,'yellow')}
          ${card('Te quedó de lo cobrado',totals.net,'mint')}
        </div>
        <p class="home-explainer">El último importe es lo que cobraste menos lo que pagaste en el mes. <strong>No es una proyección al cierre.</strong> Lo pendiente incluye cobros de otros meses.</p>
        <div class="home-primary">${button('income','Registrar ingreso',true)}</div>
      </section>
      <section class="panel home-next"><h2>¿Qué podés hacer ahora?</h2>
        <p>${pending.length?'Tenés '+pendingLabel+'.':'No tenés cobros pendientes registrados.'}</p>
        ${pending.length?button('page:Pendientes','Revisar cobros pendientes'):''}
        ${first?`<p class="muted">Próximo seguimiento: ${dateText(first.day)} · ${esc(first.text)}</p>`:''}
        <details><summary>Otras acciones</summary>
          <div class="toolbar">${button('expense','Registrar gasto')}${button('page:Resultado','Ver detalle de resultados')}</div>
        </details>
      </section>`;
  }
  if (page==='Ingresos' || page==='Gastos') {
    const income = page==='Ingresos';
    const items = records.filter(r=>r.kind===(income?'income':'expense') &&
      (r.day.startsWith(state.month) || r.settlements.some(s=>s.day.startsWith(state.month))) &&
      (!income || ((!origin||r.source===origin)&&(!status||r.state===status))));
    if(income) return incomePage(items,pending,totals);
    return heading(income?'Ingresos y honorarios':'Mis gastos',income?'Registrá lo que ganaste y controlá lo que todavía te deben.':'Revisá lo que pagaste y lo que te falta pagar.',
      button(income?'income':'expense',income?'+ Registrar ingreso':'+ Registrar gasto',true)) +
      `<div class="toolbar">${period()}${income?select('Origen','filter-source',[['','Todos'],...sources],origin)+select('Estado','filter-state',[['','Todos'],'Por cobrar','Cobrado','Parcialmente cobrado','Cerrado con ajuste','Anulado'],status):''}</div>
      <div class="cards">${card(income?'Cobrado en el mes':'Pagado en el mes',income?totals.received:totals.spent,'mint')}
      ${income?card('Pendiente de todos los meses',totals.pending,'yellow'):''}</div>
      <section class="panel"><h2>Movimientos</h2>${items.map(r=>entry(r)).join('')||empty}</section>`;
  }
  if(page==='Pendientes') return heading('Dinero que me deben','Tenés '+pending.length+' cobros pendientes.') +
    `<div class="cards">${card('Total pendiente',totals.pending,'yellow')}</div><section class="panel"><h2>Por cobrar</h2>${pending.map(r=>entry(r,'pending')).join('')||'Estás al día con tus cobros.'}</section>`;
  if(page==='Convenios') return heading('Obras sociales y prepagas','Registrá las entidades con las que trabajás.',button('payer','+ Agregar entidad',true)) +
    `<section class="panel"><h2>Mis entidades</h2>${payers.map(p=>{
      const items=records.filter(r=>r.payer===p.id&&!r.void);
      const payments=items.flatMap(r=>r.settlements.filter(s=>s.reason==='Pago').map(s=>Math.max(0,(Date.parse(s.day)-Date.parse(r.day))/86400000)));
      const avg=payments.length?Math.round(payments.reduce((a,b)=>a+b,0)/payments.length)+' días promedio desde la prestación':'Sin cobros registrados';
      return `<article class="entry"><h3>${esc(p.name)}</h3><p>${esc(p.kind)} · Plazo esperado: ${p.days} días</p>
        <p>Me deben ${pesos(sum(items,'balance'))} · Cobré ${pesos(sum(items,'cash'))}</p>
        <p>${avg} · ${items.filter(r=>r.balance).length} movimientos pendientes</p><p>${esc(p.terms)}</p></article>`;
    }).join('')||'Agregá una entidad para poder registrar sus liquidaciones.'}</section>`;
  if(page==='Resultado') return heading('Resultado de mi actividad','Dos formas de mirar el mes.') +
    `<div class="toolbar">${period()}</div><div class="cards">${card('Me queda según registros',totals.net,'mint')}${card('Resultado de mi actividad',totals.activity)}</div>
    <section class="panel"><h2>¿Cómo se calcula?</h2><details><summary>Me queda según registros</summary><p>Cobros recibidos menos gastos pagados. Puede diferir del saldo de tu cuenta y de lo que queda después de impuestos.</p></details>
    <details><summary>Resultado de mi actividad</summary><p>Honorarios y gastos según la fecha registrada. Los descuentos, retenciones y otros ajustes se restan en el mes en que los registraste.</p></details>
    <h3>Impuestos pendientes</h3><p>${pesos(sum(records.filter(r=>r.kind==='expense'&&r.source==='Impuestos'&&!r.void),'balance'))} · Se restan de “Me queda” cuando los pagás.</p></section>`;
  if(page==='Calendario') return heading('Próximos compromisos','Cobros, vencimientos y recordatorios.') +
    `<section class="panel"><h2>Fechas para tener en cuenta</h2>${commitments().map(item=>`<article class="entry row"><span>${dateText(item.day)} · ${esc(item.text)}</span>${button(item.action,item.label)}</article>`).join('')||'No hay compromisos con fecha.'}</section>`;
  return heading('Mi perfil','Configurá cómo aparece tu nombre.') +
    `<section class="panel"><form data-endpoint="profile">${field('Tu nombre','name',profile.name)}<p class="error" role="alert"></p><button class="primary">Guardar perfil</button></form></section>
    <section class="panel"><h2>Ayuda</h2><details><summary>¿Cómo registro algo que todavía me deben?</summary><p>Entrá a Ingresos, tocá Registrar ingreso y elegí “Por cobrar”. Cuando cobres, registrá el pago desde Pendientes.</p></details>
    <details><summary>¿Qué pongo en concepto?</summary><p>Usá una descripción como “Consultas de abril”. Evitá incluir nombres o datos de pacientes.</p></details></section>${profile.demo?'':button('recovery','Generar código de recuperación')} ${button('logout','Cerrar sesión')}`;
}
function render() {
  const pendingCount=state.records.filter(r=>r.kind==='income'&&!r.void&&r.balance).length;
  layout.innerHTML=`<div class="shell"><aside>${brand}<nav aria-label="Secciones">${pages.map((name,i)=>`<button type="button" data-action="page:${name}" ${name===page?'aria-current="page"':''}>${icon(navIcons[i])}<span>${({Pendientes:'Cobros pendientes',Resultado:'Reportes'})[name]||name}</span>${name==='Pendientes'&&pendingCount?`<small class="nav-count">${pendingCount}</small>`:''}</button>`).join('')}</nav><div class="side-help">${button('page:Perfil','Ayuda')}</div></aside>
    <main id="main" tabindex="-1"><header class="account-bar">${state.profile.demo?'<span class="demo-tag">Datos de ejemplo</span>':''}${button('page:Perfil',icon('people')+' '+esc((state.profile.demo?'Dr. ':'')+state.profile.name)+' ⌄')}</header>${renderPage()}</main></div>`;
}
function openDialog(title,html,wide=false) {
  stopDictation?.();
  dialog.classList.toggle('income-dialog',wide);
  if(wide) {
    dialog.innerHTML=`<header class='income-title'><span class='symbol'>${icon('coins')}</span><div><h2 id='dialog-title'>Registrar ingreso</h2><p>Sumá un cobro por una consulta, práctica u honorario.</p></div><button type='button' data-action='close' aria-label='Cerrar'>×</button></header>${html}`;
    if(!dialog.open) dialog.showModal();
    return;
  }
  dialog.innerHTML=`<header class="head"><h2 id="dialog-title">${esc(title)}</h2>${button('close','Cerrar')}</header>${html}`;
  if (!dialog.open) dialog.showModal();
  (dialog.querySelector('input:not([type=hidden]), select') || dialog.querySelector('button'))?.focus();
}
function formDialog(title,endpoint,html,submit='Guardar') {
  openDialog(title,`<form data-endpoint="${endpoint}">${html}<p class="error" role="alert"></p><button class="primary">${submit}</button></form>`);
}
const SpeechInput = window.SpeechRecognition || window.webkitSpeechRecognition;
let stopDictation;
dialog.addEventListener('close', () => {
  if (!dialog.open) stopDictation?.();
});

function voicePanel(kind) {
  const example = kind === 'income' ? 'Ayer cobré 25000 pesos por una consulta' : 'Hoy pagué 18000 pesos por insumos';
  return `<details class="voice-panel"><summary>Cargar con voz</summary>
    <p class="muted">Por ejemplo: «${example}». Evitá mencionar datos de pacientes.
    El navegador puede procesar el audio en línea.</p>
    ${SpeechInput ? button('voice-listen','Dictar') : '<p class="muted">El micrófono no está disponible en este navegador. Podés escribir la frase.</p>'}
    <label>Tu frase<textarea rows="2" maxlength="240" data-voice-text></textarea></label>
    ${button('voice-apply','Completar formulario')}
    <p role="status" data-voice-status></p>
  </details>`;
}

function listenToMovement() {
  if (stopDictation) {
    stopDictation();
    return;
  }
  const text = dialog.querySelector('[data-voice-text]');
  const status = dialog.querySelector('[data-voice-status]');
  const trigger = dialog.querySelector('[data-action="voice-listen"]');
  const speech = new SpeechInput();
  speech.lang = 'es-AR';
  let timer;
  const finish = message => {
    if (!stopDictation || stopDictation !== cancel) return;
    stopDictation = undefined;
    clearTimeout(timer);
    trigger.textContent = 'Dictar';
    status.textContent = message;
  };
  const cancel = () => {
    finish('Dictado cancelado.');
    speech.abort();
  };
  stopDictation = cancel;
  speech.onresult = event => {
    if (stopDictation !== cancel) return;
    text.value = event.results[0][0].transcript.trim().slice(0,240);
    finish('Revisá la frase y tocá Completar formulario.');
  };
  speech.onerror = () => finish('No pudimos usar el dictado. Revisá el permiso del micrófono o escribí la frase.');
  speech.onend = () => finish('No se detectó una frase. Podés volver a dictar o escribirla.');
  trigger.textContent = 'Cancelar dictado';
  status.textContent = 'Escuchando…';
  try {
    speech.start();
    timer = setTimeout(cancel, 20000);
  } catch {
    finish('No se pudo iniciar el micrófono. Podés escribir la frase.');
  }
}

function movementFromPhrase(phrase, kind, today) {
  const verbs = kind === 'income' ? 'cobr[eé]|recib[ií]|me pagaron' : 'pagu[eé]|gast[eé]';
  const pattern = new RegExp(`^(?:(hoy|ayer)\\s+)?(${verbs})\\s+\\$?\\s*((?:[0-9]{1,3}(?:\\.[0-9]{3}){1,3}|[0-9]{1,11})(?:,[0-9]{1,2})?)(?:\\s+pesos)?(?:\\s+(?:por|en)\\s+(.+))?[.!]?$`,'iu');
  const match = phrase.trim().replace(/\s+/g,' ').match(pattern);
  if (!match || Number(match[3].replaceAll('.','').replace(',','.')) <= 0) return;
  const date = new Date(today+'T00:00:00Z');
  if (match[1]?.toLowerCase() === 'ayer') date.setUTCDate(date.getUTCDate()-1);
  return {amount:match[3], concept:match[4]?.replace(/[.!]$/,'').slice(0,120), day:date.toISOString().slice(0,10)};
}

function applyMovementPhrase() {
  const form = dialog.querySelector('form');
  const {elements} = form;
  const status = form.querySelector('[data-voice-status]');
  const draft = movementFromPhrase(form.querySelector('[data-voice-text]').value,elements.kind.value,state.today);
  if (!draft) {
    status.textContent = 'No pude completar el formulario. Usá una frase como la del ejemplo, con el monto en números.';
    return;
  }
  elements.amount.value = draft.amount;
  if (draft.concept) elements.concept.value = draft.concept;
  elements.day.value = elements.paid_day.value = draft.day;
  if (elements.kind.value === 'income') elements.paid.value = 'on';
  else elements.paid.checked = true;
  form.querySelector('#paid-date').hidden = false;
  status.textContent = 'Revisá el monto, el concepto y la fecha antes de guardar.';
}

function movementForm(kind,source,record) {
  const income=kind==='income';
  const entity=income&&sources.slice(0,2).includes(source);
  const entities=state.payers.filter(p=>p.kind===source);
  if(entity&&!entities.length) {
    openDialog('Elegí una entidad',`<p>Primero agregá una entidad en Convenios.</p>${button('payer','Agregar entidad',true)}${button('income','Volver')}`);
    return;
  }
  formDialog(record?'Editar movimiento':income?'Registrar ingreso':'Registrar gasto',
    record?'movements/'+record.id+'/edit':'movements',
    `<input type="hidden" name="kind" value="${kind}">
    ${income?`<input type="hidden" name="source" value="${esc(source)}"><p class="badge">${esc(source)}</p>`:
      select('Categoría','source',categories,record?.source||'Otros')}
    ${entity?`${entities.length>5?field('Buscar entidad','payer-search','','search',false):''}${select('¿Cuál?','payer',entities.map(p=>[p.id,p.name]),record?.payer)}`:''}
    ${record?'':voicePanel(kind)}
    ${field(income?'Concepto o prestación':'¿En qué gastaste?','concept',record?.concept)}
    ${field('Monto en pesos','amount',record?amountInput(record.amount):'')}
    ${field(entity?'Fecha de prestación o liquidación':'Fecha del movimiento','day',record?.day||state.today,'date')}
    ${record?'':`<label><input name="paid" type="checkbox" ${source==='Particular'?'checked':''}>${income?'Ya me pagaron':'Ya lo pagué'}</label>
      <div id="paid-date" ${source==='Particular'?'':'hidden'}>${field(income?'Fecha del cobro':'Fecha del pago','paid_day',state.today,'date',false)}</div>`}
    <details ${entity?'open':''}><summary>Más opciones</summary>
      ${field(income?'Fecha estimada de cobro':'Vencimiento','due',record?.due,'date',false)}
      ${entity?field('Número de liquidación','reference',record?.reference,'text',false):''}
      ${income||record?.series?'':`<label><input type="checkbox" name="recurrence" ${record?.recurrence?'checked':''}>Se repite cada mes</label>`}
      <label><input type="checkbox" name="confirm_duplicate">Permitir un movimiento igual si corresponde</label>
    </details>`,record?'Guardar cambios':income?'Guardar ingreso':'Guardar gasto');
  if (!record && income) dialog.querySelector('.badge').insertAdjacentHTML('afterend',button('income','Cambiar origen'));
}
function registerIncome(source='',draft={}) {
  const entity=sources.slice(0,2).includes(source);
  const entities=state.payers.filter(p=>p.kind===source);
  const paid=draft.source===source ? draft.paid==='on' : source==='Particular';
  const sourcePicker=`<div class="source-picker"><strong>¿De dónde viene el ingreso?</strong><div class="choices">${sources.map((item,i)=>`<button type="button" data-action="source:${i}" aria-pressed="${source===item}">${icon(sourceIcons[i])}${item}</button>`).join('')}</div></div>`;
  const fields=entity&&!entities.length ? `<p>Agregá una entidad para registrar sus ingresos.</p>${button('payer','Agregar entidad',true)}` :
    `<form data-endpoint="movements"><input name="kind" type="hidden" value="income"><input name="source" type="hidden" value="${esc(source)}">
      ${entity?select('¿Cuál?','payer',entities.map(p=>[p.id,p.name]),draft.source===source?draft.payer:null):''}
      ${voicePanel('income')}
      <div class="form-grid">
        ${field('Concepto o prestación','concept',draft.concept)}
        ${field('Monto en pesos','amount',draft.amount)}
        ${field(entity?'Fecha de prestación o liquidación':'Fecha del movimiento','day',draft.day||state.today,'date')}
        <fieldset class="income-status"><legend>Estado</legend><label><input type="radio" name="paid" value="on" ${paid?'checked':''}>${icon('check')} Cobrado</label><label><input type="radio" name="paid" value="off" ${!paid?'checked':''}>${icon('clock')} Por cobrar</label></fieldset>
        <div id="paid-date" ${paid?'':'hidden'}>${field('Fecha del cobro','paid_day',draft.paid_day||state.today,'date',false)}</div>
      </div>
      <details><summary>Más opciones</summary><div class="form-grid">${field('Fecha estimada de cobro','due',draft.due,'date',false)}${entity?field('Número de liquidación','reference',draft.reference,'text',false):''}</div><label><input type="checkbox" name="confirm_duplicate" ${draft.confirm_duplicate?'checked':''}>Permitir un movimiento igual si corresponde</label></details>
      <p class="error" role="alert"></p><footer class="income-actions">${button('close','Cancelar')}<button class="primary">${icon('check')} Guardar ingreso</button></footer>
    </form>`;
  openDialog('Registrar ingreso',sourcePicker+(source?fields:'<p class="muted">Elegí el origen para continuar.</p>'),true);
  dialog.querySelector('.choices [aria-pressed="true"], .choices button')?.focus();
  if(source) dialog.querySelector('.choices [aria-pressed="true"]')?.focus();
}
async function action(name) {
  const [command,arg]=name.split(':');
  const r=state?.records.find(m=>String(m.id)===arg);
  switch(command) {
    case 'login': case 'register': auth(command==='register'); break;
    case 'reset':
      formDialog('Recuperar contraseña','reset',field('Correo electrónico','email','','email')+
        field('Código de recuperación','code')+field('Nueva contraseña (12 caracteres o más)','password','','password'),'Cambiar contraseña');
      break;
    case 'recovery':
      formDialog('Generar código de recuperación','recovery','<p>Guardá el código en un lugar seguro. Dura 30 días y podés usarlo una sola vez. Al generar uno nuevo, el anterior deja de funcionar.</p>'+
        field('Contraseña actual','password','','password'),'Generar código');
      break;
    case 'demo': await api('demo',{}); await refresh(); break;
    case 'logout': await api('logout',{}); state=null; page='Inicio'; origin=''; status=''; auth(); break;
    case 'page': page=arg; render(); document.querySelector('main').focus(); break;
    case 'close': dialog.close(); break;
    case 'voice-listen': listenToMovement(); break;
    case 'voice-apply': applyMovementPhrase(); break;
    case 'income': registerIncome(); break;
    case 'source': {
      const form=dialog.querySelector('form');
      registerIncome(sources[Number(arg)],form?Object.fromEntries(new FormData(form)):{});
      break;
    }
    case 'income-list': allIncome=!allIncome; render(); document.querySelector('.income-list header button')?.focus(); break;
    case 'origin': {
      const source=sources[Number(arg)];
      origin=origin===source?'':source;
      render();
      document.querySelector('[data-action="origin:'+arg+'"]').focus();
      break;
    }
    case 'expense': movementForm('expense'); break;
    case 'edit': movementForm(r.kind,r.source,r); break;
    case 'show': openDialog('Detalle del movimiento',entry(r,'pending')); break;
    case 'settle': case 'adjust':
      formDialog(command==='adjust'?'Registrar diferencia':r.kind==='income'?'Registrar cobro':'Registrar pago',
        'movements/'+arg+'/settle',`<p>Quedan <strong>${pesos(r.balance)}</strong></p>
        ${field('Monto en pesos','amount',command==='adjust'?'':amountInput(r.balance))}
        ${field('Fecha','day',state.today,'date')}
        ${command==='adjust'?select('Motivo','reason',['Descuento','Retención','Débito','Ajuste']):'<input name="reason" type="hidden" value="Pago">'}
        ${command==='adjust'?'<small>Si todavía esperás cobrar la diferencia, dejala pendiente y registrá solo lo que te pagaron.</small>':''}`);
      break;
    case 'void': formDialog('Anular movimiento','movements/'+arg+'/void',`<p>Se quitará de los totales junto con sus pagos. Podés consultar el movimiento anulado después.</p>${field('Motivo','note')}`,'Confirmar anulación'); break;
    case 'remind': formDialog('Crear recordatorio','movements/'+arg+'/remind',field('¿Cuándo?','day',state.today,'date')+field('¿Qué querés recordar?','note',r.concept)); break;
    case 'done': await api('reminders/'+arg,{key:crypto.randomUUID()}); await refresh(); notify('Recordatorio completado.'); break;
    case 'payer': formDialog('Agregar entidad','payers',select('Tipo','kind',sources.slice(0,2))+field('Nombre','name')+
      field('Plazo esperado en días','days','30','number')+field('Prestaciones, honorarios y descuentos acordados','terms','','text',false)); break;
  }
}
document.addEventListener('click',async event=>{
  const target=event.target.closest('[data-action]');
  if(!target) return;
  target.disabled=true;
  try { await action(target.dataset.action); }
  catch(error) { notify(error.message); }
  finally { target.disabled=false; }
});
document.addEventListener('input',event=>{
  if(event.target.name!=='payer-search') return;
  const picker=dialog.querySelector('[name="payer"]');
  const term=event.target.value.trim().toLocaleLowerCase('es-AR');
  const visible=[...picker.options].filter(option=>{
    option.hidden=!option.text.toLocaleLowerCase('es-AR').includes(term);
    return !option.hidden;
  });
  if(!visible.some(option=>option.selected)) picker.value=visible[0]?.value||'';
});
document.addEventListener('change',async event=>{
  const {name,value,checked}=event.target;
  try {
    if(name==='month'&&value) await refresh(value);
    if(name==='filter-source'||name==='filter-state') {
      if(name==='filter-source') origin=value; else status=value;
      render();
      document.querySelector('[name="'+name+'"]').focus();
    }
    if(name==='paid') dialog.querySelector('#paid-date').hidden=event.target.type==='radio'?value!=='on':!checked;
  } catch(error) { notify(error.message); }
});
document.addEventListener('submit',async event=>{
  event.preventDefault();
  const form=event.target;
  const submit=form.querySelector('button.primary');
  const errorBox=form.querySelector('.error');
  if(submit.disabled) return;
  stopDictation?.();
  submit.disabled=true;
  errorBox.textContent='';
  const data=Object.fromEntries(new FormData(form));
  for(const key of ['paid','recurrence','confirm_duplicate']) data[key]=data[key]==='on';
  data.key=form.dataset.key ||= crypto.randomUUID();
  try {
    const result=await api(form.dataset.endpoint,data);
    if(form.dataset.endpoint==='recovery') {
      openDialog('Tu código de recuperación',`<p>Copiá este código y guardalo en un lugar seguro. Dura 30 días y sirve una sola vez.</p>${field('Código','recovery-code',result.code)}`);
      const codeField=dialog.querySelector('input');
      codeField.readOnly=true;
      codeField.focus();
      codeField.select();
      return;
    }
    if(form.dataset.endpoint==='reset') {
      dialog.close();
      state=null;
      auth();
      notify('Contraseña actualizada. Ya podés ingresar.');
      return;
    }
    if(dialog.open) dialog.close();
    const previous=state;
    if(form.dataset.endpoint==='movements') {
      page=data.kind==='income'?'Ingresos':'Gastos';
      origin=''; status='';
    }
    const month=form.dataset.endpoint==='movements'?data.day.slice(0,7):previous?.month;
    await refresh(month);
    document.querySelector('main').focus();
    if(previous) notify('Guardado. Tus registros están actualizados.');
  } catch(error) { errorBox.textContent=error.message; }
  finally { submit.disabled=false; }
});
api('config').then(config=>{ demoOnly=config.demoOnly; }).catch(()=>{}).then(()=>refresh().catch(()=>auth()));
