'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import os
import pprint
from gibbon_cloud.cloudstack.dso.base import ApiClient, ApiError
from gibbon_utility.perf import watch_test 

class ApiClientTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibbon_cloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        self.pp = pprint.PrettyPrinter()
        self.server = ApiClient(base_url, api_key, sec_key)
        
    def tearDown(self):
        pass

    @watch_test
    def test_send_api_request(self):
        try:
            params = {'command':'listRegions'}
            res = self.server.send_api_request(params)
            self.logger.debug(res)
        except ApiError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [
             'test_send_api_request',
            ]
    return unittest.TestSuite(map(ApiClientTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbon_utility.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)            