"""Manual statements. Call mutations inside the HTTP BEGIN IMMEDIATE transaction."""
import hashlib
import json
from domain import money, day, label, choice, today, audit, get_movement, balance, PaymentConflict

DISCOUNTS = ('Descuento aceptado', 'Comisión aceptada', 'Débito aceptado')
RETENTIONS = ('Tributaria', 'Contractual', 'Por clasificar')
METHODS = ('Transferencia', 'Efectivo', 'Cheque acreditado', 'Otro')

def amount(value):
    # Strings only, same Argentine exact-cent parser as existing payments; no floats.
    if not isinstance(value, str):
        raise ValueError('Ingresá los importes como texto, con hasta dos decimales.')
    if value.strip() in ('0', '0,0', '0,00'):
        return 0
    return money(value)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def current(db, owner, ident):
    header = db.execute('SELECT * FROM liquidation WHERE owner=? AND id=?', (owner, ident)).fetchone()
    if not header:
        raise LookupError('No encontramos esa liquidación.')
    revision = dict(db.execute('SELECT * FROM liquidation_revision WHERE owner=? AND liquidation=? ORDER BY version DESC LIMIT 1', (owner,ident)).fetchone())
    rows = []
    for raw in db.execute('SELECT * FROM liquidation_allocation WHERE owner=? AND liquidation=? AND version=? ORDER BY movement', (owner,ident,revision['version'])):
        row = dict(raw)
        row['cash'] = row['discount'] = row['retained'] = 0
        row['payments'] = []
        for entry in db.execute('''SELECT e.component,s.* FROM liquidation_entry e JOIN effective_settlement s
            ON e.owner=s.owner AND e.settlement=s.id WHERE e.owner=? AND e.liquidation=? AND e.version=? AND e.movement=?''', (owner,ident,revision['version'],row['movement'])):
            row[entry['component']] += entry['amount']
            row['payments'].append(dict(entry))
        row['difference'] = row['allocated']-row['cash']-row['discount']-row['retained']
        movement = get_movement(db,owner,row['movement'])
        row['concept'], row['pending_now'], row['void'] = movement['concept'], balance(db,movement)[0], bool(movement['void'])
        rows.append(row)
    result = dict(header)
    result.update(version=revision['version'],day=revision['day'],method=revision['method'],received_original=revision['received'],
                  received=sum(r['cash'] for r in rows if not r['void']),allocations=rows)
    result['token'] = digest(dict(version=revision['version'],rows=rows))
    result['history'] = [dict(r) for r in db.execute('SELECT version,day,received,method,note,payload,created FROM liquidation_revision WHERE owner=? AND liquidation=? ORDER BY version', (owner,ident))]
    return result

def list_liquidations(db, owner):
    return [current(db,owner,r['id']) for r in db.execute('SELECT id FROM liquidation WHERE owner=? ORDER BY id DESC',(owner,))]

def save_liquidation(db, owner, data, ident=None):
    if not db.in_transaction:
        raise RuntimeError('Liquidations require an active write transaction')
    key = label(data.get('key'),80)
    payer = data.get('payer')
    if type(payer) is not int or not db.execute('SELECT 1 FROM payer WHERE owner=? AND id=?',(owner,payer)).fetchone():
        raise LookupError('No encontramos ese pagador.')
    reference = label(data.get('reference'),60)
    when = day(data.get('day'))
    if when > today().isoformat():
        raise ValueError('La fecha de acreditación no puede ser futura.')
    received = amount(data.get('received'))
    method = choice(data.get('method'), METHODS)
    note = label(data.get('note')) if ident else ''
    entries = data.get('allocations')
    if not isinstance(entries,list) or not 1 <= len(entries) <= 30:
        raise ValueError('Elegí entre una y treinta prestaciones existentes.')
    rows, seen = [], set()
    for item in entries:
        if not isinstance(item,dict) or type(item.get('movement')) is not int:
            raise ValueError('Revisá las prestaciones elegidas.')
        movement = item['movement']
        if movement in seen:
            raise ValueError('Una prestación no puede repetirse en la liquidación.')
        seen.add(movement)
        values = {k:amount(item.get(k)) for k in ('allocated','cash','discount','retained','difference')}
        if not values['allocated'] or values['allocated'] != sum(values[k] for k in ('cash','discount','retained','difference')):
            raise ValueError('El importe incluido debe coincidir con recibido, descuentos, retenciones y diferencia.')
        discount_kind = choice(item.get('discount_kind'),DISCOUNTS) if values['discount'] else ''
        retention_kind = choice(item.get('retention_kind'),RETENTIONS) if values['retained'] else ''
        explanation = label(item.get('note')) if values['difference'] or values['retained'] or values['discount'] else ''
        rows.append(dict(movement=movement,**values,discount_kind=discount_kind,retention_kind=retention_kind,note=explanation))
    rows.sort(key=lambda r:r['movement'])
    if sum(r['cash'] for r in rows) != received:
        raise ValueError('La suma recibida por prestación debe coincidir exactamente con el dinero recibido.')
    if sum(r['allocated'] for r in rows)>9999999999999:
        raise ValueError('La liquidación supera el rango de importes permitido.')
    payload = dict(id=ident,payer=payer,reference=reference,day=when,received=received,method=method,note=note,
                   version=data.get('version'),token=data.get('token'),allocations=rows)
    fingerprint = digest(payload)
    old = current(db,owner,ident) if ident else None
    replay = db.execute('SELECT liquidation,version,fingerprint FROM liquidation_revision WHERE owner=? AND key=?',(owner,key)).fetchone()
    if replay:
        if replay['fingerprint']!=fingerprint:
            raise PaymentConflict('Esta solicitud ya se usó para otro cambio.')
        return dict(id=replay['liquidation'],version=replay['version'])
    if db.execute('SELECT 1 FROM request WHERE owner=? AND key=?',(owner,key)).fetchone():
        raise PaymentConflict('Esta solicitud ya se usó para otro cambio.')
    if old:
        if type(data.get('version')) is not int or data['version']!=old['version'] or data.get('token')!=old['token']:
            raise PaymentConflict('La liquidación o sus cobros cambiaron. Volvé a abrir el detalle.')
        if (payer,reference)!=(old['payer'],old['reference']):
            raise ValueError('El pagador y la referencia identifican la liquidación y se conservan al corregir.')
        if any(r['void'] for r in old['allocations']):
            raise PaymentConflict('Una prestación fue anulada; revisá sus registros antes de corregir.')
    elif db.execute('SELECT 1 FROM liquidation WHERE owner=? AND payer=? AND reference=?',(owner,payer,reference)).fetchone():
        raise PaymentConflict('Esa liquidación ya está registrada. Abrila para corregirla.')
    for row in rows:
        record = get_movement(db,owner,row['movement'])
        if record['kind']!='income' or record['payer']!=payer or record['void']:
            raise ValueError('Elegí prestaciones vigentes del mismo pagador.')
        restored = sum(r['cash']+r['discount']+r['retained'] for r in old['allocations'] if r['movement']==record['id']) if old else 0
        if row['allocated']>balance(db,record)[0]+restored:
            raise PaymentConflict('El importe incluido supera el saldo disponible. Actualizá las prestaciones.')
        row['generated']=record['amount']
    db.execute('INSERT INTO request VALUES(?,?)',(owner,key))
    if not ident:
        ident=db.execute('INSERT INTO liquidation(owner,payer,reference) VALUES(?,?,?)',(owner,payer,reference)).lastrowid
    version=old['version']+1 if old else 1
    db.execute('''INSERT INTO liquidation_revision(owner,liquidation,version,key,fingerprint,day,received,method,note,payload)
        VALUES(?,?,?,?,?,?,?,?,?,?)''',(owner,ident,version,key,fingerprint,when,received,method,note,json.dumps(payload,ensure_ascii=False)))
    for row in rows:
        db.execute('''INSERT INTO liquidation_allocation(owner,liquidation,version,movement,generated,allocated,cash,discount,retained,difference,discount_kind,retention_kind,note)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(owner,ident,version,*(row[k] for k in ('movement','generated','allocated','cash','discount','retained','difference','discount_kind','retention_kind','note'))))
        for component,reason in [('cash','Pago'),('discount','Descuento'),('retained','Retención')]:
            if row[component]:
                payment=db.execute('INSERT INTO settlement(owner,movement,day,amount,reason) VALUES(?,?,?,?,?)',(owner,row['movement'],when,row[component],reason)).lastrowid
                db.execute('INSERT INTO liquidation_entry VALUES(?,?,?,?,?,?)',(owner,ident,version,row['movement'],payment,component))
    audit(db,owner,'liquidation_correct' if old else 'liquidation_create',dict(liquidation=ident,version=version,note=note,before=old,after=payload))
    return dict(id=ident,version=version)

def payment_capacity(db, owner, payment):
    entry=db.execute('SELECT * FROM liquidation_entry WHERE owner=? AND settlement=?',(owner,payment)).fetchone()
    if not entry:
        return None
    statement=current(db,owner,entry['liquidation'])
    row=next((r for r in statement['allocations'] if r['movement']==entry['movement']),None)
    if statement['version']!=entry['version'] or row is None:
        raise PaymentConflict('Este cobro pertenece a una versión anterior de la liquidación.')
    return row['allocated']-row['discount']-row['retained']
