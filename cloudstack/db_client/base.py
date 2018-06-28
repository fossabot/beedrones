'''
Created on Apr 18, 2014

@author: darkbk
'''
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def create_table(self):
    """Create all tables in the engine. This is equivalent to "Create Table"
    statements in raw SQL."""
    engine = self._conn_manager.get_engine()
    Base.metadata.create_all(engine)

def remove_table(self):
    """ Remove all tables in the engine. This is equivalent to "Drop Table"
    statements in raw SQL."""
    engine = self._conn_manager.get_engine()
    Base.metadata.drop_all(engine)