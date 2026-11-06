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
const brand = '<div class="brand"><b aria-hidden="true">N</b><div>Nagora Salud<small>Es momento de gestionar. · Logo temporal</small></div></div>';
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
function renderPage() {
  const {totals,records,payers,profile} = state;
  const pending = records.filter(r=>r.kind==='income' && !r.void && r.balance);
  if (page==='Inicio') {
    const first = commitments()[0];
    return heading('¡Hola, '+esc(profile.name.split(' ')[0])+'!','Así está tu actividad este mes.',button('income','+ Registrar ingreso',true)) +
      `<div class="toolbar">${period()}</div><div class="cards">${card('Cobré este mes',totals.received)}${card('Me deben',totals.pending,'yellow')}
      ${card('Gasté',totals.spent,'coral')}${card('Me queda',totals.net,'mint')}</div>
      <p class="muted">“Me queda” resta lo que pagaste de lo que cobraste en el mes elegido. El saldo pendiente incluye todos los meses.</p>
      <section class="panel"><h2>¿Qué necesito hacer hoy?</h2>
      <div class="row entry"><span>${pending.length?'Tenés '+pending.length+' cobros pendientes.':'Estás al día con tus cobros.'}</span>${pending.length?button('page:Pendientes','Ver pendientes'):''}</div>
      ${first?`<div class="row entry"><span>${dateText(first.day)} · ${esc(first.text)}</span>${button(first.action,first.label)}</div>`:''}</section>
      <div class="toolbar">${button('expense','Registrar gasto')}</div>`;
  }
  if (page==='Ingresos' || page==='Gastos') {
    const income = page==='Ingresos';
    const items = records.filter(r=>r.kind===(income?'income':'expense') &&
      (r.day.startsWith(state.month) || r.settlements.some(s=>s.day.startsWith(state.month))) &&
      (!income || ((!origin||r.source===origin)&&(!status||r.state===status))));
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
    <section class="panel"><h2>Ayuda</h2><details><summary>¿Cómo registro algo que todavía me deben?</summary><p>Entrá a Ingresos, tocá Registrar ingreso y dejá sin marcar “Ya me pagaron”. Cuando cobres, registrá el pago desde Pendientes.</p></details>
    <details><summary>¿Qué pongo en concepto?</summary><p>Usá una descripción como “Consultas de abril”. Evitá incluir nombres o datos de pacientes.</p></details></section>${profile.demo?'':button('recovery','Generar código de recuperación')} ${button('logout','Cerrar sesión')}`;
}
function render() {
  layout.innerHTML=`<div class="shell"><aside>${brand}<nav aria-label="Secciones">${pages.map(name=>`<button type="button" data-action="page:${name}" ${name===page?'aria-current="page"':''}>${name}</button>`).join('')}</nav></aside>
    <main id="main" tabindex="-1">${state.profile.demo?'<div class="demo">Cuenta de ejemplo · Dr. Martín López · Medicina clínica</div>':''}${renderPage()}</main></div>`;
}
function openDialog(title,html) {
  dialog.innerHTML=`<header class="head"><h2 id="dialog-title">${esc(title)}</h2>${button('close','Cerrar')}</header>${html}`;
  if (!dialog.open) dialog.showModal();
  (dialog.querySelector('input:not([type=hidden]), select') || dialog.querySelector('button'))?.focus();
}
function formDialog(title,endpoint,html,submit='Guardar') {
  openDialog(title,`<form data-endpoint="${endpoint}">${html}<p class="error" role="alert"></p><button class="primary">${submit}</button></form>`);
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
      formDialog('Generar código de recuperación','recovery','<p>Guardá el código en un lugar seguro. Podés usarlo una sola vez para recuperar tu cuenta.</p>'+
        field('Contraseña actual','password','','password'),'Generar código');
      break;
    case 'demo': await api('demo',{}); await refresh(); break;
    case 'logout': await api('logout',{}); state=null; page='Inicio'; origin=''; status=''; auth(); break;
    case 'page': page=arg; render(); document.querySelector('main').focus(); break;
    case 'close': dialog.close(); break;
    case 'income':
      openDialog('¿De dónde viene el ingreso?',`<p>Elegí quién te paga.</p><div class="choices">${sources.map((source,i)=>button('source:'+i,source)).join('')}</div>`);
      dialog.querySelector('.choices button').focus();
      break;
    case 'source': movementForm('income',sources[Number(arg)]); break;
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
    if(name==='paid') dialog.querySelector('#paid-date').hidden=!checked;
  } catch(error) { notify(error.message); }
});
document.addEventListener('submit',async event=>{
  event.preventDefault();
  const form=event.target;
  const submit=form.querySelector('button.primary');
  const errorBox=form.querySelector('.error');
  if(submit.disabled) return;
  submit.disabled=true;
  errorBox.textContent='';
  const data=Object.fromEntries(new FormData(form));
  for(const key of ['paid','recurrence','confirm_duplicate']) data[key]=data[key]==='on';
  data.key=form.dataset.key ||= crypto.randomUUID();
  try {
    const result=await api(form.dataset.endpoint,data);
    if(form.dataset.endpoint==='recovery') {
      openDialog('Tu código de recuperación',`<p>Copiá este código y guardalo en un lugar seguro.</p>${field('Código','recovery-code',result.code)}`);
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
