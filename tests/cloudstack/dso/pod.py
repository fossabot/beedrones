'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibbon_cloud.cloudstack.dso.base import ApiClient
from gibbon_cloud.cloudstack.dso.virtual_machine import ClskObjectError
from gibbon_cloud.cloudstack.dso.pod import Pod
from gibbon_utility.perf import watch_test

class PodTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibbon_cloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        oid = '8fa0bf8d-64fb-4192-97f0-467f352b2963'
        
        api_client = ApiClient(base_url, api_key, sec_key)
        self.pod = Pod(api_client, oid=oid)
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        try:
            res = self.pod.info()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_clusters(self):
        try:
            res = self.pod.list_clusters()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)          

    @watch_test
    def test_tree(self):
        try:
            res = self.pod.tree()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = ['test_info',
             'test_list_clusters',
             'test_tree',
            ]
    return unittest.TestSuite(map(PodTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbon_utility.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)  