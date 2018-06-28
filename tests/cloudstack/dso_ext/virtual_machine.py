'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.dso_ext.base import MysqlConnectionManager
from gibboncloud.cloudstack.dso_ext.base import QemuConnectionManager
from gibboncloud.cloudstack.dso_ext.base import ClskConnectionManager
from gibboncloud.cloudstack.dso_ext.base import ApiManager, ApiManagerError
from gibboncloud.cloudstack.dso_ext.virtual_machine import VirtualMachineExt
from gibboncloud.cloudstack.dso.base import ClskObjectError
from gibbonutil.perf import watch_test 

class VirtualMachineExtTestCase(unittest.TestCase):
    logger = logging.getLogger('gibbon.test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from gibboncloud.tests.config import params
        api_params = {'uri':params['gibbon_cloud.cloudstack.dso']['base_url'],
                      'api_key':params['gibbon_cloud.cloudstack.dso']['api_key'],
                      'sec_key':params['gibbon_cloud.cloudstack.dso']['sec_key']}
        
        mid = 'clsk42_db'
        host = '10.102.47.205'
        port = '3308'
        name = 'cloud'
        user = 'cloud'
        pwd = 'testlab'
        db_manager = MysqlConnectionManager(mid, host, port, name, user, pwd)
        
        name = 'clsk42'
        id = name
        clsk_manager = ClskConnectionManager(name, id, api_params, db_manager)
        
        hid = 'kvm-7-12.clskdom.lab'
        host = '10.102.90.3'  #'10.102.47.205'
        host = '172.16.0.19'
        port = '16509'
        qemu_manager = QemuConnectionManager(hid, host, port)
        clsk_manager.add_hypervisor('qemu', qemu_manager)

        hid = 'kvm-7-13.clskdom.lab'
        host = '10.102.90.4' #'10.102.47.205'
        host = '172.16.0.19'
        port = '16509'
        port = '16510'
        qemu_manager = QemuConnectionManager(hid, host, port)
        clsk_manager.add_hypervisor('qemu', qemu_manager)    
        
        vm_id = 'f9a44762-79ad-47f3-bbba-25cda08c710b'
        self.vm = VirtualMachineExt(clsk_manager, oid=vm_id)
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_list_volume(self):
        try:
            res = self.vm.list_volume()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_append_device(self):
        try:
            devices = {u'video_cirrus': '', 'usb_redirect': '', u'spice_graphics': ''}
            res = self.vm.append_device(devices)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_config(self):
        try:
            res = self.vm.config()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_change_graphics_password(self):
        try:
            res = self.vm.change_graphics_password('test1')
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_start(self):
        try:
            res = self.vm.start('1')
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [
             'test_list_volume',
             #'test_append_device',
             #'test_config',
             #'test_change_graphics_password',
             #'test_start',
             #'test_stop',
             #'test_destroy',
             #'test_update',
            ]
    return unittest.TestSuite(map(VirtualMachineExtTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbonutil.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)  