'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase
from gibboncloud.cloudstack.db_client import VmManager
from gibboncloud.cloudstack.db_client import TransactionError

class VirtualMachineTestCase(CloudTestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """
    def setUp(self):
        CloudTestCase.setUp(self)
        #self.db_uri = "mysql+pymysql://cloud:testlab@172.16.0.19:3306/cloud"
        self.db_uri = "mysql+pymysql://cloud:testlab@10.102.90.207:3306/cloud"
        db_session = self.open_mysql_session(self.db_uri)
        self.session = db_session()
        self.manager = VmManager(self.session)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)
        self.session.close()
        # remove tables
        #ConfigManager.remove_table(self.db_uri)

    @watch_test
    def test_get_device_type(self):
        self.manager.get_device_type('video_qxl')
        
    @watch_test
    def test_get_virt_domain(self):
        clsk_id = 'AAAAA'
        self.manager.get_virt_domain(clsk_id)

    @watch_test
    def test_add_virt_domain1(self):
        clsk_id = 'AAAAA'
        devices = {'video_qxl': '',
                   'usb_redirect': '', 
                   'spice_graphics': '',
                   'sound_card_ich6': ''}        
        self.manager.add_virt_domain(clsk_id, devices)

    @watch_test
    def test_add_virt_domain2(self):
        clsk_id = 'AAAAA'
        devices = {'video_qxl': '',
                   'usb_redirect': '', 
                   'spice_graphics': '',
                   'sound_card_ich6': ''}
        with self.assertRaises(TransactionError):    
            self.manager.add_virt_domain(clsk_id, devices)

    @watch_test
    def test_append_virt_domain_devices(self):
        clsk_id = 'AAAAA'
        devices = {'video_qxl': '',
                   'usb_redirect': '', 
                   'spice_graphics': ''}
        self.manager.append_virt_domain_devices(clsk_id, devices)

    @watch_test
    def test_delete_virt_domain(self):
        clsk_id = 'AAAAA'
        self.manager.delete_virt_domain(clsk_id)

    @watch_test
    def test_update_graphic_password(self):
        clsk_id = 'AAAAA'
        password = 'mypass'
        self.manager.update_graphic_password(clsk_id, password)

def test_suite():
    tests = [
             'test_get_device_type',
             'test_add_virt_domain1',
             'test_add_virt_domain2',
             'test_append_virt_domain_devices',
             'test_get_virt_domain',
             'test_update_graphic_password',
             'test_delete_virt_domain',
            ]
    return unittest.TestSuite(map(VirtualMachineTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])