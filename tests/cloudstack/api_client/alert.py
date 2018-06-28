'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
from gibboncloud.cloudstack.api_client import ClskOrchestrator
from tests.test_util import run_test, CloudTestCase

class AlertTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        self.system = ClskOrchestrator(self.api_client, name='clsk43', oid='clsk43', active=True)
        self.alert = self.system.list_alerts(oid='35ce3f47-5dee-457c-9115-81c54e81453b')[0]
        
    def tearDown(self):
        pass

    def test_get(self):
        self.logger.debug(self.alert.__dict__)

    def test_archive(self):
        res = self.alert.archive()

    def test_delete(self):
        res = self.alert.delete()

def test_suite():
    tests = [
             'test_get',
             'test_archive',
             'test_delete',
            ]
    return unittest.TestSuite(map(AlertTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])