'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.api_client import ClskOrchestrator
from tests.test_util import run_test, CloudTestCase

class ClskOrchestratorTestCase(CloudTestCase):
    """To execute this test you need a cloudstack instance.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        self.system = ClskOrchestrator(self.api_client, db_manager=self.db_session, 
                                       name='clsk43', oid='clsk43', active=True)
        #self.system.extend(self.db_session, self.hypervisors)
        self.userid = '56c82fb4-3281-11e3-830f-005056020061'
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    def test_ping(self):
        res = self.system.ping()

    def test_info(self):
        res = self.system.info()

    def test_get_hypervisors(self):
        res = self.system.get_hypervisors()
        self.logger.debug(self.pp.pformat(res))

    def test_list_deployment_planners(self):
        res = self.system.list_deployment_planners()
        

    def test_list_configurations(self):
        res = self.system.list_configurations(category='Alert')
        

    def test_list_ldap_configurations(self):
        res = self.system.list_ldap_configurations()


    def test_get_cloud_identifier(self):
        res = self.system.get_cloud_identifier(self.userid)

    def test_login(self):
        username = 'admin'
        password = 'testlab_$01' 
        domainId = None
        res = self.system.login(username, password, domainId=domainId)

    def test_logout(self):
        res = self.system.logout()

    def test_list_regions(self):
        res = self.system.list_regions()
        for item in res:
            self.logger.debug(item.__dict__)        

    def test_list_zones(self):
        res = self.system.list_zones()
        for item in res:
            self.logger.debug(item.__dict__)  

    def test_list_pods(self):
        res = self.system.list_pods()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_clusters(self):
        res = self.system.list_clusters()
        for item in res:
            self.logger.debug(item.__dict__)  

    def test_list_hosts(self):
        res = self.system.list_hosts()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_storagepools(self):
        res = self.system.list_storagepools()
        for item in res:
            self.logger.debug(item.__dict__)  

    def test_list_imagestores(self):
        res = self.system.list_imagestores()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_system_vms(self):
        res = self.system.list_system_vms()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_routers(self):
        res = self.system.list_routers()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_virtual_machines(self):
        res = self.system.list_virtual_machines()
        c = 0
        for i in res:
            #if i.created.find('2015') == 0 or i.created.find('2014') == 0:
            #    print "%10s %20s %20s %12s %10s %s" %  (i.domain, i.account, i.name, i.instancename, i.state, i.created)
            if i.state == 'Running':
                c += 1
        print c

    def test_list_volumes(self):
        res = self.system.list_volumes()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_sdns(self):
        #domain = 'ROOT/CSI'
        #account = 'sergio'
        domain = None
        account = None
        net_id = '84564ac7-923c-41f8-b777-e26167594413'
        #res = self.system.list_networks(zone_id=None, domain=domain, 
        #                                account=account, net_id=net_id)
        res = self.system.list_sdns()
        fres = []
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_physical_networks(self):
        res = self.system.list_physical_networks()

    def test_list_remote_access_vpns(self):
        res = self.system.list_remote_access_vpns()

    def test_list_public_ip_addresses(self):
        res = self.system.list_public_ip_addresses()

    def test_list_os_categories(self):
        res = self.system.list_os_categories()

    def test_list_os_types(self):
        res = self.system.list_os_types(oscategoryid='b0bf0cf8-2f5c-11e4-a368-00505602012d')

    def test_list_templates(self):
        res = self.system.list_templates()

    def test_list_isos(self):
        res = self.system.list_isos()
    
    def test_list_domains(self):
        res = self.system.list_domains()
        for item in res:
            self.logger.debug(item.__dict__)

    def test_list_accounts(self):
        #res = self.system.list_accounts(domain='ROOT/CSI', account='sergio')
        res = self.system.list_accounts()
        for item in res:
            self.logger.debug(item.__dict__)        

    def test_list_service_offerings(self):
        res = self.system.list_service_offerings()

    def test_list_network_offerings(self):
        res = self.system.list_network_offerings()
            
    def test_list_disk_offerings(self):
        res = self.system.list_disk_offerings()

    def test_get_domain_id(self):
        res = self.system.get_domain_id('ROOT')

    def test_get_account_id(self):
        domainid = self.system.get_domain_id('ROOT/CSI')
        res = self.system.get_account_id(domainid, 'sistemisti')

    def test_get_domain_path(self):
        res = self.system.get_domain_path('b492ba80-99a4-4fd9-8814-b543b2670746')

    # tree
    def test_tree_physical(self):
        res = self.system.tree_physical()

    def test_tree_logical(self):
        res = self.system.tree_logical()

    def test_tree_network(self):
        res = self.system.tree_network()

    # create
    def test_create_domain(self):
        name = 'domain-%s' % random.randint(0, 10000)
        domid = 'b492ba80-99a4-4fd9-8814-b543b2670746'
        res = self.system.create_domain(name, parent_domain_id=None)

    def test_create_vm(self):
        name = 'vm-%s' % random.randint(0, 10000)
        displayname = name
        serviceofferingid = '1e6fbb0a-12ff-4493-b096-cc2b5cc7062c'
        templateid = '9c91464f-f22c-4686-a2ae-4a9daf8f2cb5'
        zoneid = 'd159496e-6fc6-4d31-a6cf-f453563fcc41'
        domainid = 'b0ba6f68-2f5c-11e4-a368-00505602012d'
        account = 'admin'
        hypervisor = 'KVM'
        networkids = '4a813e07-87d7-4a9b-8a0f-ca658c41d23c'
        hostid = None
        
        clsk_job_id = self.system.create_vm(name, displayname, serviceofferingid, 
                                    templateid, zoneid, domainid, account, 
                                    hypervisor, networkids, hostid=hostid)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_create_isolated_sdn(self):
        name = 'net-%s' % random.randint(0, 10000)
        displaytext = name
        networkoffering_id = 'c4d5b79e-8661-4d0f-841f-800efdcab95a'
        zoneid = 'd159496e-6fc6-4d31-a6cf-f453563fcc41'
        domain = 'ROOT/CSI'
        account = 'sistemisti'
        networkdomain = 'acs1.local.it'
        gateway = '172.16.2.1'
        netmask = '255.255.255.0'
        startip = '172.16.2.2'
        endip = '172.16.2.254'        
        res = self.system.create_isolated_sdn(name, displaytext, 
                                              networkoffering_id, 
                                              zoneid, domain=domain, 
                                              account=account, 
                                              networkdomain=networkdomain,
                                              gateway=gateway, netmask=netmask, 
                                              startip=startip, endip=endip)

    def test_create_guest_sdn(self):
        name = 'net-%s' % random.randint(0, 10000)
        displaytext = name
        networkoffering_id = '6b4adb1a-7400-441f-85d0-4cb444173139'
        zoneid = 'd159496e-6fc6-4d31-a6cf-f453563fcc41'
        domain = 'ROOT/CSI'
        account = 'sistemisti'
        account = None
        networkdomain = 'acs1.local.it'
        gateway = '44.44.44.1'
        netmask = '255.255.255.0'
        startip = '44.44.44.3'
        endip = '44.44.44.254'
        vlan = 3001
        res = self.system.create_guest_sdn(name, displaytext, 
                                           networkoffering_id, 
                                           zoneid, 
                                           gateway, netmask, startip, endip, vlan,
                                           domain=domain, account=account,
                                           shared=True,
                                           networkdomain=networkdomain)

    def test_create_data_volume(self):
        name = 'datavol-%s' % random.randint(0, 10000)
        diskofferingid = 'b3ed1ca3-a4d6-4785-870e-ee5d94e9f45d'
        zoneid = 'd159496e-6fc6-4d31-a6cf-f453563fcc41'
        domain = 'ROOT/CSI'
        account = 'sistemisti'
        size = 10
        #virtualmachineid = '0f02e724-10c4-4995-8858-aa551b775484'
                
        clsk_job_id = self.system.create_data_volume(name, zoneid,
                                 domain=domain, account=account,
                                 diskofferingid=diskofferingid, 
                                 snapshotid=None,
                                 size=size,
                                 virtualmachineid=None,
                                 maxiops=None, miniops=None)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        fres = self.pp.pformat(jobres)
        self.logger.debug(jobres)

    def test_upload_data_volume(self):
        name = 'datavol-%s' % random.randint(0, 10000)
        format = 'QCOW2'
        url = ''
        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        domainid = '92e75598-4604-43d3-a8ad-b3a96bfabcb1'
        account = 'oasis'
      
        clsk_job_id = self.system.upload_data_volume(name, zoneid, format, url,
                                 domain_id=None, domain=None, account=None,
                                 checksum=None, 
                                 imagestoreuuid=None)


    def test_register_template(self):
        name = 'tmpl-%s' % random.randint(0, 10000)
        displaytext = name
        format = 'QCOW2'
        hypervisor = 'KVM'
        ostypeid = 'ae6678fe-d518-11e3-8225-0050560203f1'
        url = 'http://10.102.47.205/storage/template/CentOS-6.5-minimal.qcow2.gz'
        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        domainid = 'b07b93ba-e402-42bf-8a5c-d9542f41be2a'
        account = 'OASIS'
      
        res = self.system.register_template(name, displaytext, format, 
                                            hypervisor, ostypeid, url, 
                                            zoneid, domainid=domainid, 
                                            account=account, bits='64')


    def test_register_iso(self):
        name = 'iso-%s' % random.randint(0, 10000)
        displaytext = name
        hypervisor = 'KVM'
        ostypeid = 'ae6678fe-d518-11e3-8225-0050560203f1'
        url = 'http://10.102.47.205/storage/iso/virtio-win-0.1-74.iso'
        zoneid = '2af97976-9679-427b-8dbd-6b11f9dfa169'
        domainid = 'b07b93ba-e402-42bf-8a5c-d9542f41be2a'
        account = 'OASIS'
      
        res = self.system.register_iso(name, displaytext,
                                       hypervisor, ostypeid, url, 
                                'test_list_event_types',            zoneid, bits='64')


    def test_list_event_types(self):
        self.system.list_event_types()
        
    def test_list_events(self):
        res = self.system.list_events(page=1, pagesize=10)

    def test_archive_events(self):
        ids = '12386af1-5b09-4784-9e3b-26b981066965'
        #ids = None
        enddate = None
        #enddate = '2014-05-20'
        startdate = None
        #startdate = '2014-05-21'
        res = self.system.archive_events(ids=ids, 
                                        enddate=enddate, 
                                        startdate=startdate)

    def test_delete_events(self):
        ids = '12386af1-5b09-4784-9e3b-26b981066965'
        ids = None
        enddate = None
        enddate = '2014-05-20'
        startdate = None
        startdate = '2014-05-20'
        res = self.system.delete_events(ids=ids, 
                                        enddate=enddate, 
                                        startdate=startdate)


    def test_list_alerts(self):
        res = self.system.list_alerts(page=1, pagesize=10)

    def test_generate_archive_alert(self):
        name = 'alert-%s' % random.randint(0, 10000)
        description = name
        atype = 100
        clsk_job_id = self.system.generate_alert(description, name, atype, 
                                                 zoneid=None, podid=None)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        self.logger.debug(jobres)
        
        self.system.list_alerts(page=1, pagesize=10, atype=100)
        
        res = self.system.archive_alerts(atype=atype)
        self.logger.debug(res)        


    def test_generate_delete_alert(self):
        name = 'alert-%s' % random.randint(0, 10000)
        description = name
        atype = 100
        clsk_job_id = self.system.generate_alert(description, name, atype, 
                                                 zoneid=None, podid=None)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        self.logger.debug(jobres)
        
        self.system.list_alerts(page=1, pagesize=10, atype=100)
        
        res = self.system.delete_alerts(atype=atype)
        self.logger.debug(res)

    def test_list_tags(self):
        res = self.system.list_tags(value='prova')
        self.logger.debug(self.pp.pformat(res))  

    # usage
    def test_get_usage_type(self):
        self.system.get_usage_type()
        
    def test_get_usage_data(self):
        self.system.get_usage_data('bf883db3-e85b-4e12-9e7b-dddb9af2f9a8',
                                   accountid='22e34c74-e45e-42d5-9fa4-636c610db617',
                                   usage_type=2,
                                   oid='a492dfa0-6c1a-461c-a991-2bf475aca8b7')

def test_suite():
    tests = [
             #'test_ping',
             #'test_info',
             #'test_get_hypervisors',
             
             ##'test_list_deployment_planners',
             ##'test_list_configurations',
             ##'test_update_configuration',
             ##'test_list_ldap_configurations',             
             
             ##'test_list_tags',
             
             #'test_list_event_types',
             #'test_list_events',
             #'test_archive_events',
             #'test_delete_events',             
             
             #'test_list_alerts',
             ##'test_archive_alerts',
             ##'test_delete_alerts',
             ##'test_generate_archive_alert',
             ##'test_generate_delete_alert',             

             ##'test_get_cloud_identifier',
             ##'test_login',
             ##'test_logout',
             
             #'test_list_regions',
             #'test_list_zones',
             #'test_list_pods',
             #'test_list_clusters',
             #'test_list_hosts',
             #'test_list_storagepools',
             ##'test_list_imagestores',
             #'test_list_system_vms',
             #'test_list_routers',
             #'test_list_virtual_machines',
             #'test_list_volumes',
             #'test_list_sdns',
             #'test_list_physical_networks',
             #'test_list_remote_access_vpns',
             #'test_list_public_ip_addresses',
             #'test_list_os_categories',
             #'test_list_os_types',
             #'test_list_templates',
             #'test_list_isos',
             #'test_list_domains',
             #'test_list_accounts',
             #'test_list_service_offerings',
             #'test_list_network_offerings',
             #'test_list_disk_offerings',
             #'test_get_domain_id',
             #'test_get_account_id',
             #'test_get_domain_path',

             #'test_create_domain',
             #'test_create_vm',
             #'test_create_isolated_sdn',
             #'test_create_guest_sdn',
             #'test_create_data_volume',
             ####'test_upload_data_volume',
             
             ##'test_register_template',
             ##'test_register_iso',
             
             #'test_tree_physical',
             #'test_tree_logical',
             ##'test_tree_network',
             
             'test_get_usage_type',
             'test_get_usage_data',
            ]
    return unittest.TestSuite(map(ClskOrchestratorTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])