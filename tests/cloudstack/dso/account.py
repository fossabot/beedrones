'''
Created on Sep 2, 2013

@author: darkbk
'''
import logging
import unittest
import traceback
import random
import pprint
from gibboncloud.cloudstack.dso import ApiClient
from gibboncloud.cloudstack.dso import ClskObjectError
from gibboncloud.cloudstack.dso import Account, System
from gibbonutil.perf import watch_test

class AccountTestCase(unittest.TestCase):
    logger = logging.getLogger('gibbon.test')

    def setUp(self):
        self.logger.debug('\n########## %s.%s ##########' % 
                          (self.__module__, self.__class__.__name__))
        
        from gibboncloud.tests.config import params
        base_url = params['gibbon_cloud.cloudstack.dso']['base_url']
        api_key = params['gibbon_cloud.cloudstack.dso']['api_key']
        sec_key = params['gibbon_cloud.cloudstack.dso']['sec_key']
        
        domain_id = '1239b151-d6be-4f2f-88e4-66507cd0fdaa'
        account_id = '47f09d80-ec8c-46d9-a450-cfb0e372f2a9'
        self.zone_id = '4cfb99c5-f5a6-4a8e-95b5-88eb860e3dc6'
        
        api_client = ApiClient(base_url, api_key, sec_key)
        system = System(api_client, name='clsk42', oid='clsk42')
        self.account = system.list_accounts(domain='ROOT/CSI', account='account-434')[0]
        
        self.pp = pprint.PrettyPrinter() 
        
    def tearDown(self):
        pass

    @watch_test
    def test_tree(self):
        try:
            res = self.account.tree()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_info(self):
        try:
            res = self.account.info()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_delete(self):
        try:
            job_id = 1
            res = self.account.delete(job_id)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_get_resource_limit(self):
        try:
            res = self.account.get_resource_limit()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_update_resource_limit(self):
        try:
            type = 0
            max = 0
            res = self.account.update_resource_limit(type, max)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_all_virtual_machines(self):
        try:
            res = self.account.list_all_virtual_machines()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_system_vms(self):
        try:
            res = self.account.list_system_vms()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_routers(self):
        try:
            res = self.account.list_routers()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_virtual_machines(self):
        try:
            res = self.account.list_virtual_machines()
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_templates(self):
        try:
            hypervisor = 'KVM'
            res = self.account.list_templates(self.zone_id, hypervisor)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_isos(self):
        try:
            hypervisor = 'KVM'
            res = self.account.list_isos(self.zone_id, hypervisor)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_list_networks(self):
        try:
            hypervisor = 'KVM'
            res = self.account.list_networks(hypervisor)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

    @watch_test
    def test_create_private_guest_network(self):
        try:
            name = '%s-net-%s' % (self.account_name, random.randint(0, 10000))
            displaytext = name
            res = self.account.test_create_private_guest_network(
                    name, displaytext, self.networkoffering_id, self.zone_id)
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)           

    @watch_test
    def test_create_direct_guest_network(self):
        try:
            hypervisor = 'KVM'
            res = self.account.create_direct_guest_network(
                    name, displaytext, networkoffering_id, zone_id, 
                    physical_network_id, gateway, netmask, 
                    startip, endip, vlan)
            fres = self.pp.pformat(res)
            self.logger.debug(res)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)

def test_suite():
    tests = [#'test_tree',
             #'test_info',
             #'test_delete',
             #'test_get_resource_limit',
             #'test_update_resource_limit',
             #'test_list_all_virtual_machines',
             #'test_list_system_vms',
             #'test_list_routers',
             #'test_list_virtual_machines',
             #'test_list_templates',
             'test_list_isos',
             #'test_list_networks',
             #'test_create_private_guest_network',
             #'test_create_direct_guest_network',
            ]
    return unittest.TestSuite(map(AccountTestCase, tests))

if __name__ == '__main__':
    import os
    from gibbonutil.test_util import run_test
    syspath = os.path.expanduser("~")
    log_file = syspath + '/workspace/gibbon/util/log/test.log'
    run_test([test_suite()], log_file)  