'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.dso.base import ApiClient
from gibboncloud.cloudstack.dso.virtual_machine import ClskObjectError
from gibboncloud.cloudstack.dso.system import System
from gibboncloud.cloudstack.dso.domain import Domain
from gibboncloud.cloudstack.dso.account import Account
from gibbonutil.perf import watch_test 

class DomainTestCase(unittest.TestCase):
    logger = logging.getLogger('gibbon.test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from tests.gibboncloud.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        
        api_client = ApiClient(base_url, api_key, sec_key)
        system = System(api_client, name='clsk42', oid='clsk42')
        self.domain = system.list_domains(domain_id='e245ad4c-4bad-4611-bbc3-05a46cdd375d')[0]
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_info(self):
        try:
            res = self.domain.info()
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_delete(self):
        try:
            res = self.domain.delete(1)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_accounts(self):
        try:
            res = self.domain.list_accounts()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_create_account(self):
        try:
            name = 'account-%s' % random.randint(0, 10000)
            type = 'USER'
            firstname = name
            lastname = name
            username = name
            password = name
            email = "%s@localhost.localdomain" % name
            res = self.domain.create_account(name, type, firstname, 
                                             lastname, username, password,
                                             email, timezone='CET')
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [
             'test_delete',
             #'test_info',
             #'test_list_accounts',
             #'test_list_create_account',
            ]
    return unittest.TestSuite(map(DomainTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbonutil.test_util import run_test
    
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)  