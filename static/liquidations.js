'use strict';
let liquidationDraft;
function liquidationBack(step){
  const form=dialog.querySelector('form');
  if(form?.dataset.liquidationStep==='2'){
    liquidationDraft.allocations=[...form.querySelectorAll('.allocation')].filter(el=>el.querySelector('input[type=checkbox]').checked).map(el=>{
      const movement=Number(el.dataset.movement);
      return {movement,...Object.fromEntries(['allocated','cash','discount','retained','discount_kind','retention_kind','note'].map(k=>[k,el.querySelector(`[name="${k}-${movement}"]`).value])),difference:'0'};
    });
  }
  liquidationStep(step);
}
const liquidationMoney = value => {
  const text=String(value).trim();
  if(!/^(?:[0-9]{1,11}|[0-9]{1,3}(?:\.[0-9]{3}){1,3})(?:,[0-9]{1,2})?$/.test(text)) throw Error('Usá importes como 1500 o 1.500,25, sin más de dos decimales.');
  const [whole,cents='']=text.replaceAll('.','').split(',');
  const exact=BigInt(whole)*100n+BigInt(cents.padEnd(2,'0'));
  if(exact>9999999999999n) throw Error('El importe supera el rango permitido.');
  return exact;
};
function liquidationList(){
  openDialog('Liquidaciones',`<p>Registrá lo recibido por varias prestaciones, sin volver a cargar los ingresos.</p>
    ${button('liquidation-new','Cargar liquidación',true)}
    <div class="liquidation-list">${state.liquidations.map(l=>`<article class="entry"><h3>${esc(state.payers.find(p=>p.id===l.payer)?.name)} · ${esc(l.reference)}</h3><p>Recibido vigente: ${pesos(l.received)} · ${dateText(l.day)}</p>${button('liquidation-show:'+l.id,'Ver liquidación '+l.reference)}</article>`).join('')||'<p>Todavía no cargaste liquidaciones.</p>'}</div>`);
}
function startLiquidation(id){
  const existing=state.liquidations.find(l=>l.id===id);
  liquidationDraft=existing?{id,payer:existing.payer,reference:existing.reference,day:existing.day,method:existing.method,received:amountInput(existing.received),version:existing.version,token:existing.token,allocations:existing.allocations.map(r=>({...r,...Object.fromEntries(['allocated','cash','discount','retained','difference'].map(k=>[k,amountInput(r[k])]))})),note:''}:{payer:state.payers[0]?.id,reference:'',received:'',day:state.today,method:'Transferencia',allocations:[]};
  if(!state.payers.length){openDialog('Liquidaciones','<p>Agregá el pagador en Convenios antes de cargar su liquidación.</p>'+button('payer','Agregar entidad',true));return;}
  liquidationStep(1);
}
function liquidationStep(step){
  const d=liquidationDraft;
  let content;
  if(step===1){
    content=`<p>Identificá la liquidación y sólo el dinero que ya se acreditó.</p>
      ${d.id?`<p>${esc(state.payers.find(p=>p.id===d.payer)?.name)} · ${esc(d.reference)}</p>`:select('¿Quién liquidó?','payer',state.payers.map(p=>[p.id,p.name]),d.payer)+field('Referencia de la liquidación','reference',d.reference)}
      ${field('Dinero recibido en pesos','received',d.received)}${field('Fecha de acreditación o liquidación','day',d.day,'date')}
      <details><summary>Medio de cobro</summary>${select('Medio','method',['Transferencia','Efectivo','Cheque acreditado','Otro'],d.method)}</details>
      ${d.id?field('Motivo de la corrección','note',d.note):''}`;
  }else if(step===2){
    const candidates=state.records.filter(r=>r.kind==='income'&&!r.void&&r.payer===Number(d.payer)&&(r.balance>0||d.allocations.some(a=>a.movement===r.id)));
    content=`<p>Elegí las prestaciones incluidas. Podés registrar sólo una parte; el resto seguirá pendiente.</p>
      ${candidates.map(r=>{
        const a=d.allocations.find(a=>a.movement===r.id);
        return `<article class="allocation" data-movement="${r.id}"><label><input type="checkbox" name="include-${r.id}" ${a?'checked':''}>Incluir ${esc(r.concept)}</label><p class="muted">Honorarios: ${pesos(r.amount)} · Pendiente actual: ${pesos(r.balance)}</p>
          <div class="allocation-fields" ${a?'':'hidden'}>
          ${field('Importe incluido en pesos','allocated-'+r.id,a?.allocated||amountInput(r.balance),'text',false)}
          ${field('Recibido para esta prestación','cash-'+r.id,a?.cash||'0','text',false)}
          <details ${a?'open':''}><summary>Descuentos y retenciones</summary>
          ${field('Descuento aceptado en pesos','discount-'+r.id,a?.discount||'0','text',false)}
          ${select('Tipo de descuento','discount_kind-'+r.id,[['','Elegir si corresponde'],'Descuento aceptado','Comisión aceptada','Débito aceptado'],a?.discount_kind||'')}
          ${field('Retenido en pesos','retained-'+r.id,a?.retained||'0','text',false)}
          ${select('Tipo de retención','retention_kind-'+r.id,[['','Elegir si corresponde'],'Tributaria','Contractual','Por clasificar'],a?.retention_kind||'')}
          <p class="muted">Lo retenido no es caja ni una pérdida definitiva.</p></details>
          <p data-difference>Diferencia por resolver: se calcula al revisar.</p>
          ${field('Explicación administrativa (sin datos de pacientes)','note-'+r.id,a?.note||'','text',false)}
          </div></article>`;
      }).join('')||'<p>No hay prestaciones pendientes de este pagador. Cargá los honorarios primero.</p>'}`;
  }else{
    content=`<p><strong>${esc(d.reference)}</strong> · ${esc(state.payers.find(p=>p.id===Number(d.payer))?.name)} · ${dateText(d.day)}</p>
      <p>Se acreditará en caja: <strong>${pesos(liquidationMoney(d.received))}</strong></p>
      ${d.allocations.map(a=>`<article class="entry"><h3>${esc(state.records.find(r=>r.id===a.movement)?.concept)}</h3>
      <p>Incluido: ${pesos(liquidationMoney(a.allocated))} · Recibido: ${pesos(liquidationMoney(a.cash))}</p>
      <details><summary>Ver descuentos, retenciones y diferencia</summary><p>Descuento aceptado: ${pesos(liquidationMoney(a.discount))} ${esc(a.discount_kind)}</p><p>Retenido: ${pesos(liquidationMoney(a.retained))} ${esc(a.retention_kind)}</p><p>Diferencia por resolver: ${pesos(liquidationMoney(a.difference))}</p><p>${esc(a.note)}</p></details></article>`).join('')}
      <p class="muted">No se crearán prestaciones nuevas. Las diferencias seguirán pendientes; las retenciones quedan separadas del resultado.</p>
      ${d.id?'<p>La corrección reemplaza las asignaciones vigentes y aplica esta fecha a todos sus cobros. Conserva el historial y recalcula los meses afectados.</p>':''}`;
  }
  openDialog(d.id?'Corregir liquidación':'Cargar liquidación',`<div class="liquidation-wizard"><p class="step-label" role="status">Paso ${step} de 3 · ${['','Identificar','Asignar','Revisar'][step]}</p><form data-liquidation-step="${step}">${content}<p class="error" role="alert" tabindex="-1"></p><div class="toolbar">${step>1?button('liquidation-back:'+(step-1),'Atrás'):''}<button class="primary">${step===3?(d.id?'Confirmar corrección':'Confirmar liquidación'):'Continuar'}</button></div></form></div>`);
  // Optional selectors cannot block native validation when their amounts are zero.
  if(step===2)dialog.querySelectorAll('select').forEach(el=>el.required=false);
  if(step===1)dialog.querySelector('[name=day]').max=state.today;
}
function readAllocation(article){
  const id=Number(article.dataset.movement),d={movement:id};
  for(const key of ['allocated','cash','discount','retained','discount_kind','retention_kind','note'])d[key]=article.querySelector(`[name="${key}-${id}"]`).value;
  const rest=liquidationMoney(d.allocated)-liquidationMoney(d.cash)-liquidationMoney(d.discount)-liquidationMoney(d.retained);
  if(rest<0n)throw Error('Recibido, descuentos y retenciones superan el importe incluido.');
  if(liquidationMoney(d.allocated)===0n)throw Error('El importe incluido debe ser mayor que cero.');
  d.difference=amountInput(rest);
  if(liquidationMoney(d.discount)>0n&&!d.discount_kind)throw Error('Elegí el tipo de descuento aceptado.');
  if(liquidationMoney(d.retained)>0n&&!d.retention_kind)throw Error('Clasificá la retención, aunque quede por revisar.');
  if((rest>0n||liquidationMoney(d.discount)>0n||liquidationMoney(d.retained)>0n)&&!d.note.trim())throw Error('Explicá la diferencia, descuento o retención sin datos de pacientes.');
  return d;
}
async function submitLiquidation(form){
  const submit=form.querySelector('.primary'),errors=form.querySelector('.error');
  if(submit.disabled)return;
  submit.disabled=true;errors.textContent='';
  try{
    const step=Number(form.dataset.liquidationStep),d=liquidationDraft;
    if(step===1){
      const data=Object.fromEntries(new FormData(form));liquidationMoney(data.received);
      if(!d.id&&Number(data.payer)!==Number(d.payer))d.allocations=[];
      Object.assign(d,data);d.payer=Number(d.payer);liquidationStep(2);
    }else if(step===2){
      const rows=[...form.querySelectorAll('.allocation')].filter(el=>el.querySelector('input[type=checkbox]').checked).map(readAllocation);
      if(!rows.length||rows.length>30)throw Error('Elegí entre una y treinta prestaciones.');
      if(rows.reduce((total,r)=>total+liquidationMoney(r.cash),0n)!==liquidationMoney(d.received))throw Error('La suma recibida por prestación debe coincidir exactamente con el dinero recibido.');
      d.allocations=rows;liquidationStep(3);
    }else{
      const {requestKey,requestPayload,...body}=d,payload=JSON.stringify(body);
      if(requestPayload!==payload){d.requestPayload=payload;d.requestKey=crypto.randomUUID();}
      const result=await api(d.id?`liquidations/${d.id}/correct`:'liquidations',{...body,key:d.requestKey});
      await refresh();liquidationDetail(result.id);notify('Liquidación guardada. La caja incluye sólo lo recibido.');
    }
  }catch(error){errors.textContent=error.message;errors.focus();}
  finally{submit.disabled=false;}
}
function liquidationDetail(id){
  const l=state.liquidations.find(l=>l.id===id);
  openDialog('Detalle de liquidación',`<div class="liquidation-wizard"><p><strong>${esc(l.reference)}</strong> · ${esc(state.payers.find(p=>p.id===l.payer)?.name)}</p><p>Dinero recibido vigente: <strong>${pesos(l.received)}</strong></p>
    ${l.allocations.map(a=>`<article class="entry"><h3>${esc(a.concept)}</h3>${a.void?'<p>Prestación anulada: estos importes históricos no integran los totales vigentes.</p>':'<p>Cobros vigentes de la prestación</p>'}<p>Recibido: ${pesos(a.cash)}</p><details><summary>Ver desglose de la prestación</summary><p>Honorarios al cargar: ${pesos(a.generated)} · Incluido: ${pesos(a.allocated)}</p><p>Descuento aceptado: ${pesos(a.discount)} ${esc(a.discount_kind)}</p><p>Retenido: ${pesos(a.retained)} ${esc(a.retention_kind)} (no es caja ni pérdida definitiva)</p><p>Diferencia de esta liquidación: ${pesos(a.difference)}</p><p>Pendiente actual de la prestación: ${pesos(a.pending_now)}. Incluye otros pagos posteriores; no sumes ambos pendientes.</p><p>${esc(a.note)}</p>${button('show:'+a.movement,'Ver prestación y corregir cobros')}</details></article>`).join('')}
    <details><summary>Historial de la liquidación (${l.history.length})</summary>${l.history.map(h=>`<article class="entry"><p>Versión ${h.version} · ${dateText(h.day)} · Recibido registrado: ${pesos(h.received)}</p><p>${esc(h.note||'Carga original')}</p><small>${esc(h.created)} UTC</small><details><summary>Asignaciones de esta versión</summary>${JSON.parse(h.payload).allocations.map(a=>`<p>${esc(state.records.find(r=>r.id===a.movement)?.concept||'Prestación')} · Incluido: ${pesos(a.allocated)} · Recibido: ${pesos(a.cash)} · Descuento: ${pesos(a.discount)} ${esc(a.discount_kind)} · Retenido: ${pesos(a.retained)} ${esc(a.retention_kind)} · Diferencia: ${pesos(a.difference)}</p>`).join('')}</details></article>`).join('')}</details>
    <p class="muted">Los cobros individuales pueden cambiar su importe o fecha. El recibido vigente usa esas correcciones, sin duplicarlas.</p>${button('liquidation-edit:'+id,'Corregir liquidación',true)}${button('liquidations','Volver a liquidaciones')}</div>`);
}
document.addEventListener('change',event=>{
  const article=event.target.closest('.allocation');
  if(!article)return;
  if(event.target.type==='checkbox')article.querySelector('.allocation-fields').hidden=!event.target.checked;
});
document.addEventListener('input',event=>{
  const article=event.target.closest('.allocation');if(!article)return;
  const out=article.querySelector('[data-difference]');
  try{const id=article.dataset.movement;const get=k=>liquidationMoney(article.querySelector(`[name="${k}-${id}"]`).value);const rest=get('allocated')-get('cash')-get('discount')-get('retained');out.textContent=rest<0n?'Los importes superan lo incluido.':'Diferencia por resolver: '+pesos(rest);}catch{out.textContent='Revisá el formato de los importes.';}
});
