'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
from gibboncloud.cloudstack.dso_ext.base import MysqlConnectionManager
from gibboncloud.cloudstack.dso_ext.base import ClskConnectionManager
from gibboncloud.cloudstack.dso_ext.base import ApiManager, ApiManagerError
from gibboncloud.cloudstack.dso_ext import NetworkExt
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase

class NetworkExtTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        base_url = "http://10.102.90.207:8080/client/api"
        #base_url = "http://158.102.160.234:5000/api/clsk/clsk42_01"
        #base_url = "http://172.16.0.19:8081/client/api"
        api_params = {'uri':base_url,
                      'api_key':"oo25khLLZCJTWYBbpt8PthN4hSoeP93-pXJeZFvkYncgK1w1jzYpT-UX-ucH1SsStzNZpgWjlzPLHxHZQqmzcg",
                      'sec_key':"d85PXqWsMy0sHV7Kjip_tH8Ejr93wlHokc7E4_dtSXrPAoAzQ4PVzoDoAQ18gReubkipJqLvQJWNFGcfVBTcOQ"}
        
        mid = 'clsk42_db'
        host = '10.102.90.207'
        port = '3306'
        name = 'cloud'
        user = 'cloud'
        pwd = 'testlab'
        db_manager = MysqlConnectionManager(mid, host, port, name, user, pwd)
        
        name = 'clsk42'
        id = name
        clsk_manager = ClskConnectionManager(name, id, api_params, db_manager)        
        
        net_id = '48a74a6f-c839-4ffc-9fa6-d5f9d453cd56'
        self.net = NetworkExt(clsk_manager, oid=net_id)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    @watch_test
    def test_info(self):
        res = self.net.info()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_restart(self):
        res = self.net.restart(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_delete(self):
        res = self.net.delete(1)
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    #-----------------------------------VPN------------------------------------#
    @watch_test
    def test_list_remote_access_vpns(self):
        res = self.net.list_remote_access_vpns(ipaddressid='c08a5410-1bf3-4250-b1ed-41a0354c9821')
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    @watch_test
    def test_create_remote_access_vpn(self):
        res = self.net.create_remote_access_vpn('c08a5410-1bf3-4250-b1ed-41a0354c9821')
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    @watch_test
    def test_delete_remote_access_vpn(self):
        res = self.net.delete_remote_access_vpn('c08a5410-1bf3-4250-b1ed-41a0354c9821')
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_list_vpn_user(self):
        res = self.net.list_vpn_user()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_add_vpn_user(self):
        res = self.net.add_vpn_user('test', 'test')
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    @watch_test
    def test_remove_vpn_user(self):
        res = self.net.remove_vpn_user('test')
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
    #-----------------------------------VPN------------------------------------#

    @watch_test
    def test_list_public_ip_addresses(self):
        #res = self.net.list_public_ip_addresses(ipaddressid='c08a5410-1bf3-4250-b1ed-41a0354c9821')
        res = self.net.list_public_ip_addresses()
        fres = self.pp.pformat(res)
        self.logger.debug(fres) 

    @watch_test
    def test_list_firewall_rules(self):
        res = self.net.list_firewall_rules()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)    

    @watch_test
    def test_list_port_forwarding_rules(self):
        res = self.net.list_port_forwarding_rules()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_list_egress_firewall_rules(self):
        res = self.net.list_egress_firewall_rules()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_list_all_virtual_machines(self):
        res = self.net.list_all_virtual_machines()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

def test_suite():
    tests = [
             #'test_info',
             #'test_restart',
             #'test_delete',
             #'test_tree',
             'test_create_remote_access_vpn',
             'test_list_remote_access_vpns',
             'test_add_vpn_user',
             'test_list_vpn_user',
             'test_remove_vpn_user',
             'test_delete_remote_access_vpn',
             #'test_list_public_ip_addresses',
             #'test_list_firewall_rules',
             #'test_list_port_forwarding_rules',
             #'test_list_egress_firewall_rules',
             #'test_list_all_virtual_machines',
            ]
    return unittest.TestSuite(map(NetworkExtTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])