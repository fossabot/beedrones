'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import Domain, Orchestrator, Account, Volume
from gibboncloud.cloudstack.api_client import ApiClient
from gibboncloud.cloudstack.api_client import ClskObjectError
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class AccountTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # <account id=44e7d4da-d519-11e3-8225-0050560203f1, name=admin>
        # <account id=9481c07c-d1b9-4673-b514-4c33138116ee, name=OASIS>
        # <domain id=ae3fad3c-d518-11e3-8225-0050560203f1, name=ROOT>
        # <domain id=4217b591-ae1e-4c83-8666-178966c6603a, name=domain-4909>
        # <domain id=3ee46212-cd07-4430-8c6f-51bc67cc7faf, name=CSI>
        # <domain id=b07b93ba-e402-42bf-8a5c-d9542f41be2a, name=PRG-EUROPEI>        
        #accountid = '44e7d4da-d519-11e3-8225-0050560203f1'
        #domainid = 'ae3fad3c-d518-11e3-8225-0050560203f1'
        accountid = '9481c07c-d1b9-4673-b514-4c33138116ee'
        domainid = 'b07b93ba-e402-42bf-8a5c-d9542f41be2a'
        self.zone_id = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        self.hypervisor = 'KVM'
        self.account = Account(self.api_client, oid=accountid,
                               domain_id=domainid)
  
        self.domain = Domain(self.api_client, oid=domainid)
        
        self.system = Orchestrator(self.api_client, name='clsk42', oid='clsk42')
        self.system.extend(self.db_session, self.hypervisors)  
        
    def tearDown(self):
        CloudTestCase.tearDown(self)


    def test_tree(self):
        res = self.account.tree()


    def test_info(self):
        res = self.account.info()


    def test_delete(self):
        job_id = 1
        res = self.account.delete(job_id)
        fres = self.pp.pformat(res)
        self.logger.debug(res)


    def test_get_resource_limit(self):
        res = self.account.get_resource_limit()


    def test_update_resource_limit(self):
        type = 0
        max = 2
        res = self.account.update_resource_limit(type, max)


    def test_list_all_virtual_machines(self):
        res = self.account.list_all_virtual_machines()


    def test_list_templates(self):
        res = self.account.list_templates(self.zone_id, self.hypervisor)


    def test_list_isos(self):
        res = self.account.list_isos(self.zone_id, self.hypervisor)


    def test_list_sdns(self):
        res = self.account.list_sdns(self.zone_id)


    def test_list_volumes(self):
        res = self.account.list_volumes(self.zone_id)


    def test_create_isolated_sdn(self):
        name = 'net-%s' % random.randint(0, 10000)
        displaytext = name
        # DefaultIsolatedNetworkOfferingWithSourceNatService
        networkoffering_id = '959bcacd-17c8-4ece-b4f3-510bb4daaf5a'
        zoneid = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
        networkdomain = 'acs1.local.it'
        res = self.account.create_isolated_sdn(name, displaytext, 
                                               networkoffering_id, 
                                               self.zone_id, 
                                               networkdomain=networkdomain)
            

    def test_create_guest_sdn(self):
        name = 'net-%s' % random.randint(0, 10000)
        displaytext = name
        # QuickCloudNoServices
        networkoffering_id = '3a470bcc-8889-4da7-8b90-968360c69431'
        networkdomain = 'acs1.local.it'
        gateway = '44.44.44.1'
        netmask = '255.255.255.0'
        startip = '44.44.44.3'
        endip = '44.44.44.254'
        vlan = 3001
        res = self.account.create_guest_sdn(name, displaytext, 
                                            networkoffering_id, 
                                            self.zone_id, 
                                            gateway, netmask, 
                                            startip, endip, vlan, 
                                            networkdomain=networkdomain)


    def test_create_vm(self):
        name = 'vm-%s' % random.randint(0, 10000)
        displayname = name
        serviceofferingid = 'ec3cce76-2330-444c-89fc-4fda2b37fbaf'
        templateid = '67f80880-22aa-4f85-ae8c-ca34b43394ea'
        hypervisor = 'KVM'
        networkids = 'd60e380e-831e-497d-aa4f-5bdf789f1a10'
        #networkids = 'c3846198-4084-453f-962e-326be6d28a26'
        hostid = 'e302ecac-5785-4194-8c44-9b8fa06f5d5f'
        
        clsk_job_id = self.account.create_vm(name, displayname, 
                                             serviceofferingid, 
                                             templateid, self.zone_id,
                                             hypervisor, networkids)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)


    def test_create_delete_data_volume(self):
        name = 'datavol-%s' % random.randint(0, 10000)
        diskofferingid = '16e10ca9-2c04-401f-a12d-6009693698bc'
        size = 10
        # create
        clsk_job_id = self.account.create_data_volume(
                                 name, self.zone_id,
                                 diskofferingid=diskofferingid,
                                 size=size)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # delete
        vol_id = jobres['jobresult']['volume']['id']
        volume = Volume(self.api_client, oid=vol_id)
        volume.delete()


    def test_upload_data_volume(self):
        name = 'datavol-%s' % random.randint(0, 10000)
        format = 'QCOW2'
        url = 'http://10.102.47.205/storage/template/vm-osgis2-disk2.qcow2.gz'
        clsk_job_id = self.account.upload_data_volume(name, self.zone_id, 
                                                      format, url,
                                                      checksum=None, 
                                                      imagestoreuuid=None)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)


    def test_list_configurations(self):
        clsk_job_id = self.account.list_configurations()


    def test_update_configuration(self):
        clsk_job_id = self.account.update_configuration('name', 'value')

def test_suite():
    tests = [
             #'test_tree',
             #'test_info',
             #'test_delete',
             #'test_get_resource_limit',
             #'test_update_resource_limit',
             #'test_list_all_virtual_machines',
             #'test_list_templates',
             #'test_list_isos',
             #'test_list_sdns',
             #'test_list_volumes',
             
             #'test_create_isolated_sdn',
             #'test_create_guest_sdn',
             #'test_create_vm',
             #'test_create_delete_data_volume',
             #'test_upload_data_volume',
             
             'test_list_configurations',
             ##'test_update_configuration',             
            ]
    return unittest.TestSuite(map(AccountTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])