'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Host, Orchestrator
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class HostTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        hostid = 'e302ecac-5785-4194-8c44-9b8fa06f5d5f'
        self.host = Host(self.api_client, oid=hostid)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)        
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_info(self):
        res = self.host.info()
        
    def test_update(self):
        allocationstate = None
        hosttags = None
        oscategoryid = None
        res = self.host.update(allocationstate, hosttags, oscategoryid)       

    def test_delete(self):
        res = self.host.delete()

    def test_update_password(self):
        username = 'root'
        password = 'mypass'
        res = self.host.update_password(username, password)

    def test_tree(self):
        res = self.host.tree()

    def test_list_system_vms(self):
        res = self.host.list_system_vms()
        
    def test_list_routers(self):
        clsk_job_id = self.host.list_routers()

    def test_list_virtual_machines(self):
        clsk_job_id = self.host.list_virtual_machines()  

    def test_maintenance(self):
        clsk_job_id = self.host.maintenance()
        
    def test_cancel_maintenance(self):
        clsk_job_id = self.host.cancel_maintenance()
        
    def test_reconnect(self):
        clsk_job_id = self.host.reconnect()
        

def test_suite():
    tests = [
             'test_info',
             ##'test_update',
             ##'test_delete',
             ##'test_update_password',
             'test_tree',
             'test_list_system_vms',
             'test_list_routers',
             'test_list_virtual_machines',
             ##'test_maintenance',
             ##'test_cancel_maintenance',
             ##'test_reconnect',
            ]
    return unittest.TestSuite(map(HostTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])