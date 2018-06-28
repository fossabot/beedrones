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
from gibbon_cloud.cloudstack.dso.virtual_machine import VirtualMachine
from gibbon_utility.perf import watch_test

class VirtualMachineTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibbon_cloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        
        vm_id = '82a6c361-9a48-4a52-85b5-153dcb26f025'
        vm_id = 'ee1d5b09-cd98-47db-9125-dba4a1002718'
        self.hostid = 'faf286be-9413-4677-9e28-9c90987f09e5'
        
        api_client = ApiClient(base_url, api_key, sec_key)
        self.vm = VirtualMachine(api_client, oid=vm_id)
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        try:
            res = self.vm.info()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_start(self):
        try:
            res = self.vm.start()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_stop(self):
        try:
            res = self.vm.stop()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_migrate(self):
        try:
            res = self.vm.migrate(hostid=self.hostid)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [
             'test_info',
             #'test_start',
             #'test_stop',
             #'test_migrate',
            ]
    return unittest.TestSuite(map(VirtualMachineTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbon_utility.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)