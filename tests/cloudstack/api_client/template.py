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
from gibboncloud.cloudstack.api_client.template import Template
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class TemplateTestCase(CloudTestCase):
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
        
        # <domain id=ae3fad3c-d518-11e3-8225-0050560203f1, name=ROOT>
        # <domain id=4217b591-ae1e-4c83-8666-178966c6603a, name=domain-4909>
        # <domain id=3ee46212-cd07-4430-8c6f-51bc67cc7faf, name=CSI>
        # <domain id=b07b93ba-e402-42bf-8a5c-d9542f41be2a, name=PRG-EUROPEI>
        templateid = 'b15c261d-f846-45b0-b9cf-04dff37bab5f'
        self.template = Template(self.api_client, oid=templateid)
        self.template.extend(self.db_session, self.hypervisors)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        res = self.template.info()

    @watch_test
    def test_is_ready(self):
        res = self.template.is_ready()
        self.logger.debug(res)
        
    @watch_test
    def test_deep_info(self):
        res = self.template.deep_info()
        self.logger.debug(res)

    @watch_test
    def test_get_os_type(self):
        res = self.template.get_os_type()
        self.logger.debug(res)

    @watch_test
    def test_delete(self):
        name = 'tmpl-%s' % random.randint(0, 10000)
        displaytext = name
        format = 'QCOW2'
        hypervisor = 'KVM'
        ostypeid = 'ae6678fe-d518-11e3-8225-0050560203f1'
        url = 'http://10.102.47.205/storage/template/CentOS-6.5-minimal.qcow2.gz'
        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        domainid = 'b07b93ba-e402-42bf-8a5c-d9542f41be2a'
        account = 'OASIS'
        # register
        tmpl = self.system.register_template(name, displaytext, format, 
                                            hypervisor, ostypeid, url, 
                                            zoneid, domainid=domainid, 
                                            account=account, bits='64')
        # delete
        while not tmpl.is_ready():
            time.sleep(2)
            tmpl.info()
        clsk_job_id = tmpl.delete()
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_extract(self):
        clsk_job_id = self.template.extract()
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_update(self):
        res = self.template.update(name='prova')
        self.logger.debug(res)
        
    @watch_test
    def test_load_in_primary_storage(self):
        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        res = self.template.load_in_primary_storage(zoneid)
        self.logger.debug(res)        

def test_suite():
    tests = [
             'test_info',
             'test_deep_info',
             'test_is_ready',
             'test_get_os_type',
             'test_delete',
             #'test_extract',
             #'test_update',
             #'test_load_in_primary_storage',
            ]
    return unittest.TestSuite(map(TemplateTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])