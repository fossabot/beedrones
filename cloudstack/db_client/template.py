'''
Created on Jan 31, 2014

@author: darkbk
'''
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .decorator import transaction, query
from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.types import BigInteger, SmallInteger

Base = declarative_base()

try:
    from beecell.uwsgi_sys.perf import watch
except:
    from beecell.perf import watch
    
class VmTemplate(Base):
    __tablename__ = 'vm_template'
    __table_args__ = {'mysql_engine':'InnoDB'}

    id = Column(Integer, primary_key=True)
    unique_name = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    uuid = Column(String(40), nullable=False)
    public = Column(Integer, primary_key=True)
    featured = Column(Integer, primary_key=True)
    type = Column(String(32), nullable=False)
    hvm = Column(Integer, primary_key=True)
    bits = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    format = Column(String(32), nullable=False)
    created = Column(DateTime, nullable=False)
    removed = Column(DateTime, nullable=False)
    account_id = Column(BigInteger, nullable=False)
    checksum = Column(String(255), nullable=False)
    display_text = Column(String(4096), nullable=False)
    enable_password = Column(SmallInteger, primary_key=True)
    enable_sshkey = Column(SmallInteger, primary_key=True)
    guest_os_id = Column(BigInteger, nullable=False)
    bootable = Column(SmallInteger, nullable=False)
    prepopulate = Column(SmallInteger, nullable=False)
    cross_zones = Column(SmallInteger, nullable=False)
    extractable = Column(SmallInteger, nullable=False)
    hypervisor_type = Column(String(32), nullable=False)
    source_template_id = Column(BigInteger, nullable=False)
    template_tag = Column(String(255), nullable=False)
    sort_key = Column(BigInteger, nullable=False)
    size = Column(BigInteger, nullable=False)
    state = Column(String(255), nullable=False)
    update_count = Column(BigInteger, nullable=False)
    updated = Column(DateTime, nullable=False)
    dynamically_scalable = Column(SmallInteger, nullable=False)

    def __repr__(self):
        return "<Template(%s, %s, %s)>" % (self.id, self.name, self.uuid)

class TmplManagerError(Exception): pass
class TmplManager(object):
    """
    """
    logger = logging.getLogger('gibbon.cloud.db')
    
    def __init__(self, session):
        """ """
        self._session = session
    
    @staticmethod
    def create_table(db_uri):
        """Create all tables in the engine. This is equivalent to "Create Table"
        statements in raw SQL."""
        try:
            engine = create_engine(db_uri)
            Base.metadata.create_all(engine)
            del engine
        except exc.DBAPIError, e:
            raise TmplManagerError(e)
    
    @staticmethod
    def remove_table(db_uri):
        """ Remove all tables in the engine. This is equivalent to "Drop Table"
        statements in raw SQL."""
        try:
            engine = create_engine(db_uri)
            Base.metadata.drop_all(engine)
            del engine
        except exc.DBAPIError, e:
            raise TmplManagerError(e)

    @watch
    def set_initial_data(self):
        """Set initial data.
        """
        @transaction(self._session)
        def set_initial_data_inner(session):
            pass
        return set_initial_data_inner()
    
    def get_template(self, tid):
        @query(self._session)
        def get_template_inner(session):
            device = session.query(VmTemplate).filter_by(uuid=tid).first()
            return device
        return get_template_inner()