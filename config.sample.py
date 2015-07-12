from bottle import ConfigDict

app_config = ConfigDict()
app_config.load_dict({
    'app': {
        'debug': True,
        'timezone': 'Europe/Moscow',
        'server': 'tornado',
        'port': 5040,
        'auth': {
            'admin': '$2a$10$YOUR-BCRYPT-HASH'
        },
        'db': {
            'path': './data/sqlite.db'
        }
    },
    'feed': {
        'author': 'Nikita Dementev',
        'title': 'Neutral notes',
        'subtitle': 'О коде и погоде',
    },
    'deploy': {
        'production': {
            'host': 'admin@example.com',
            'key_file': '~/.ssh/same_rsa',
            'target_dir': '~/www/example.com'
        }
    }
})