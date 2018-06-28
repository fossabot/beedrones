'''
Created on Jun 23, 2017 

@author: darkbk
'''
import os

import logging
import unittest
import pprint
import time
import json
import urllib
import redis
from beecell.logger import LoggerHelper
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from beecell.test.runner import TextTestRunner
from beecell.remote import RemoteClient
from base64 import b64encode
from yaml import load, dump
from beecell.simple import str2uni
from datetime import datetime
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from celery.utils.log import ColorFormatter as CeleryColorFormatter
from celery.utils.term import colored

class ColorFormatter(CeleryColorFormatter):
    #: Loglevel -> Color mapping.
    COLORS = colored().names
    colors = {u'DEBUG': COLORS[u'blue'], 
              u'WARNING': COLORS[u'yellow'],
              u'WARN': COLORS[u'yellow'],
              u'ERROR': COLORS[u'red'], 
              u'CRITICAL': COLORS[u'magenta']}

class BeedronesTestCase(unittest.TestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """    
    logger = logging.getLogger(u'beedrones.test')
    pp = pprint.PrettyPrinter(width=200)
    
    @classmethod
    def setUpClass(cls):
        pass
        #cls._connection = createExpensiveConnectionObject()

    @classmethod
    def tearDownClass(cls):
        pass
        #cls._connection.destroy()

    def load_config(self, file_config, frmt=u'json'):
        f = open(file_config, u'r')
        config = f.read()
        if frmt == u'json':
            config = json.loads(config)
        elif frmt == u'yaml':
            config = data = load(config, Loader=Loader)
        f.close()
        return config

    def setUp(self):
        logging.getLogger(u'beedrones.test')\
               .info(u'========== %s ==========' % self.id()[9:])
        self.start = time.time()
        
        # ssl
        path = os.path.dirname(__file__).replace(u'beedrones/common', u'tests')
        pos = path.find(u'tests')
        path = path[:pos+6]
        # load config
        self.config = self.load_config(u'%s/params.yml' % path, frmt=u'yaml')
        self.platform = self.config.get(u'platform')
        
    def tearDown(self):
        elapsed = round(time.time() - self.start, 4)
        logging.getLogger(u'beedrones.test')\
               .info(u'========== %s ========== : %ss\n' % (self.id()[9:], elapsed))
    
    def open_mysql_session(self, db_uri):
        engine = create_engine(db_uri)
        
        """
        engine = create_engine(app.db_uri,
                               pool_size=10, 
                               max_overflow=10,
                               pool_recycle=3600)
        """
        db_session = sessionmaker(bind=engine, 
                                  autocommit=False, 
                                  autoflush=False)
        return db_session
    
    def convert_timestamp(self, timestamp):
        """
        """
        timestamp = datetime.fromtimestamp(timestamp)
        return str2uni(timestamp.strftime(u'%d-%m-%Y %H:%M:%S.%f'))

def runtest(suite):
    log_file = u'/tmp/test.log'
    watch_file = u'/tmp/test.watch'
    
    logging.captureWarnings(True)    
    
    #setting logger
    #frmt = "%(asctime)s - %(levelname)s - %(process)s:%(thread)s - %(message)s"
    frmt = u'%(asctime)s - %(levelname)s - %(message)s'
    loggers = [
        logging.getLogger(u'beedrones'),
        logging.getLogger(u'beecell'),
        logging.getLogger(u'requests'),
        logging.getLogger(u'urllib3'),
    ]
    LoggerHelper.file_handler(loggers, logging.DEBUG, log_file, frmt=frmt, 
                              formatter=ColorFormatter)
    loggers = [
        logging.getLogger(u'beecell.perf'),
    ]
    LoggerHelper.file_handler(loggers, logging.DEBUG, watch_file, 
                              frmt=u'%(message)s', formatter=ColorFormatter)
    
    # run test suite
    alltests = suite
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
        