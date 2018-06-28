'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibbon_cloud.cloudstack.dso.audit import Audit, ApiError

from gibbon_utility.perf import watch_test 

def suite_Audit():
    tests = [
             'test_list_events1',
             'test_list_events2',
             'test_list_events3',
            ]
    return unittest.TestSuite(map(AuditTestCase, tests))

class AuditTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibbon_cloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        
        self.level = params['gibbon_cloud.cloudstack.dso.audit']['level']
        self.account = params['gibbon_cloud.cloudstack.dso.audit']['account_name']
        self.domain_id = params['gibbon_cloud.cloudstack.dso.audit']['domain_id']
        self.startdate = params['gibbon_cloud.cloudstack.dso.audit']['startdate']
        self.enddate = params['gibbon_cloud.cloudstack.dso.audit']['enddate']
        
        self.audit = Audit(base_url, api_key, sec_key)
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_list_events1(self):
        try:
            res = self.audit.list_events()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_list_events2(self):
        try:
            res = self.audit.list_events(startdate=self.startdate, 
                                         enddate=self.enddate, 
                                         account=self.account, 
                                         domain_id=self.domain_id)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_list_events3(self):
        try:
            res = self.audit.list_events(level=self.level)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)              