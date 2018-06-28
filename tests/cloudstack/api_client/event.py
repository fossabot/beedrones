'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
from gibboncloud.cloudstack.api_client import ClskOrchestrator
from tests.test_util import run_test, CloudTestCase

class EventTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        self.system = ClskOrchestrator(self.api_client, name='clsk43', oid='clsk43', active=True)
        self.event = self.system.list_events(oid='1706fb79-e430-4da2-bc82-4c000fab0b98')[0]
        
    def tearDown(self):
        pass

    def test_get(self):
        self.logger.debug(self.event.__dict__)

    def test_archive(self):
        res = self.event.archive()

    def test_delete(self):
        res = self.event.delete()
        self.logger.debug(res)

def test_suite():
    tests = [
             'test_get',
             'test_archive',
             'test_delete',
            ]
    return unittest.TestSuite(map(EventTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])