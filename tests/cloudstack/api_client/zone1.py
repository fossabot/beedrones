'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import os
import pprint
from gibbon_cloud.cloudstack.dso.base import ApiError
from gibbon_cloud.cloudstack.dso.zone import Zone
from gibbon_utility.perf import watch_test 

def suite_Zone():
    tests = ['test_info',
             'test_list',
             'test_list_pods',
             'test_list_clusters',
             'test_tree',
            ]
    return unittest.TestSuite(map(ZoneTestCase, tests))

class ZoneTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibbon_cloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']    
        self.zoneid = params['gibbon_cloud.cloudstack.dso.zone']['zoneid']
        self.podid = params['gibbon_cloud.cloudstack.dso.zone']['podid']
        
        self.server = Zone(base_url, api_key, sec_key)
        
        self.pp = pprint.PrettyPrinter()        
        
    def tearDown(self):
        pass
        #self.logger.debug('\n############ %s.%s ############' % 
        #                  (self.__module__, self.__class__.__name__))

    @watch_test
    def test_info(self):
        try:
            res = self.server.info(self.zoneid)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_list(self):
        try:
            res = self.server.list()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)            
            
    @watch_test
    def test_list_pods(self):
        try:
            res = self.server.list_pods(self.zoneid)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_clusters(self):
        try:
            params = {'command':'listRegions'}
            res = self.server.list_clusters(self.zoneid, self.podid)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_tree(self):
        try:
            res = self.server.tree()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)