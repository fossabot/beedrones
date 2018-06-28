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
from gibboncloud.cloudstack.api_client import Domain, Orchestrator, Zone
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class ZoneTestCase(CloudTestCase):
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

        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        self.zone = Zone(self.api_client, oid=zoneid)
        self.zone.extend(self.db_session, self.hypervisors)
        
        #self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        #self.system.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_info(self):
        res = self.zone.info()

    def test_update(self):
        name = None 
        details = None
        res = self.zone.update(name, details)

    def test_delete(self):
        res = self.zone.delete()
        
    def test_tree(self):
        res = self.zone.tree()
        self.logger.debug(res)

    def test_list_pods(self):
        res = self.zone.list_pods()

    def test_list_clusters(self):
        res = self.zone.list_clusters()

    def test_list_hosts(self):
        iso = self.zone.list_hosts()

    def test_list_hypervisors(self):
        clsk_job_id = self.zone.list_hypervisors()

    def test_list_hypervisor_capabilities(self):
        clsk_job_id = self.zone.list_hypervisor_capabilities()

    def test_list_configurations(self):
        clsk_job_id = self.zone.list_configurations()

    def test_update_configuration(self):
        clsk_job_id = self.zone.update_configuration('name', 'value')
        
    def test_list_vmware_dcs(self):
        clsk_job_id = self.zone.list_vmware_dcs()
        
    def test_add_vmware_dc(self):
        name = ''
        vcenter = ''
        username = ''
        password = ''
        clsk_job_id = self.zone.add_vmware_dc(name, vcenter, username, password)
        
    def test_remove_vmware_dc(self):
        clsk_job_id = self.zone.remove_vmware_dc()
        

def test_suite():
    tests = [
             'test_info',
             ##'test_update',
             ##'test_delete',
             'test_tree',
             'test_list_pods',
             'test_list_clusters',
             'test_list_hosts',
             'test_list_hypervisors',
             'test_list_hypervisor_capabilities',
             'test_list_configurations',
             ##'test_update_configuration',
             'test_list_vmware_dcs',
             ##'test_add_vmware_dc',
             ##'test_remove_vmware_dc',
            ]
    return unittest.TestSuite(map(ZoneTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])