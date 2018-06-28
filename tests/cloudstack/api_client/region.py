'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Region, Orchestrator
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class RegionTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        regionid = '1'
        self.region = Region(self.api_client, oid=regionid)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)        
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_info(self):
        res = self.region.info()

def test_suite():
    tests = [
             'test_info',
            ]
    return unittest.TestSuite(map(RegionTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])