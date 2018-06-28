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
from gibboncloud.cloudstack.api_client import ApiClient, Volume
from gibboncloud.virt import VirtManager

class VolumeTestCase(CloudTestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # s-67-vm 7779d5f5-efd4-4b7c-a0cc-e7397c76bca0
        self.volumeid = 'ce42f419-b33d-4d88-b882-013b55840e2e'
        self.virtualmachineid = '911cc837-591f-4eda-a0a4-bd6562b557f4'
        self.volume = Volume(self.api_client, oid=self.volumeid)
        self.volume.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    @watch_test
    def test_info(self):
        res = self.volume.info()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_attach(self):
        clsk_job_id = self.volume.attach(self.virtualmachineid)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        
    @watch_test
    def test_detach(self):
        clsk_job_id = self.volume.detach(self.virtualmachineid)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
    
    @watch_test
    def test_delete(self):
        res = self.volume.delete()
    
    @watch_test
    def test_extract(self):
        clsk_job_id = self.volume.extract()
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
    
    @watch_test
    def test_migrate(self):
        storageid = ''
        clsk_job_id = self.volume.migrate(storageid)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
    
    @watch_test
    def test_resize(self):
        diskofferingid = ''
        size = 0
        clsk_job_id = self.volume.resize(diskofferingid, size)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

def test_suite():
    tests = [
             'test_info',
             #'test_attach',
             #'test_detach',
             'test_delete',
             #'test_extract',
             #'test_migrate',
             #'test_resize',
            ]
    return unittest.TestSuite(map(VolumeTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])