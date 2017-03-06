import bottle
from bottle import request, response, run, route, get, post, error, TEMPLATE_PATH, jinja2_template, HTTPError
import functools
import bcrypt
from beaker.middleware import SessionMiddleware
import re

from config import app_config
from db import Note, Session

bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 3600 * 24,
    'session.data_dir': './data',
    'session.auto': True
}

app = bottle.app()
middleware = SessionMiddleware(app, session_opts)


def strip_cut(s):
    return re.sub(r'<cut title="[^"]*"/>', '<span id="cut"></span>', s)


def header_into_link(s, note_id):
    url = app.router.build('note-details', note_id=note_id)
    return re.sub(r'(<h[12]>)([^<]+)<', r'\g<1><a href="' + url + '">\g<2></a><', s, 1)

template = functools.partial(jinja2_template, template_settings={
    'globals': {
        'app': app,
        'request': request,
        'url_for': app.router.build,
        'app_config': app_config,
    },
    'filters': {
        'strip_cut': strip_cut,
        'header_into_link': header_into_link
    },
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


@route('/me', name='about')
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
    s = get_session()
    db_session = Session()
    note = db_session.query(Note).get(note_id)
    if note is None:
        raise HTTPError(404)
    return template('note/note.html', note=note, can_submit=s.get('authenticated'), site_title=note.title)


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
    is_draft = bool(post_get('is_draft', False))
    db_session = Session()
    if note_id is not None:
        note = db_session.query(Note).get(note_id)
        note.source_type = source_type
        note.is_draft = is_draft
        note.text = note_source
    else:
        note = Note(source=note_source, source_type=source_type, is_draft=is_draft)
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


@get('/atom.xml', name='note-feed')
def note_feed():
    from pyatom import AtomFeed
    site_url = '://'.join(request.urlparts[:2])
    author = app_config.get('feed.author')
    db_session = Session()
    notes = db_session.query(Note).order_by(Note.created_at.desc()).limit(10).all()
    feed = AtomFeed(title=app_config.get('feed.title'),
                    subtitle=app_config.get('feed.subtitle'),
                    feed_url=site_url + app.get_url('note-feed'),
                    url=site_url + app.get_url('note-list'),
                    author=author)
    for note in [n for n in notes if not n.is_draft]:
        feed.add(title=note.title,
                 content=strip_cut(note.text),
                 content_type="html",
                 author=author,
                 url=site_url + app.get_url('note-details', note_id=note.id),
                 updated=note.created_at)
    response.add_header('Content-Type', 'application/atom+xml')
    return feed.to_string()


debug = app_config.get('app.debug', False)

if __name__ == '__main__':
    run(middleware,
        host='localhost',
        port=app_config.get('app.port', 5040),
        server=app_config.get('app.server', 'wsgiref'),
        debug=debug,
        reloader=debug
        )
else:
    application = middleware