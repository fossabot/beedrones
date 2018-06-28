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
from gibboncloud.cloudstack.dso_ext import VolumeExt
from gibboncloud.cloudstack.dso.base import ClskObjectError
from gibbonutil.perf import watch_test 

class VolumeExtTestCase(unittest.TestCase):
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
        
        vol_id = '30ea5c5d-f688-40e5-8180-8d35eb33dc13'
        self.vol = VolumeExt(clsk_manager, oid=vol_id)
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        try:
            res = self.vol.info()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_get_storagepool_info(self):
        try:
            res = self.vol.get_storagepool_info()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_tree(self):
        try:
            res = self.vol.list_volume()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [#'test_info',
             'test_get_storagepool_info',
             #'test_tree',
            ]
    return unittest.TestSuite(map(VolumeExtTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbonutil.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)  