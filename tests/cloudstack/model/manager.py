'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibbonutil.perf import watch_test
from gibboncloud.cloudstack.model import ClskManager

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

def open_mysql_engine(db_uri):
    engine = create_engine(db_uri)
    
    """
    engine = create_engine(app.db_uri,
                           pool_size=10, 
                           max_overflow=10,
                           pool_recycle=3600)
    """
    
    db_session = sessionmaker(bind=engine, 
                              autocommit=False, 
                              autoflush=False,)    
    
    return db_session

db_uri = "mysql+pymysql://portal:testlab@172.16.0.19:3308/portal"
db_session = open_mysql_engine(db_uri)

class ClskManagerTestCase(unittest.TestCase):
    logger = logging.getLogger('gibbon.test')
    pp = pprint.PrettyPrinter()

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
    def tearDown(self):
        pass

    @watch_test
    def test_tree(self):       
        if conn:
            """
            query = db.session.query("id", "name", "grp", "type").\
                    from_statement("SELECT t1.id as id, t1.name as name, t2.group as grp, t2.type as type "
                                   "FROM portal.object t1, portal.object_type t2 " 
                                   "WHERE t1.type_id=t2.id").all()
            """
            app.logger.debug("start sleeping")
            #result = conn.execute("SELECT t1.id as id, t1.name as name, t2.group as grp, t2.type as type "
            #        "FROM portal.object t1, portal.object_type t2 " 
            #        "WHERE t1.type_id=t2.id")
            #for row in result:
            #    res.append(str(row))
                   
        
        try:
            session = db_session()
            query = session.query("id", "name", "grp", "type").\
                    from_statement("SELECT t1.id as id, t1.name as name, t2.group as grp, t2.type as type "
                                   "FROM portal.object t1, portal.object_type t2 " 
                                   "WHERE t1.type_id=t2.id").all()
            for row in query:
                res.append(str(row))
            
            self.logger.debug("end sleeping")
            
            session.close()
            
            #fres = self.pp.pformat(res)
            self.logger.debug(res)
        except exc.DBAPIError, e:
            self.logger.error(traceback.format_exc())
            self.fail(e)

def test_suite():
    tests = [
            ]
    return unittest.TestSuite(map(ClskManagerTestCase, tests))

if __name__ == '__main__':
    from tests.test_util import run_test
    run_test([test_suite()])