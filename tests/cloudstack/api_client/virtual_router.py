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
from gibboncloud.cloudstack.api_client import ApiClient, VirtualRouter
from gibboncloud.virt import VirtManager

class VirtualRouterTestCase(CloudTestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # r-10-VM 0d88519c-728b-40d7-b19d-10464aa9638c
        self.virtual_router = VirtualRouter(self.api_client, oid='0d88519c-728b-40d7-b19d-10464aa9638c')
        self.virtual_router.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    @watch_test
    def test_get_state(self):
        res = self.virtual_router.get_state()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_info(self):
        res = self.virtual_router.info()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_list_nics(self):
        res = self.virtual_router.list_nics()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_start(self):
        res = self.virtual_router.start(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_stop(self):
        res = self.virtual_router.stop(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_destroy(self):
        res = self.virtual_router.destroy(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_migrate(self):
        clsk_job_id = self.virtual_router.migrate(1, hostid=self.cid1)
        self.logger.debug(clsk_job_id)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_change_service_offering(self):
        res = self.virtual_router.change_service_offering()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

def test_suite():
    tests = [
             'test_get_state',
             'test_info',
             'test_list_nics',
             #'test_start',
             #'test_stop',
             #'test_destroy',
             'test_migrate',
             #'test_change_service_offering',
            ]
    return unittest.TestSuite(map(VirtualRouterTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])