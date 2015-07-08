from sqlalchemy import create_engine
from config import app_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from markdown2 import markdown
from datetime import datetime
from html import escape

Base = declarative_base()

engine = create_engine('sqlite:///%s' % app_config.get('app.db.path', ':memory:'), echo=True, encoding='utf-8')
Session = sessionmaker(bind=engine)


class Note(Base):
    __tablename__ = 'notes'

    SOURCE_TYPE_MARKDOWN = 1
    SOURCE_TYPE_HTML = 2
    SOURCE_TYPE_PLAINTEXT = 3

    id = Column(Integer, primary_key=True)
    source = Column(Text)
    _source_type = Column('source_type', Integer)
    _text = Column('text', Text)
    created_at = Column(DateTime)

    def __init__(self, source=None, source_type=None):
        self.source_type = source_type or self.SOURCE_TYPE_PLAINTEXT
        self.text = source
        self.created_at = datetime.now()

    def _update_text(self):
        if self.source is None:
            return
        if self.source_type == self.SOURCE_TYPE_MARKDOWN:
            self._text = markdown(self.source)
        elif self.source_type == self.SOURCE_TYPE_PLAINTEXT:
            self._text = escape(self.source)
        else:
            self._text = self.source

    @hybrid_property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self.source = value
        self._update_text()

    @hybrid_property
    def source_type(self):
        return self._source_type

    @source_type.setter
    def source_type(self, value):
        self._source_type = value
        self._update_text()

    def __repr__(self):
        return "<Note (id='%s', type='%s')>" % (self.id, self.source_type)