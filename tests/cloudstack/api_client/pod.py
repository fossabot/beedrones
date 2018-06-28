'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Pod, Orchestrator
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class RegionTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        regionid = '1'
        self.pod = Pod(self.api_client, oid=regionid)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)        
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_info(self):
        res = self.pod.info()

    def test_update(self):
        allocationstate = None
        name = None
        startip = None
        endip = None
        gateway = None
        netmask = None
        res = self.pod.update(allocationstate, name, startip, endip, gateway, 
                              netmask)

    def test_delete(self):
        res = self.pod.delete()

    def test_tree(self):
        res = self.pod.tree()
        
    def test_list_clusters(self):
        res = self.pod.list_clusters()

    def test_add_clusters(self):
        hypervisor = 'KVM'
        url = 'hostname'
        username = 'root'
        password = 'mypass'
        res = self.pod.add_cluster(hypervisor, url, username, password)

def test_suite():
    tests = [
             'test_info',
             ##'test_update',
             ##'test_delete',
             'test_tree',
             'test_list_clusters',
             ##'test_add_clusters',
            ]
    return unittest.TestSuite(map(RegionTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])