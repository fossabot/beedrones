'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import time
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Domain, Orchestrator, Iso
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class IsoTestCase(CloudTestCase):
    """Template api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object. [optional]
    :type data: dict or None
    :param oid: set oid for current object. [optional]
    :type data: str or None    
    """      
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # <iso id=101cc810-6b68-4927-8337-91e45fa48b7e, name=xs-tools.iso>, 
        # <iso id=db27b211-04e5-408f-bfa0-3107888b5054, name=rhel-server-7.0-x86_64>, 
        # <iso id=ca93b969-d4d1-425b-b94e-0521fd37c8fc, name=CentOS-6.5-x86_64-minimal>, 
        # <iso id=d6da001b-d2ed-4c22-b523-bb591f79f282, name=vmware-tools.iso>, 
        # <iso id=c39f6837-8324-481e-9a2c-3ab14fdc9e41, name=virtio-win-0_1-74>
        isoid = 'ca93b969-d4d1-425b-b94e-0521fd37c8fc'
        self.iso = Iso(self.api_client, oid=isoid)
        self.iso.extend(self.db_session, self.hypervisors)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        res = self.iso.info()

    @watch_test
    def test_is_ready(self):
        res = self.iso.is_ready()
        self.logger.debug(res)

    @watch_test
    def test_get_status(self):
        res = self.iso.get_status()
        self.logger.debug(res)

    @watch_test
    def test_get_os_type(self):
        res = self.iso.get_os_type()
        self.logger.debug(res)

    @watch_test
    def test_delete(self):
        name = 'iso-%s' % random.randint(0, 10000)
        displaytext = name
        hypervisor = 'KVM'
        ostypeid = 'ae6678fe-d518-11e3-8225-0050560203f1'
        url = 'http://10.102.47.205/storage/iso/virtio-win-0.1-74.iso'
        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        domainid = 'b07b93ba-e402-42bf-8a5c-d9542f41be2a'
        account = 'OASIS'
        # register
        iso = self.system.register_iso(name, displaytext, 
                                       hypervisor, ostypeid, url, 
                                       zoneid, bits='64')
        # delete
        while not iso.is_ready():
            time.sleep(1)
            iso.info()
        clsk_job_id = iso.delete()
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_extract(self):
        clsk_job_id = self.iso.extract()
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_update(self):
        res = self.iso.update(name='prova')
        self.logger.debug(res)   

def test_suite():
    tests = [
             'test_info',
             'test_is_ready',
             'test_get_status',
             'test_get_os_type',
             'test_delete',
             #'test_extract',
             'test_update',
            ]
    return unittest.TestSuite(map(IsoTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])