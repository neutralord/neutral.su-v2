from sqlalchemy import create_engine
from config import app_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pytz import timezone

tzlocal = timezone(app_config.get('app.timezone', 'UTC'))

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
    preview = Column(Text)
    read_more_label = Column(String(255))
    created_at = Column(DateTime)

    def __init__(self, source=None, source_type=None):
        self.source_type = source_type or self.SOURCE_TYPE_PLAINTEXT
        self.text = source
        self.created_at = datetime.now(tzlocal)

    def _update_text(self):
        from markdown2 import Markdown
        from html import escape
        from bs4 import BeautifulSoup
        import re

        if self.source is None:
            return
        if self.source_type == self.SOURCE_TYPE_MARKDOWN:
            class Converter(Markdown):
                def postprocess(self, text):
                    return re.compile(r'^<h1>CUT:?\s*(.*)?</h1>', flags=re.M)\
                        .sub((lambda m: r'<cut title="%s"/>' % escape(m.group(1))), text) # r'<cut title="\1"/>'
            self._text = Converter(extras=['fenced-code-blocks']).convert(self.source)
        elif self.source_type == self.SOURCE_TYPE_PLAINTEXT:
            self._text = escape(self.source)
        else:
            self._text = self.source
        cut = BeautifulSoup(self._text, app_config.get('blog.html_parser')).find('cut')
        self.preview = cut and ''.join(reversed([str(e) for e in cut.previous_siblings]))
        self.read_more_label = cut and cut['title'] or None
        pass

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

    @property
    def title(self):
        import re
        plain_text = re.sub(r'<[^>]+>', '', self.text)
        pos = max(plain_text.find('\n', 0, 50), 0) or max(plain_text.find(' ', 30), 30)
        title = plain_text[:pos].replace("\n", " ").strip(' ')
        return title

    def __repr__(self):
        return "<Note (id='%s', type='%s')>" % (self.id, self.source_type)