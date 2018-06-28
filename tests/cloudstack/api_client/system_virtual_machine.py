'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
import time
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from gibboncloud.cloudstack.api_client import ApiClient, SystemVirtualMachine
from gibboncloud.virt import VirtManager

class SystemVirtualMachineTestCase(CloudTestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # s-67-vm 7779d5f5-efd4-4b7c-a0cc-e7397c76bca0
        self.system_vm = SystemVirtualMachine(self.api_client, oid='7779d5f5-efd4-4b7c-a0cc-e7397c76bca0')
        self.system_vm.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    @watch_test
    def test_get_state(self):
        res = self.system_vm.get_state()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_info(self):
        res = self.system_vm.info()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_start(self):
        res = self.system_vm.start(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_stop(self):
        res = self.system_vm.stop(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_destroy(self):
        res = self.system_vm.destroy(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_migrate(self):
        clsk_job_id = self.system_vm.migrate(1, hostid=self.cid1)
        self.logger.debug(clsk_job_id)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_change_service_offering(self):
        res = self.system_vm.change_service_offering()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_create_vv_file(self):
        res = self.system_vm.create_vv_file()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

def test_suite():
    tests = [
             'test_get_state',
             'test_info',
             #'test_start',
             #'test_stop',
             #'test_destroy',
             #'test_migrate',
             #'test_change_service_offering',
             #'test_create_vv_file',
            ]
    return unittest.TestSuite(map(SystemVirtualMachineTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])