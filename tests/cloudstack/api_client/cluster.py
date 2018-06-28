'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Cluster, Orchestrator
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class DomainTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        clusterid = 'fa7c3775-863c-4c06-97b9-4f2da013634f'
        self.cluster = Cluster(self.api_client, oid=clusterid)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)        
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_info(self):
        res = self.cluster.info()

    def test_update(self):
        allocationstate = None
        clustername = None
        clustertype = None
        hypervisor = None
        managedstate = None
        res = self.cluster.update(allocationstate, clustername, clustertype, 
                                  hypervisor, managedstate)

    def test_delete(self):
        res = self.cluster.delete()

    def test_tree(self):
        res = self.cluster.tree()

    def test_list_hosts(self):
        res = self.cluster.list_hosts()
        
    def test_add_host(self):
        hypervisor = 'KVM'
        url = 'hostname'
        username = 'root'
        password = 'mypass'
        res = self.cluster.add_host(hypervisor, url, username, password)
        
    def test_list_configurations(self):
        clsk_job_id = self.cluster.list_configurations()

    def test_update_configuration(self):
        clsk_job_id = self.cluster.update_configuration('name', 'value')  

def test_suite():
    tests = [
             'test_info',
             ##'test_update',
             ##'test_delete',
             'test_tree',
             'test_list_hosts',
             ##'test_add_host',
             #'test_list_configurations',
             ##'test_update_configuration',
            ]
    return unittest.TestSuite(map(DomainTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])