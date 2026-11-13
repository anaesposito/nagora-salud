import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import ssl
import time
from contextlib import closing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

from domain import *

ASSETS = {'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
AUTH_WINDOW = 900
RECOVERY_LIFETIME = 30 * 86400


def allow_auth(database, address, email, now=None):
    """Persist counters separately so rejected credentials cannot roll them back."""
    now = int(time.time()) if now is None else now
    buckets = [('ip:' + address, 100)]
    if isinstance(email, str):
        buckets.append(('account:' + email.strip().lower(), 20))
    with closing(connect(database)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM auth_attempt WHERE started<=?', (now - AUTH_WINDOW,))
        allowed = True
        for value, limit in buckets:
            bucket = hashlib.sha256(value.encode()).hexdigest()
            db.execute('INSERT INTO auth_attempt VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET attempts=attempts+1', (bucket, now))
            if db.execute('SELECT attempts FROM auth_attempt WHERE bucket=?', (bucket,)).fetchone()[0] > limit:
                allowed = False
        return allowed

def password(value, salt):
    return hashlib.scrypt(value.encode(), salt=bytes.fromhex(salt), n=32768, r=8, p=1, maxmem=64*1024*1024).hex()

def encode_password(value):
    salt = secrets.token_hex(16)
    return salt + ':' + password(value,salt)

def read_password(value, minimum=12):
    if not isinstance(value, str) or not minimum <= len(value) <= 128:
        raise ValueError('Usá una contraseña de entre 12 y 128 caracteres.')
    return value

def valid_password(value, stored):
    salt, digest = stored.split(':')
    return hmac.compare_digest(password(value,salt),digest)

class App(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        # Do not record query strings, account identifiers, cookies or bodies.
        self.log_message('request %s %s', self.command, code)

    def respond(self, status, payload, mime='application/json', cookie=None):
        body = json.dumps(payload, ensure_ascii=False).encode() if mime=='application/json' else payload
        self.send_response(status)
        self.send_header('Content-Type',mime+'; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if self.server.secure:
            self.send_header('Strict-Transport-Security','max-age=31536000')
        if cookie:
            self.send_header('Set-Cookie',cookie)
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def cookie(self, token, duration=604800):
        return f'nagora={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={duration}' + ('; Secure' if self.server.secure else '')

    def do_GET(self):
        self.handle_route(False)

    def do_POST(self):
        self.handle_route(True)

    def handle_route(self, write):
        parsed = urlsplit(self.path)
        path = parsed.path
        try:
            if not write and path=='/api/config':
                self.respond(200,{'demoOnly':self.server.demo_only})
                return
            if not write and path in ASSETS:
                filename,mime = ASSETS[path]
                self.respond(200,(ROOT/'static'/filename).read_bytes(),mime)
                return
            data = {}
            if write:
                if self.headers.get('Origin') != self.server.origin:
                    self.respond(403,{'error':'La solicitud debe salir de Nagora Salud.'})
                    return
                length = int(self.headers.get('Content-Length','0'))
                if self.headers.get_content_type()!='application/json' or not 0 < length <= 16384:
                    raise ValueError('La solicitud tiene un formato o tamaño inválido.')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data,dict):
                    raise ValueError('Solicitud inválida.')
                if path in ('/api/login', '/api/register', '/api/reset', '/api/recovery', '/api/demo'):
                    if not allow_auth(self.server.database, self.client_address[0], data.get('email')):
                        self.respond(429, {'error':'Hubo muchos intentos. Esperá 15 minutos y volvé a intentar.'})
                        return
            with closing(connect(self.server.database)) as db, db:
                if write or path=='/api/state':
                    db.execute('BEGIN IMMEDIATE')
                result,cookie = self.route(db,path,write,data,parse_qs(parsed.query))
            self.respond(200,result,cookie=cookie)
        except PermissionError:
            self.respond(401,{'error':'Ingresá a tu cuenta para continuar.'})
        except LookupError as error:
            self.respond(404,{'error':str(error)})
        except (ValueError, TypeError, sqlite3.IntegrityError) as error:
            message = 'Ya existe un registro con esos datos.' if isinstance(error,sqlite3.IntegrityError) else str(error)
            self.respond(400,{'error':message})
        except Exception as error:
            self.log_error('request_failed %s',type(error).__name__)
            self.respond(500,{'error':'No pudimos completar la operación. Probá de nuevo.'})

    def route(self,db,path,write,data,query):
        cookie = SimpleCookie(self.headers.get('Cookie',''))
        token = cookie['nagora'].value if 'nagora' in cookie else ''
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        account = db.execute('SELECT a.* FROM account a JOIN session s ON a.id=s.owner WHERE s.token=? AND s.expires>?',
                             (token_hash,int(time.time()))).fetchone()
        if write and self.server.demo_only and path in ('/api/register','/api/login','/api/reset'):
            raise LookupError('Esta versión está habilitada para probar con datos de ejemplo.')
        if write and path=='/api/reset':
            email=label(data.get('email'),254).lower()
            code=label(data.get('code'),64)
            new_secret=read_password(data.get('password'))
            recovery=db.execute('SELECT a.id,r.digest FROM account a JOIN recovery r ON a.id=r.owner WHERE a.email=? AND a.demo=0 AND r.expires>?',(email,int(time.time()))).fetchone()
            digest=hashlib.sha256(code.encode()).hexdigest()
            if not recovery or not hmac.compare_digest(digest,recovery['digest']):
                raise ValueError('El correo o código de recuperación es incorrecto.')
            db.execute('UPDATE account SET secret=? WHERE id=?',(encode_password(new_secret),recovery['id']))
            db.execute('DELETE FROM session WHERE owner=?',(recovery['id'],))
            db.execute('DELETE FROM recovery WHERE owner=?',(recovery['id'],))
            return {'ok':True},self.cookie('',0)
        if write and path in ('/api/register','/api/login','/api/demo'):
            if path=='/api/demo':
                owner=db.execute('INSERT INTO account(email,name,secret,demo) VALUES(?,?,?,1)',
                                 (secrets.token_hex(16)+'@demo.invalid','Martín López','')).lastrowid
                seed(db,owner)
            else:
                email = label(data.get('email'),254).lower()
                if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
                    raise ValueError('Ingresá un correo válido.')
                secret = read_password(data.get('password'),12 if path=='/api/register' else 1)
                if path=='/api/register':
                    owner=db.execute('INSERT INTO account(email,name,secret) VALUES(?,?,?)',
                                     (email,label(data.get('name')),encode_password(secret))).lastrowid
                else:
                    row=db.execute('SELECT * FROM account WHERE email=? AND demo=0',(email,)).fetchone()
                    stored=row['secret'] if row else '0'*32+':'+'0'*128
                    if not valid_password(secret,stored) or not row:
                        raise ValueError('El correo o la contraseña son incorrectos.')
                    owner=row['id']
            token=secrets.token_urlsafe(32)
            db.execute('DELETE FROM session WHERE token=? OR expires<=?',(token_hash,int(time.time())))
            db.execute('INSERT INTO session VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),owner,int(time.time())+604800))
            return {'ok':True},self.cookie(token)
        if not account:
            raise PermissionError
        owner=account['id']
        if write and path=='/api/logout':
            db.execute('DELETE FROM session WHERE token=?',(token_hash,))
            return {'ok':True},self.cookie('',0)
        if not write and path=='/api/state':
            month=query.get('month',[today().isoformat()[:7]])[0]
            day(month+'-01')
            repeat_expenses(db,owner)
            records,totals=snapshot(db,owner,month)
            return dict(profile=dict(name=account['name'],demo=bool(account['demo'])),records=records,totals=totals,
                        payers=[dict(r) for r in db.execute('SELECT * FROM payer WHERE owner=? ORDER BY name',(owner,))],
                        reminders=[dict(r) for r in db.execute('SELECT * FROM reminder WHERE owner=? AND done=0 ORDER BY day',(owner,))],
                        today=today().isoformat(),month=month),None
        if not write:
            raise LookupError('Página inexistente.')
        if path=='/api/recovery':
            current=read_password(data.get('password'),1)
            if account['demo'] or not valid_password(current,account['secret']):
                raise ValueError('La contraseña es incorrecta.')
            code=secrets.token_urlsafe(24)
            expires = int(time.time()) + RECOVERY_LIFETIME
            db.execute('INSERT OR REPLACE INTO recovery(owner,digest,expires) VALUES(?,?,?)',(owner,hashlib.sha256(code.encode()).hexdigest(),expires))
            return {'code':code,'expires':expires},None
        key = label(data.get('key'),80)
        if db.execute('SELECT 1 FROM request WHERE owner=? AND key=?',(owner,key)).fetchone():
            return {'ok':True},None
        db.execute('INSERT INTO request VALUES(?,?)',(owner,key))
        match = re.fullmatch(r'/api/movements/([0-9]{1,15})/(edit|settle|void|remind)',path)
        if path=='/api/movements':
            save_movement(db,owner,data)
        elif match:
            ident,action=int(match[1]),match[2]
            record=get_movement(db,owner,ident)
            if action=='edit':
                save_movement(db,owner,data,ident)
            elif action=='settle':
                reason=choice(data.get('reason'),('Pago',*ADJUSTMENTS) if record['kind']=='income' else ('Pago',))
                settle(db,owner,record,money(data.get('amount')),day(data.get('day')),reason)
            elif action=='void':
                if not record['void']:
                    db.execute('UPDATE movement SET void=1 WHERE owner=? AND id=?',(owner,ident))
                    audit(db,owner,'void',dict(movement=ident,reason=label(data.get('note'))))
            elif action=='remind':
                if record['void'] or not balance(db,record)[0]:
                    raise ValueError('El movimiento ya está cerrado.')
                db.execute('INSERT INTO reminder(owner,movement,day,note) VALUES(?,?,?,?)',
                           (owner,ident,day(data.get('day')),label(data.get('note'))))
        elif re.fullmatch(r'/api/reminders/[0-9]{1,15}',path):
            result=db.execute('UPDATE reminder SET done=1 WHERE owner=? AND id=?',(owner,int(path.split('/')[-1])))
            if not result.rowcount:
                raise LookupError('No encontramos el recordatorio.')
        elif path=='/api/payers':
            kind=choice(data.get('kind'),SOURCES[:2])
            name=label(data.get('name'))
            days=int(data.get('days','30'))
            if not 0<=days<=730:
                raise ValueError('Ingresá un plazo entre 0 y 730 días.')
            terms=label(data.get('terms'),500) if data.get('terms') else ''
            db.execute('INSERT INTO payer(owner,kind,name,days,terms) VALUES(?,?,?,?,?)',(owner,kind,name,days,terms))
        elif path=='/api/profile':
            db.execute('UPDATE account SET name=? WHERE id=?',(label(data.get('name')),owner))
        else:
            raise LookupError('Página inexistente.')
        return {'ok':True},None

def make_server(database,host='127.0.0.1',port=8000,cert=None,key=None):
    argentina_timezone()
    initialize(database)
    server=ThreadingHTTPServer((host,port),App)
    server.database=database
    server.demo_only=os.getenv('NAGORA_DEMO_ONLY')=='1'
    server.secure=bool(cert) or os.getenv('RENDER')=='true'
    if cert:
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert,key)
        server.socket=context.wrap_socket(server.socket,server_side=True)
    scheme='https' if cert else 'http'
    server.origin=os.getenv('NAGORA_ORIGIN') or os.getenv('RENDER_EXTERNAL_URL') or f'{scheme}://{host}:{server.server_port}'
    return server

if __name__=='__main__':
    os.umask(0o077)
    with make_server(os.getenv('NAGORA_DB','nagora.sqlite3'),host=os.getenv('NAGORA_HOST','127.0.0.1'),
                     port=int(os.getenv('PORT',os.getenv('NAGORA_PORT','8000'))),
                     cert=os.getenv('NAGORA_CERT'),key=os.getenv('NAGORA_KEY')) as server:
        print(f'Nagora Salud en {server.origin}',flush=True)
        server.serve_forever()
