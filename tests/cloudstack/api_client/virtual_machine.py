'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
import random
from tests.test_util import run_test, CloudTestCase
from gibboncloud.cloudstack.api_client import ClskOrchestrator

vmid = None

class VirtualMachineTestCase(CloudTestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """
    
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        # 8d968643-3916-448c-955f-92e1beb5b115
        # e834408b-24e1-446f-8989-8362f88b09b3
        # vmid = '8a6a9add-1b33-4a5f-9c65-501c768d3bd9'
        self.orch = ClskOrchestrator(self.api_client, db_manager=self.db_session, 
                                     name='clsk43', oid='clsk43', active=True)
        global vmid
        if vmid != None:
            self.virtual_machine = self.orch.list_virtual_machines(oid=vmid)[0]
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

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
        
        clsk_job_id = self.orch.create_vm(1, name, displayname, serviceofferingid, 
                                    templateid, zoneid, domainid, account, 
                                    hypervisor, networkids, hostid=hostid)
        jobres = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        global vmid
        vmid = jobres['jobresult']['virtualmachine']['id']

    def test_get_state(self):
        res = self.virtual_machine.state

    def test_info(self):
        fres = self.pp.pformat(self.virtual_machine.__dict__)
        self.logger.debug(fres)

    def test_configuration(self):
        res = self.virtual_machine.configuration()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_list_volumes(self):
        res = self.virtual_machine.list_volumes()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_get_root_volume(self):
        res = self.virtual_machine.get_root_volume().info()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_attach_volume(self):
        clsk_job_id = self.virtual_machine.attach_volume(self.virtualmachineid)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        
    def test_detach_volume(self):
        clsk_job_id = self.virtual_machine.detach_volume(self.virtualmachineid)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_list_nics(self):
        res = self.virtual_machine.list_nics()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_change_password(self):
        password = 'mypass'
        clsk_job_id = self.virtual_machine.change_password()
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        res = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_change_graphics_password(self):
        password = 'mypass'
        res = self.virtual_machine.change_graphics_password(password)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    def test_get_graphics_password(self):
        res = self.virtual_machine.get_graphics_password()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_create_vv_file(self):
        res = self.virtual_machine.create_vv_file()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_start(self):
        clsk_job_id = self.virtual_machine.start()
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
            
    def test_stop(self):
        clsk_job_id = self.virtual_machine.stop(forced=True)
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_reboot(self):
        clsk_job_id = self.virtual_machine.reboot()
        if not self.virtual_machine.is_extended():
            self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_destroy(self):
        clsk_job_id = self.virtual_machine.destroy()
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_expunge(self):
        clsk_job_id = self.virtual_machine.expunge()
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_restore(self):
        clsk_job_id = self.virtual_machine.restore()
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_assign(self):
        account = 'oasis'
        domainid = '92e75598-4604-43d3-a8ad-b3a96bfabcb1'
        networkids = '48a74a6f-c839-4ffc-9fa6-d5f9d453cd56'
        res = self.virtual_machine.assign(account, domainid, networkids)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_update(self):
        displayname = 'pippo'
        res = self.virtual_machine.update(displayname)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    def test_migrate_hot(self):
        clsk_job_id = self.virtual_machine.migrate(hostid=self.cid1)
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_migrate_cold(self):
        # stop vm
        clsk_job_id = self.virtual_machine.stop(forced=True)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        self.logger.debug('vm status: %s' % self.virtual_machine.get_state())
        # start vm
        clsk_job_id = self.virtual_machine.start(hostid=self.cid2)
        self.query_async_clsk_job(self.api_client, 2, clsk_job_id)
        self.logger.debug('vm status: %s' % self.virtual_machine.get_state())
        # add device
        #devices = self.virtual_machine.get_extra_devices()
        #res = self.virtual_machine.append_devices(devices)

    def test_attach_iso(self):
        #CentOS-6.5-x86_64-minimal
        iso_id= 'ca93b969-d4d1-425b-b94e-0521fd37c8fc'
        clsk_job_id = self.virtual_machine.attach_iso(iso_id)
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_detach_iso(self):
        iso_id= 'ca93b969-d4d1-425b-b94e-0521fd37c8fc'
        clsk_job_id = self.virtual_machine.detach_iso(iso_id)
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_create_template(self):
        name = 'tmplwin81telelav-final'
        displaytext = name
        clsk_job_id = self.virtual_machine.create_template(name, displaytext)
        #ostypeid='9daa7858-db44-11e3-b14c-001e4f153171')
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_create_snapshot(self):
        pass
    
    def test_revert_to_snapshot(self):
        pass
    
    def test_delete_snapshot(self):
        pass
    
    def test_list_tags(self):
        res = self.virtual_machine.list_tags()
        self.logger.debug(self.pp.pformat(res))

    def test_create_tags(self):
        clsk_job_id = self.virtual_machine.create_tags([('test', 'test')])
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    def test_delete_tags(self):
        clsk_job_id = self.virtual_machine.delete_tags([('test', 'test')])
        fres = self.pp.pformat(clsk_job_id)
        self.logger.debug(fres)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

def test_suite():
    tests = ['test_create_vm',
             'test_get_state',
             'test_info',
             ##'test_configuration',
             ##'test_list_volumes',
             ##'test_list_nics',
             ##'test_get_root_volume',
             ##'test_attach_volume',
             ##'test_detach_volume',
             
             ##'test_change_graphics_password',
             ##'test_create_vv_file',
             ##'test_stop',
             ##'test_assign',
             ##'test_change_password',
             ##'test_start',
             ##'test_stop',
             ##'test_start',
             ##'test_get_ext_devices',
             ##'test_get_graphics_password',
             ##'test_reboot',
             'test_destroy',
             'test_expunge',
             ##'test_restore',
             ##'test_update',

             ##'test_migrate_hot',
             ##'test_migrate_cold',
             ##'test_attach_iso',
             ##'test_detach_iso',
             
             ##'test_create_template',
             ##'test_create_snapshot',
             ##'test_revert_to_snapshot',
             ##'test_delete_snapshot',
             
             ##'test_create_tags',
             ##'test_list_tags',
             ##'test_delete_tags',
            ]
    return unittest.TestSuite(map(VirtualMachineTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])