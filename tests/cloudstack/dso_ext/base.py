'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import os
import pprint
from gibbon_cloud.cloudstack.dso_ext.base import MysqlConnectionManager
from gibbon_cloud.cloudstack.dso_ext.base import QemuConnectionManager
from gibbon_cloud.cloudstack.dso_ext.base import ClskConnectionManager
from gibbon_cloud.cloudstack.dso_ext.base import ApiManager, ApiManagerError
from gibbon_utility.perf import watch_test 

class ClskConnectionManagerTestCase(unittest.TestCase):
    logger = logging.getLogger('test')

    def setUp(self):
        self.logger.debug('########## START ##########')

        from tests.gibbon_cloud.config import params
        
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
        self.manager = ClskConnectionManager(name, id, api_params, db_manager)
        
        hid = 'clsk42_qemu_1'
        host = '10.102.47.205'
        port = '16509'
        qemu_manager = QemuConnectionManager(hid, host, port)
        self.manager.add_hypervisor('qemu', qemu_manager)

        hid = 'clsk42_qemu_2'
        host = '10.102.47.205'
        port = '16510'
        qemu_manager = QemuConnectionManager(hid, host, port)
        self.manager.add_hypervisor('qemu', qemu_manager)
        
        self.pp = pprint.PrettyPrinter()
    
    def tearDown(self):
        self.logger.debug('########## STOP  ##########\n')

    @watch_test
    def test_remove_hypervisor(self):
        try:
            hid = 'clsk42_qemu_2'
            res = self.manager.remove_hypervisor('qemu', hid)
            self.logger.debug(res)
        except ApiManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_get_hypervisor(self):
        try:
            hid = 'clsk42_qemu_2'
            res = self.manager.get_hypervisor('qemu', hid)
            self.logger.debug(res)
        except ApiManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_get_api_client(self):
        try:
            res = self.manager.get_api_client()
            self.logger.debug(res)
        except ApiManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_get_db_conn(self):
        try:
            conn = self.manager.get_db_conn()
            self.manager.release_db_conn(conn)
            self.logger.debug(conn)
        except ApiManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_get_db_session(self):
        try:
            session = self.manager.get_db_session()
            session.close()
            self.logger.debug(session)
        except ApiManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
            
    @watch_test
    def test_get_hypervisor_conn(self):
        try:
            hid = 'clsk42_qemu_2'
            conn = self.manager.get_hypervisor_conn('qemu', hid)
            self.manager.release_hypervisor_conn('qemu', hid, conn)
            self.logger.debug(conn)
        except ApiManagerError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [
             #'test_remove_hypervisor',
             'test_get_hypervisor',
             'test_get_api_client',
             'test_get_db_conn',
             'test_get_db_session',
             'test_get_hypervisor_conn',
            ]
    return unittest.TestSuite(map(ClskConnectionManagerTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbon_utility.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)            