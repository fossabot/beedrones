'''
Created on Jun 23, 2017

@author: darkbk, igna
'''
from beedrones.tests.test_util import runtest, BeedronesTestCase
import unittest
import ujson as json
import requests
from beedrones.vsphere.client import VsphereManager
from beedrones.graphite.client import GraphiteManager

class GraphiteClientTestCase(BeedronesTestCase):
    """
    """
    def setUp(self):
        BeedronesTestCase.setUp(self)
        
        env = u'test'
        host = self.platform.get(u'graphite').get(env).get(u'host')
        self.graphite_client = GraphiteManager(host, env)
        
        env = u'tstsddc'
        params = self.platform.get(u'vsphere').get(env)
        self.vsphere_client = VsphereManager(params.get(u'vcenter', None), 
                                             params.get(u'nsxmanager', None))
        
        self.vpshere_host_id = u'host_53'
        self.vpshere_vm_id = u'vm_785'
        self.kvm_host_id = u'compute-0'
        self.kvm_vm_id = u'instance-00000009'
        self.minutes = 5
        
    def tearDown(self):
        BeedronesTestCase.tearDown(self)
        
    def test_get_vsphere_vm_metrics(self):
        self.graphite_client.set_search_path(u'test.vmware.tst-open-graphite')
        res = self.graphite_client.get_virtual_node_metrics(
            u'vsphere', self.vpshere_vm_id, self.minutes)
        res = self.graphite_client.format_metrics(self.vpshere_vm_id, res, 
                                                   u'vsphere')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_vsphere_host_metrics(self):
        self.graphite_client.set_search_path(u'test.vmware.tst-open-graphite')
        res = self.graphite_client.get_physical_node_metrics(
            u'vsphere', self.vpshere_host_id, self.minutes)
        res = self.graphite_client.format_metrics(self.vpshere_host_id, res, 
                                                   u'vsphere')
        self.logger.info(self.pp.pformat(res))        
        
    def test_get_kvm_vm_metrics(self):
        self.graphite_client.set_search_path(u'test.kvm')
        res = self.graphite_client.get_virtual_node_metrics(
            u'kvm', self.kvm_vm_id, self.minutes)
        res = self.graphite_client.format_metrics(self.kvm_vm_id, res, u'kvm')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_kvm_host_metrics(self):
        self.graphite_client.set_search_path(u'test.kvm')
        res = self.graphite_client.get_physical_node_metrics(
            u'kvm', self.kvm_host_id, self.minutes)
        res = self.graphite_client.format_metrics(self.kvm_host_id, res, u'kvm')
        self.logger.info(self.pp.pformat(res)) 
        
    def test_get_vsphere_nodes(self):
        self.graphite_client.set_search_path(u'test.vmware.tst-open-graphite')
        res = self.graphite_client.get_nodes(u'vsphere')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_kvm_nodes(self):
        self.graphite_client.set_search_path(u'test.kvm')
        res = self.graphite_client.get_nodes(u'kvm')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_kvm_redhat_nodes(self):
        self.graphite_client.set_search_path(u'test.redhat')
        res = self.graphite_client.get_nodes(u'kvm')
        self.logger.info(self.pp.pformat(res))
        
def test_suite():
    tests = [
        #u'test_get_vsphere_vm_metrics',
        #u'test_get_vsphere_host_metrics',
        #u'test_get_kvm_vm_metrics',
        u'test_get_kvm_host_metrics',
        
        #u'test_get_vsphere_nodes',
        #u'test_get_kvm_nodes',
        #u'test_get_kvm_redhat_nodes',
    ]
    return unittest.TestSuite(map(GraphiteClientTestCase, tests))

if __name__ == u'__main__':
    runtest(test_suite())
            