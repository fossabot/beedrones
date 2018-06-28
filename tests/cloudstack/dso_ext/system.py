'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.dso_ext import MysqlConnectionManager
from gibboncloud.cloudstack.dso_ext import QemuConnectionManager
from gibboncloud.cloudstack.dso_ext import ClskConnectionManager
from gibboncloud.cloudstack.dso_ext import ApiManager, ApiManagerError
from gibboncloud.cloudstack.dso_ext import SystemExt
from gibboncloud.cloudstack.dso import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class SystemExtTestCase(CloudTestCase):
    def setUp(self):
        base_url = "http://10.102.90.207:8080/client/api"
        #base_url = "http://158.102.160.234:5000/api/clsk/clsk42_01"
        #base_url = "http://172.16.0.19:8081/client/api"
        api_params = {'uri':base_url,
                      'api_key':"oo25khLLZCJTWYBbpt8PthN4hSoeP93-pXJeZFvkYncgK1w1jzYpT-UX-ucH1SsStzNZpgWjlzPLHxHZQqmzcg",
                      'sec_key':"d85PXqWsMy0sHV7Kjip_tH8Ejr93wlHokc7E4_dtSXrPAoAzQ4PVzoDoAQ18gReubkipJqLvQJWNFGcfVBTcOQ"}

        mid = 'clsk42_db'
        host = '172.16.0.19'
        #host = '10.102.90.203'
        port = '3306'
        name = 'cloud'
        user = 'cloud'
        pwd = 'testlab'
        db_manager = MysqlConnectionManager(mid, host, port, name, user, pwd)
        
        name = 'clsk42'
        id = name
        clsk_manager = ClskConnectionManager(name, id, api_params, db_manager)
        
        hid = 'kvm-7-11.clskdom.lab'
        host = '172.16.0.19'
        #host = '10.102.90.3'
        #port = '16509'
        port = '16508'    
        qemu_manager = QemuConnectionManager(hid, host, port)
        clsk_manager.add_hypervisor('qemu', qemu_manager)

        hid = 'kvm-7-12.clskdom.lab'
        host = '172.16.0.19'
        #host = '10.102.90.4'
        #port = '16510'
        port = '16509'
        qemu_manager = QemuConnectionManager(hid, host, port)
        clsk_manager.add_hypervisor('qemu', qemu_manager)
        self.system = SystemExt(clsk_manager, name)
        
        domain_id = '1239b151-d6be-4f2f-88e4-66507cd0fdaa'
        account_id = '47f09d80-ec8c-46d9-a450-cfb0e372f2a9'
        self.zoneid = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
        self.hypervisor = 'KVM'   
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_list_hosts(self):
        # kvm-7-11.clskdom.lab e302ecac-5785-4194-8c44-9b8fa06f5d5f
        # kvm-7-12.clskdom.lab bbb22094-e3d4-451b-9ad8-d60e093a6c7e
        # cluster_kvm_01 fa7c3775-863c-4c06-97b9-4f2da013634f
        # zona_kvm_01 2af97976-9679-427b-8dbd-6b11f9dfa169
        # pod_kvm_01 b74681af-7405-4ec8-a6c1-a4308fbae326
        res = self.system.list_hosts(oid='e302ecac-5785-4194-8c44-9b8fa06f5d5f')
        fres = self.pp.pformat(res)
        self.logger.debug(res[0].info())

    @watch_test
    def test_list_virtual_machines(self):
        #res = self.system.list_virtual_machines(domain='ROOT/CSI', account='test1', vm_id=None)
        res = self.system.list_virtual_machines()
        fres = self.pp.pformat(res)
        self.logger.debug(res)          

    @watch_test
    def test_list_networks(self):
        #domain = 'ROOT/CSI'
        #account = 'sergio'
        domain = None
        account = None
        net_id = '84564ac7-923c-41f8-b777-e26167594413'
        res = self.system.list_networks(zone_id=None, domain=domain, 
                                        account=account, net_id=net_id)
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_list_physical_networks(self):
        res = self.system.list_physical_networks()
        fres = self.pp.pformat(res)
        self.logger.debug(res)      

    @watch_test
    def test_list_remote_access_vpns(self):
        res = self.system.list_remote_access_vpns()
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_list_public_ip_addresses(self):
        res = self.system.list_public_ip_addresses()
        fres = self.pp.pformat(res)
        self.logger.debug(res)
            
    @watch_test
    def test_list_volumes(self):
        #domain = 'ROOT/CSI'
        #account = 'sergio'
        domain = None
        account = None
        net_id = '84564ac7-923c-41f8-b777-e26167594413'
        res = self.system.list_volumes()
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_list_tenants(self):
        res = self.system.list_tenants()
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_list_storagepools(self):
        res = self.system.list_storagepools(name='primarykvm')
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_list_templates(self):
        res = self.system.list_templates(self.zoneid, self.hypervisor)
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_list_isos(self):
        res = self.system.list_isos(self.zoneid)
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_create_vm(self):
        oid = str(random.randint(0, 10000))
        job_id = oid
        name = 'vm-iso-%s' % oid
        displayname = name
        serviceofferingid = '6d01dd0f-ddfc-443b-a266-7d1a643526cc'
        templateid = '0873d544-b5c6-4924-967b-20c099daac44'
        isoid = 'b3e2c2b6-573a-45b8-881e-66f02a0886ea'
        zoneid = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
        domain = 'ROOT'
        account = 'admin'
        hypervisor = 'KVM'
        networkids = '262a5232-2601-48d1-ac75-d0c8e4229167'
        diskoffering = '66cb24c5-7f77-4381-9047-be44b8a8f8a1'
        devices = {'video_qxl': '',
                   'usb_redirect': '', 
                   'spice_graphics': '',
                   'sound_card_ich6': ''}
        
        res = self.system.create_vm(job_id, name, displayname, 
                                    serviceofferingid, isoid, 
                                    zoneid, domain, account, 
                                    hypervisor, networkids, devices=devices, 
                                    diskofferingid=diskoffering, size=10)
        fres = self.pp.pformat(res)
        self.logger.debug(res)

    @watch_test
    def test_create_private_network(self):
        name = 'net-%s' % random.randint(0, 10000)
        displaytext = name
        networkoffering_id = '6d72113c-dd42-4558-bde1-ad81a7a0c81f'
        zoneid = 'a6ff29f2-fd3c-4a42-b6f9-0fceac126510'
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
            
    @watch_test
    def test_create_hybrid_network(self):
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

def test_suite():
    tests = [
             #'test_list_hosts',
             #'test_create_vm',
             #'test_list_virtual_machines',
             #'test_list_networks',
             'test_list_physical_networks',
             'test_list_remote_access_vpns',
             'test_list_public_ip_addresses',
             #'test_list_storagepools',
             #'test_list_volumes',
             #'test_list_tenants',
             #'test_list_templates',
             #'test_list_isos',
             #'test_create_private_network',
             #'test_create_hybrid_network',
            ]
    return unittest.TestSuite(map(SystemExtTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])