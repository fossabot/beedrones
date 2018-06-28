'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.dso import System
from gibboncloud.cloudstack.dso import ApiClient
from gibboncloud.cloudstack.dso import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class SystemTestCase(CloudTestCase):
    """To execute this test you need a cloudstack instance.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        base_url = "http://10.102.90.209:8080/client/api"
        base_url = "http://158.102.160.234:5000/api/clsk/clsk42_01"
        api_key = "wWYlBdZ9S6HW5oFLO6xLS15rlTWDDxP4KnZSQ6__MoKNGgMhnpEFTyqvolc1teSMRAShjzQKH33fO9v97xuy4Q"
        sec_key = "u2yxAUEujncW4b2OuWg9vWA2vZ8hDLn-pCY3HLI0vo21sPaGTWtRdPoqe2T4CUQAOiAwfJVlYwhWBDfQWaH5Lg"
        
        api_client = ApiClient(base_url, api_key, sec_key)
        self.system = System(api_client, name='clsk42', oid='clsk42')
        self.userid = '56c82fb4-3281-11e3-830f-005056020061'
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    @watch_test
    def test_get_cloud_identifier(self):
        try:
            res = self.system.get_cloud_identifier(self.userid)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_apis(self):
        try:
            res = self.system.list_apis()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_regions(self):
        try:
            res = self.system.list_regions()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_zones(self):
        try:
            res = self.system.list_zones()
            for item in res:
                fres = self.pp.pformat(item.info())
                self.logger.debug(fres)
            #self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_pods(self):
        try:
            res = self.system.list_pods()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_clusters(self):
        try:
            res = self.system.list_clusters()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)    

    @watch_test
    def test_list_hosts(self):
        try:
            res = self.system.list_hosts()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)    
    
    @watch_test
    def test_list_storagepools(self):
        try:
            res = self.system.list_storagepools()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_imagestores(self):
        try:
            res = self.system.list_imagestores()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex) 
    
    @watch_test
    def test_list_system_vms(self):
        try:
            res = self.system.list_system_vms()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_routers(self):
        try:
            res = self.system.list_routers()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_virtual_machines(self):
        try:
            res = self.system.list_virtual_machines()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_volumes(self):
        try:
            res = self.system.list_volumes()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_networks(self):
        try:
            #domain = 'ROOT/CSI'
            #account = 'sergio'
            domain = None
            account = None
            net_id = '84564ac7-923c-41f8-b777-e26167594413'
            res = self.system.list_networks(zone_id=None, domain=domain, 
                                            account=account, net_id=net_id)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_list_templates(self):
        try:
            res = self.system.list_templates()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    
    @watch_test
    def test_list_domains(self):
        try:
            res = self.system.list_domains()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_accounts(self):
        try:
            #res = self.system.list_accounts(domain='ROOT/CSI', account='sergio')
            res = self.system.list_accounts()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_service_offerings(self):
        try:
            res = self.system.list_service_offerings()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_network_offerings(self):
        try:
            res = self.system.list_network_offerings()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_list_disk_offerings(self):
        try:
            res = self.system.list_disk_offerings()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    @watch_test
    def test_get_domain_id(self):
        try:
            res = self.system.get_domain_id('ROOT/comto/Formazione')
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    # tree
    @watch_test
    def test_physical_tree(self):
        try:
            res = self.system.physical_tree()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)    

    @watch_test
    def test_logical_tree(self):
        try:
            res = self.system.logical_tree()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)  

    @watch_test
    def test_network_tree(self):
        try:
            res = self.system.network_tree()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex) 

    # create
    @watch_test
    def test_create_domain(self):
        try:
            name = 'domain-%s' % random.randint(0, 10000)
            res = self.system.create_domain(name)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_create_vm(self):
        try:
            name = 'vm-%s' % random.randint(0, 10000)
            displayname = name
            serviceofferingid = '23db0535-23a2-42ca-b936-8317e1e54410'
            templateid = 'd740695b-f1ca-48ab-9100-4b376c46f022'
            zoneid = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
            domainid = '1239b151-d6be-4f2f-88e4-66507cd0fdaa'
            account = 'account-434'
            hypervisor = 'KVM'
            networkids = '84564ac7-923c-41f8-b777-e26167594413'
            
            res = self.system.create_vm(name, displayname, serviceofferingid, 
                                        templateid, zoneid, domainid, account, 
                                        hypervisor, networkids)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_create_private_network(self):
        try:
            name = 'net-%s' % random.randint(0, 10000)
            displaytext = name
            networkoffering_id = '6d72113c-dd42-4558-bde1-ad81a7a0c81f'
            zoneid = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
            domain = 'ROOT/CSI'
            account = 'sergio'
            networkdomain = 'acs1.local.it'
            res = self.system.create_private_network(name, displaytext, 
                                                     networkoffering_id, 
                                                     zoneid, domain=domain, 
                                                     account=account, 
                                                     networkdomain=networkdomain)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_create_hybrid_network(self):
        try:
            name = 'net-%s' % random.randint(0, 10000)
            displaytext = name
            networkoffering_id = '00616132-a25a-4c03-a92e-dd5185fb0c29'
            zoneid = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
            domain = 'ROOT/CSI'
            account = 'sergio'
            networkdomain = 'acs1.local.it'
            gateway = '44.44.44.1'
            netmask = '255.255.255.0'
            startip = '44.44.44.3'
            endip = '44.44.44.254'
            vlan = 3001
            res = self.system.create_hybrid_network(name, displaytext, 
                                                     networkoffering_id, 
                                                     zoneid, 
                                                     gateway, netmask, startip, endip, vlan,
                                                     domain=domain, account=account,
                                                     shared=True,
                                                     networkdomain=networkdomain)
            
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)            


def test_suite():
    tests = [
             'test_get_cloud_identifier',
             #'test_list_apis',
             #'test_list_regions',
             #'test_list_zones',
             #'test_list_pods',
             #'test_list_clusters',
             #'test_list_hosts',
             #'test_list_storagepools',
             #'test_list_imagestores',
             #'test_list_system_vms',
             #'test_list_routers',
             #'test_list_virtual_machines',
             #'test_list_volumes',
             #'test_list_networks',
             #'test_list_templates',
             #'test_list_domains',
             #'test_list_accounts',
             #'test_list_service_offerings',
             #'test_list_network_offerings',
             #'test_list_disk_offerings',
             #'test_get_domain_id',
             #'test_physical_tree',
             #'test_logical_tree',
             #'test_network_tree',
             #'test_create_domain',
             #'test_create_vm',
             #'test_create_private_network',
             #'test_create_hybrid_network',
            ]
    return unittest.TestSuite(map(SystemTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])