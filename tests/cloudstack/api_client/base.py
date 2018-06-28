'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
import time
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class ApiClientTestCase(CloudTestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_send_api_request1(self):
        params = {'command':'listRegions'}
        res = self.api_client.send_api_request(params)

    def test_send_api_request2(self):
        params = {'command':'listRegions'}
        self.api_client.set_gevent_async(False)
        res = self.api_client.send_api_request(params)
        
    def test_query_async_jobresult(self):
        clsk_job_id = ''
        res = self.api_client.query_async_job(clsk_job_id)
        self.logger.debug(res)    

    def test_list_aync_jobs(self):
        domainid = 'ae3fad3c-d518-11e3-8225-0050560203f1' #'b07b93ba-e402-42bf-8a5c-d9542f41be2a'
        account = 'admin' #'OASIS'
        isrecursive = False
        startdate = '2014-07-17'
        res = self.api_client.list_async_jobs(account=account, domainid=domainid, isrecursive=isrecursive)
        self.logger.debug(self.pp.pformat(res))
        res = self.api_client.list_async_jobs()
        self.logger.debug(self.pp.pformat(res))  

    def test_list_apis(self):
        res = self.api_client.list_apis()

def test_suite():
    tests = [
             'test_send_api_request1',
             'test_send_api_request2',
             #'test_query_async_jobresult',
             #'test_list_aync_jobs',
             #'test_list_apis',
            ]
    return unittest.TestSuite(map(ApiClientTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])         