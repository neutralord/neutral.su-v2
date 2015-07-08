import bottle
from bottle import request, run, route, get, post, error, TEMPLATE_PATH, jinja2_template, HTTPError
import functools
import bcrypt
from beaker.middleware import SessionMiddleware

from config import app_config
from db import Note, Session

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 3600 * 24,
    'session.data_dir': './data',
    'session.auto': True
}

app = bottle.app()
middleware = SessionMiddleware(app, session_opts)

template = functools.partial(jinja2_template, template_settings={
    'globals': {'app': app, 'request': request, 'url_for': app.router.build},
    'extensions': ['jinja2.ext.with_']
})
TEMPLATE_PATH.append("./templates")


def get_session():
    return request.environ.get('beaker.session')


def post_get(*args, **kwargs):
    return bottle.request.forms.getunicode(*args, **kwargs)


@error(404)
@error(500)
def error_page(err):
    return template('error.html', code=err.status_code)


@route('/', name='index')
def index():
    return template('index.html')


@route('/who', name='about')
def who():
    return template('who.html', site_title='О себе')


@get('/login', name='login')
def login():
    return template('login.html')


@post('/login')
def login():
    username = post_get('username')
    password = post_get('password').encode('utf-8')
    if (username and password) is not None:
        hashed = app_config.get('app.auth.%s' % username).encode('utf-8')
        if bcrypt.hashpw(password, hashed) == hashed:
            s = get_session()
            s['authenticated'] = True
            s['username'] = username
            s.save()
            bottle.redirect('/')
        else:
            return template('login.html')


@route('/notes', name='note-list')
def note_list():
    s = get_session()
    db_session = Session()
    notes = db_session.query(Note).order_by(Note.created_at.desc()).all()
    return template('note/list.html', notes=notes, can_submit=s.get('authenticated'), site_title='Заметки')


@route('/note/<note_id:int>', name='note-details')
def note_details(note_id):
    import re
    s = get_session()
    db_session = Session()
    note = db_session.query(Note).get(note_id)
    if note is None:
        raise HTTPError(404)

    plain_text = re.sub(r'<[^>]+>', '', note.text)
    pos = max(plain_text.find('\n', 0, 50), 0) or max(plain_text.find(' ', 30), 30)
    title = plain_text[:pos].replace("\n", " ").strip(' ')

    return template('note/note.html', note=note, can_submit=s.get('authenticated'), site_title=title)


@get('/note-edit', name='note-edit')
@get('/note-edit/<note_id:int>', name='note-edit-id')
def note_edit(note_id=None):
    s = get_session()
    if not s.get('authenticated'):
        return bottle.redirect('/login')
    note = None
    if note_id is not None:
        db_session = Session()
        note = db_session.query(Note).get(note_id)
    return template('note/edit.html', note=note, types={
        Note.SOURCE_TYPE_MARKDOWN: 'Markdown',
        Note.SOURCE_TYPE_HTML: 'HTML',
        Note.SOURCE_TYPE_PLAINTEXT: 'Plain text',
    })


@post('/note-save', name='note-save')
@post('/note-save/<note_id:int>', name='note-save-id')
def note_save(note_id=None):
    s = get_session()
    if not s.get('authenticated'):
        bottle.redirect(bottle.url('login'))
    note_source = post_get('source')
    source_type = int(post_get('source_type', Note.SOURCE_TYPE_PLAINTEXT))
    db_session = Session()
    if note_id is not None:
        note = db_session.query(Note).get(note_id)
        note.source_type = source_type
        note.text = note_source
    else:
        note = Note(source=note_source, source_type=source_type)
        db_session.add(note)
    db_session.commit()
    bottle.redirect(bottle.url('note-list'))


@get('/note-remove/<note_id:int>', name='note-remove')
def note_remove(note_id=None):
    s = get_session()
    if not s.get('authenticated') or not note_id:
        return bottle.redirect('/login')
    db_session = Session()
    note = db_session.query(Note).get(note_id)
    db_session.delete(note)
    db_session.commit()
    bottle.redirect(bottle.url('note-list'))

debug = app_config.get('app.debug', False)
run(middleware,
    host='localhost',
    port=app_config.get('app.port', 5040),
    server=app_config.get('app.server', 'wsgiref'),
    debug=debug,
    reloader=debug
    )