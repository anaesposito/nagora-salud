import calendar
import json
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SOURCES = ('Obra social', 'Prepaga', 'Particular', 'Otro')
CATEGORIES = ('Alquiler', 'Servicios', 'Insumos', 'Matrícula profesional', 'Equipamiento', 'Impuestos', 'Software', 'Otros')
ADJUSTMENTS = ('Descuento', 'Retención', 'Débito', 'Ajuste')

def today():
    return datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).date()

def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def initialize(path):
    with connect(path) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript((ROOT / 'migrations/001.sql').read_text())

def money(value):
    value = str(value).strip()
    if not re.fullmatch(r'(?:[0-9]{1,11}|[0-9]{1,3}(?:\.[0-9]{3}){1,3})(?:,[0-9]{1,2})?', value):
        raise ValueError('Ingresá un monto como 70000 o 70.000,50.')
    whole, _, cents = value.replace('.', '').partition(',')
    result = int(whole) * 100 + int(cents.ljust(2, '0'))
    if not 0 < result <= 9999999999999:
        raise ValueError('Ingresá un monto mayor que cero dentro del rango permitido.')
    return result

def day(value, optional=False):
    if optional and not value:
        return None
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value:
            return value
    except (TypeError, ValueError):
        pass
    raise ValueError('Ingresá una fecha válida.')

def label(value, limit=120):
    if not isinstance(value, str) or not 0 < len(value.strip()) <= limit:
        raise ValueError(f'Completá el texto con hasta {limit} caracteres.')
    return value.strip()

def choice(value, options):
    if value not in options:
        raise ValueError('Elegí una opción válida.')
    return value

def audit(db, owner, action, details):
    db.execute('INSERT INTO audit(owner,action,details) VALUES(?,?,?)',
               (owner, action, json.dumps(details, ensure_ascii=False)))

def get_movement(db, owner, ident):
    row = db.execute('SELECT * FROM movement WHERE owner=? AND id=?', (owner, ident)).fetchone()
    if row is None:
        raise LookupError('No encontramos ese movimiento.')
    return dict(row)

def balance(db, record):
    settled, cash = db.execute("""SELECT COALESCE(SUM(amount),0),
        COALESCE(SUM(CASE WHEN reason='Pago' THEN amount ELSE 0 END),0)
        FROM settlement WHERE owner=? AND movement=?""", (record['owner'], record['id'])).fetchone()
    return record['amount'] - settled, cash

def settle(db, owner, record, amount, when, reason):
    if record['void'] or amount <= 0 or amount > balance(db, record)[0]:
        raise ValueError('El importe supera lo que queda pendiente o el movimiento está anulado.')
    if when > today().isoformat():
        raise ValueError('La fecha del pago o ajuste no puede ser futura.')
    db.execute('INSERT INTO settlement(owner,movement,day,amount,reason) VALUES(?,?,?,?,?)',
               (owner, record['id'], when, amount, reason))
    audit(db, owner, 'settlement', dict(movement=record['id'], amount=amount, day=when, reason=reason))

def save_movement(db, owner, data, ident=None):
    before = get_movement(db, owner, ident) if ident else None
    kind = before['kind'] if before else choice(data.get('kind'), ('income','expense'))
    source = choice(data.get('source'), SOURCES if kind == 'income' else CATEGORIES)
    concept, amount = label(data.get('concept')), money(data.get('amount'))
    when, due = day(data.get('day')), day(data.get('due'), True)
    reference = label(data['reference'], 60) if data.get('reference') else None
    payer = None
    if source in SOURCES[:2]:
        entity = db.execute('SELECT id FROM payer WHERE owner=? AND id=? AND kind=?',
                            (owner,data.get('payer'),source)).fetchone()
        if not entity:
            raise ValueError('Elegí una entidad de la lista.')
        payer = entity['id']
    recurrence = int(kind == 'expense' and data.get('recurrence') is True)
    if before and (before['void'] or amount < before['amount'] - balance(db, before)[0]):
        raise ValueError('El monto no puede ser menor que los pagos y ajustes registrados.')
    if before and (before['series'] or before['recurrence']) and when != before['day']:
        raise ValueError('La fecha de un gasto de la serie mensual se mantiene fija.')
    if not data.get('confirm_duplicate') or reference:
        duplicate = db.execute("""SELECT id FROM movement WHERE owner=? AND kind=? AND void=0
            AND id<>? AND source=? AND payer IS ? AND
            ((? IS NOT NULL AND reference=?) OR (? IS NULL AND concept=? AND amount=? AND day=?))""",
            (owner,kind,ident or 0,source,payer,reference,reference,reference,concept,amount,when)).fetchone()
        if duplicate:
            raise ValueError('Ya existe un movimiento similar. Revisalo antes de guardar.' if reference else
                             'Ya existe un movimiento similar. Revisalo o marcá que querés guardar otro.')
    values = (source,concept,amount,when,due,payer,reference,recurrence)
    if before:
        db.execute('UPDATE movement SET source=?,concept=?,amount=?,day=?,due=?,payer=?,reference=?,recurrence=? WHERE owner=? AND id=?',
                   (*values,owner,ident))
    else:
        ident = db.execute('INSERT INTO movement(source,concept,amount,day,due,payer,reference,recurrence,owner,kind) VALUES(?,?,?,?,?,?,?,?,?,?)',
                           (*values,owner,kind)).lastrowid
    record = get_movement(db, owner, ident)
    audit(db,owner,'edit' if before else 'create',dict(before=before,after=record))
    if not before and data.get('paid') is True:
        settle(db, owner, record, amount, day(data.get('paid_day')), 'Pago')
    return ident

def repeat_expenses(db, owner):
    now = today()
    for row in db.execute('SELECT * FROM movement WHERE owner=? AND recurrence=1 AND series IS NULL AND void=0',(owner,)).fetchall():
        start = date.fromisoformat(row['day'])
        for month_index in range(start.year*12+start.month,min(now.year*12+now.month+1, 9999*12+12)):
            year, month = divmod(month_index,12)
            month += 1
            when = date(year,month,min(start.day,calendar.monthrange(year,month)[1])).isoformat()
            exists = db.execute("SELECT 1 FROM movement WHERE owner=? AND series=? AND substr(day,1,7)=?", (owner,row['id'],when[:7])).fetchone()
            if exists:
                continue
            ident = db.execute("""INSERT INTO movement(owner,kind,source,concept,amount,day,due,series)
                VALUES(?,'expense',?,?,?,?,?,?)""",(owner,row['source'],row['concept'],row['amount'],when,when,row['id'])).lastrowid
            audit(db,owner,'recurrence',dict(movement=ident,series=row['id']))

def snapshot(db, owner, month):
    totals = dict(received=0,pending=0,spent=0,activity=0)
    records = []
    for raw in db.execute("""SELECT m.*, p.name AS payer_name FROM movement m LEFT JOIN payer p
        ON p.owner=m.owner AND p.id=m.payer WHERE m.owner=? ORDER BY day DESC,m.id DESC""",(owner,)):
        row = dict(raw)
        row['settlements'] = [dict(s) for s in db.execute(
            'SELECT day,amount,reason FROM settlement WHERE owner=? AND movement=? ORDER BY day,id',(owner,row['id']))]
        row['balance'], row['cash'] = balance(db,row)
        if row['void']:
            row['state'] = 'Anulado'
        else:
            row['state'] = 'Cerrado con ajuste' if not row['balance'] and row['cash'] < row['amount'] else (
                ('Cobrado' if row['kind']=='income' else 'Pagado') if not row['balance'] else
                'Parcialmente cobrado' if row['cash'] else 'Por cobrar' if row['kind']=='income' else 'Por pagar')
            income = row['kind']=='income'
            if income:
                totals['pending'] += row['balance']
            if row['day'].startswith(month):
                totals['activity'] += row['amount'] if income else -row['amount']
            for entry in row['settlements']:
                if entry['day'].startswith(month):
                    if entry['reason']=='Pago':
                        totals['received' if income else 'spent'] += entry['amount']
                    else:
                        totals['activity'] -= entry['amount']
        records.append(row)
    totals['net'] = totals['received'] - totals['spent']
    return records, totals

def seed(db, owner):
    now = today().isoformat()
    for kind, name in [('Obra social','Obra Social Ejemplo'),('Prepaga','Prepaga Ejemplo')]:
        db.execute('INSERT INTO payer(owner,kind,name,days,terms) VALUES(?,?,?,?,?)',(owner,kind,name,30,'Convenio de ejemplo'))
    entities = {r['kind']:r['id'] for r in db.execute('SELECT kind,id FROM payer WHERE owner=?',(owner,))}
    examples = [
        ('income','Particular','Consultas particulares',950000,950000),
        ('income','Prepaga','Liquidación de honorarios',1200000,1200000),
        ('income','Obra social','Liquidación con pago parcial',680000,300000),
        ('income','Obra social','Prestaciones por cobrar',400000,0),
        ('expense','Alquiler','Alquiler del consultorio',700000,700000),
        ('expense','Matrícula profesional','Matrícula profesional',220000,220000),
        ('expense','Impuestos','Próximo vencimiento',110000,0),
    ]
    for kind,source,concept,amount,cash in examples:
        due = (today().fromordinal(today().toordinal()+5)).isoformat() if not cash else None
        ident=save_movement(db,owner,dict(kind=kind,source=source,concept=concept,amount=str(amount),day=now,due=due,payer=entities.get(source)))
        if cash:
            settle(db,owner,get_movement(db,owner,ident),cash*100,now,'Pago')
