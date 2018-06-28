'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import os
import pprint
from gibboncloud.virt.manager import VirtManager, VirtManagerError

class VirtManagerTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))        
        
        id = 'kvm1'
        host = '10.102.47.205:16509'
        #host = '10.102.47.205:16510'
        
        self.server = VirtManager(id, "qemu+tcp://%s/system" % host)
        self.server.connect()
        #self.logger.debug('Connect to server %s' % self.server)
        
        self.node_id = 'kvm1'
        self.ds_id = '6fc7f3f4-7f76-3660-afd9-0baf1eed5fbd'
        self.vm_name='v-105-VM'
        
        self.pp = pprint.PrettyPrinter()
        
    def tearDown(self):
        self.server.disconnect()
        #self.logger.debug('Disconnect from server %s' % self.server)

    # hypervisor
    
    def test_is_alive(self):
        try:     
            res = self.server.is_alive()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except VirtManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)            

    
    def test_ping(self):
        try:     
            res = self.server.ping()
            self.logger.debug(res)
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
    
    
    def test_info(self):
        try:     
            res = self.server.info()
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
    
    
    def test_tree(self):
        try:     
            res = self.server.tree()
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
        
    
    def test_stats(self):
        try:     
            res = self.server.stats()
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())

    
    def test_nw_filters_list(self):
        try:     
            res = self.server.nw_filters_list()
            #self.logger.debug(self.pp.pformat(res))
            self.logger.debug(res)
        except VirtManagerError:
            self.logger.error(traceback.format_exc())

    # node
    
    def test_nodes_list(self):
        try:     
            res = self.server.nodes_list()
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())    
    
    
    def test_node_info(self):
        try:
            res = self.server.node_info(self.node_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())

    
    def test_node_network_list(self):
        try:
            res = self.server.node_network_list(self.node_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 

    
    def test_node_network_conf(self):
        try:
            res = self.server.node_network_conf(self.node_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 

    
    def test_node_datastore_list(self):
        try:
            res = self.server.node_datastore_list(self.node_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 

    
    def test_node_vm_list(self):
        try:
            res = self.server.node_vm_list(self.node_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 

    
    def test_node_device_list(self):
        try:
            res = self.server.node_device_list(self.node_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 

    # datastore
    
    def test_datastores_list(self):
        try:
            res = self.server.datastores_list()
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
    
    
    def test_datastore_info(self):
        try:
            res = self.server.datastore_info(self.ds_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
            
    
    def test_datastore_tree(self):
        try:
            res = self.server.datastore_tree(id=self.ds_id)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())            
    
    
    def test_datastore_volumes_list(self):
        try:
            vm_status = 16
            res = self.server.datastore_volumes_list(vm_status)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())

    # network
    
    def test_networks_list(self):
        try:
            res = self.server.networks_list()
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
    
    # virtual machine
    
    def test_vms_list(self):
        try:
            status = 16
            res = self.server.vms_list(host=self.node_id, status=status)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
        
    
    def test_vm_info(self):
        try:
            status = 16
            res = self.server.vm_info(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
    
    
    def test_vm_storage(self):
        try:
            status = 16
            res = self.server.vm_storage(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
    
    
    def test_vm_files(self):
        try:
            status = 16
            res = self.server.vm_files(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 
    
    
    def test_vm_network(self):
        try:
            status = 16
            res = self.server.vm_network(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc()) 
 
    
    def test_vm_device(self):
        try:
            status = 16
            res = self.server.vm_device(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
            
    
    def test_vm_stats(self):
        try:
            status = 16
            res = self.server.vm_stats(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())

    
    def test_vm_snapshots(self):
        try:
            status = 16
            res = self.server.vm_snapshots(name=self.vm_name)
            self.logger.debug(self.pp.pformat(res))
        except VirtManagerError:
            self.logger.error(traceback.format_exc())
            
def test_suite():
    tests = ['test_is_alive',
             'test_ping',
             'test_info',
             'test_tree',
             'test_stats',
             'test_nw_filters_list',
             
             'test_nodes_list', 
             'test_node_info',
             'test_node_network_list', 
             'test_node_network_conf', 
             'test_node_datastore_list', 
             'test_node_vm_list', 
             'test_node_device_list',
             
             'test_datastores_list', 
             'test_datastore_info', 
             'test_datastore_tree', 
             'test_datastore_volumes_list',
             
             'test_networks_list',
             
             'test_vms_list', 
             'test_vm_info', 
             'test_vm_storage',
             'test_vm_files',
             'test_vm_network', 
             'test_vm_device', 
             'test_vm_stats', 
             'test_vm_snapshots'
            ]
    tests = ['test_tree', ]
    return unittest.TestSuite(map(VirtManagerTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbon_utility.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)              