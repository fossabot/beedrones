'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
import time
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from gibboncloud.cloudstack.api_client import ApiClient, SDN
from gibboncloud.virt import VirtManager

class SDNTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        self.setup_cloudstack()
        
        net_id = '9a8731d7-1cef-4b04-bb8a-c2b115c1366a' # admin-network-01
        net_id = '48a74a6f-c839-4ffc-9fa6-d5f9d453cd56' # oasis-network01
        #net_id = '5f7a7282-65c5-4b40-8d6d-da7f21f890e5' # oasis-network01-ext

        self.net = SDN(self.api_client, oid=net_id)
        self.net.extend(self.db_session, self.hypervisors)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)

    @watch_test
    def test_info(self):
        res = self.net.info()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)

    @watch_test
    def test_get_network_type(self):
        res = self.net.get_network_type()
        self.logger.debug(res)     

    @watch_test
    def test_get_service(self):
        res = self.net.get_service()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)        
    
    @watch_test
    def test_restart(self):
        res = self.net.restart(1)

    @watch_test
    def test_delete(self):
        res = self.net.delete(1)
        
    @watch_test
    def test_list_all_virtual_machines(self):
        res = self.net.list_all_virtual_machines()

    @watch_test
    def test_tree(self):
        res = self.net.tree()

    #-----------------------------------VPN------------------------------------#
    @watch_test
    def test_list_remote_access_vpns(self):
        res = self.net.list_remote_access_vpns(ipaddressid='c08a5410-1bf3-4250-b1ed-41a0354c9821')
        
    @watch_test
    def test_create_remote_access_vpn(self):
        clsk_job_id = self.net.create_remote_access_vpn('c08a5410-1bf3-4250-b1ed-41a0354c9821')
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        
    @watch_test
    def test_delete_remote_access_vpn(self):
        clsk_job_id = self.net.delete_remote_access_vpn('c08a5410-1bf3-4250-b1ed-41a0354c9821')
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)

    @watch_test
    def test_list_vpn_user(self):
        res = self.net.list_vpn_user()

    @watch_test
    def test_add_vpn_user(self):
        clsk_job_id = self.net.add_vpn_user('test', 'test')
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        
    @watch_test
    def test_remove_vpn_user(self):
        clsk_job_id = self.net.remove_vpn_user('test')
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
    #-----------------------------------VPN------------------------------------#

    #-----------------------------------PUBLIC IP------------------------------#
    @watch_test
    def test_list_public_ip_addresses(self):
        res = self.net.list_public_ip_addresses()
        
    @watch_test
    def test_associate_disassociate_public_ip_addresses(self):
        # associate
        clsk_job_id = self.net.associate_public_ip_addresses()
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # disassociate
        ipaddressid = data['jobresult']['ipaddress']['id']
        clsk_job_id = self.net.disassociate_public_ip_addresses(ipaddressid)
        self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        
    #-----------------------------------PUBLIC IP------------------------------#        

    #-----------------------------------FIREWALL-------------------------------#
    @watch_test
    def test_list_firewall_rules(self):
        res = self.net.list_firewall_rules()

    @watch_test
    def test_create_remove_firewall_rule(self):
        # create
        ipaddressid = 'c08a5410-1bf3-4250-b1ed-41a0354c9821'
        protocol = 'tcp'
        cidrlist = '0.0.0.0/0'
        ftype = 'user'
        startport = 980
        endport = 981
        clsk_job_id = self.net.create_firewall_rule(ipaddressid, protocol, 
                                                    cidrlist, ftype, 
                                                    startport=startport, 
                                                    endport=endport)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # list
        self.net.list_firewall_rules()
        # delete
        firewall_rule_id = data['jobresult']['firewallrule']['id']
        clsk_job_id = self.net.delete_firewall_rule(firewall_rule_id)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)        
        
    #-----------------------------------FIREWALL-------------------------------#

    #------------------test_get_network_type-----------------PORT FORWARD---------------------------#
    @watch_test
    def test_list_port_forwarding_rules(self):
        res = self.net.list_port_forward_rules()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    @watch_test
    def test_create_remove_port_forward_rule(self):
        # create
        ipaddressid = 'c08a5410-1bf3-4250-b1ed-41a0354c9821'
        protocol = 'tcp'
        ftype = 'user'
        privateport = 980
        privateendport = 981
        publicport = 980
        publicendport = 981
        virtualmachineid = '03d38085-154a-454e-9aa0-b81c717dc9ff'
        clsk_job_id = self.net.create_port_forward_rule(ipaddressid, protocol, 
                                                        virtualmachineid, 
                                                        privateport, 
                                                        privateendport, 
                                                        publicport, 
                                                        publicendport)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # list
        self.net.list_port_forward_rules(ipaddressid)
        # delete
        port_forward_rule_id = data['jobresult']['portforwardingrule']['id']
        clsk_job_id = self.net.delete_port_forward_rule(port_forward_rule_id)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)          
    #-----------------------------------PORT FORWARD---------------------------#

    #-----------------------------------EGRESS RULES---------------------------#
    @watch_test
    def test_list_egress_rules(self):
        res = self.net.list_egress_rules()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    @watch_test
    def test_create_remove_egress_rule(self):
        # create
        ipaddressid = 'c08a5410-1bf3-4250-b1ed-41a0354c9821'
        protocol = 'tcp'
        cidrlist = '0.0.0.0/0'
        ftype = 'user'
        startport = 980
        endport = 981
        clsk_job_id = self.net.create_egress_rule(ipaddressid, protocol, 
                                                  cidrlist, ftype, 
                                                  startport=startport, 
                                                  endport=endport)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # list
        self.net.list_egress_rules()
        # delete
        egress_rule_id = data['jobresult']['firewallrule']['id']
        clsk_job_id = self.net.delete_egress_rule(egress_rule_id)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)          
    #-----------------------------------EGRESS RULES---------------------------#

    #-----------------------------------LOAD BALANCE---------------------------#
    @watch_test
    def test_list_load_balancer_rules(self):
        res = self.net.list_load_balancer_rules()
        fres = self.pp.pformat(res)
        self.logger.debug(fres)
        
    @watch_test
    def test_create_remove_load_balancer_rule(self):
        # create
        name = 'lb1'
        description = name
        algorithm = 'roundrobin'
        privateport = 1000
        publicport = 95
        publicipid = 'c08a5410-1bf3-4250-b1ed-41a0354c9821'
        virtualmachineids = '03d38085-154a-454e-9aa0-b81c717dc9ff'
        methodname = 'LbCookie'
        clsk_job_id = self.net.create_load_balancer_rule(name, description,
                                                         algorithm,
                                                         privateport, 
                                                         publicport, 
                                                         publicipid, 
                                                         protocol='tcp')
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # assign vm
        load_balancer_id = data['jobresult']['loadbalancer']['id']
        clsk_job_id = self.net.assign_to_load_balancer_rule(load_balancer_id, 
                                                            virtualmachineids)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # create stickiness
        clsk_job_id = self.net.create_lb_stickiness_policy(load_balancer_id, 
                                                           name, description,
                                                           methodname)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # list lb stickiness policies
        self.net.list_lb_stickiness_policies(load_balancer_id)
        # remove
        """
        {u'stickinesspolicy': [{u'params': {}, u'description': u'lb1', 
                                u'methodname': u'LbCookie', 
                                u'id': u'78417a16-bcf9-429d-af68-66e1da8db11b', 
                                u'name': u'lb1'}], 
         u'account': u'oasis', 
         u'lbruleid': u'93711ff0-182a-4b6e-8f79-3e6b7dabe32e', 
         u'domainid': u'92e75598-4604-43d3-a8ad-b3a96bfabcb1', 
         u'domain': u'PRG-EUROPEI'}
        """
        policy_id = data['jobresult']['stickinesspolicies']['stickinesspolicy'][0]['id']
        clsk_job_id = self.net.delete_lb_stickiness_policy(policy_id)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        
        # create lb health check policies
        #self.net.create_lb_health_check_policy(lbruleid, description, healthythreshold, intervaltime, pingpath, responsetimeout, unhealthythreshold)
        
        # list lb health check policies
        self.net.list_lb_health_check_policies(load_balancer_id)
        # remove lb health check policies
        #self.net.delete_lb_health_check_policy(policy_id)
        
        # list
        self.net.list_load_balancer_rules()
        self.net.list_load_balancer_rule_instances(load_balancer_id)
        # remove vm
        clsk_job_id = self.net.remove_from_load_balancer_rule(load_balancer_id, 
                                                              virtualmachineids)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)
        # delete
        clsk_job_id = self.net.delete_load_balancer_rule(load_balancer_id)
        data = self.query_async_clsk_job(self.api_client, 1, clsk_job_id)          
    #-----------------------------------LOAD BALANCE---------------------------#
    
    #-----------------------------------STATIC NAT-----------------------------#
    @watch_test
    def test_is_enabled_source_nat(self):
        ipaddressid = '2aa96042-7c1e-4c6a-a2f1-a0a887b2ad11'
        res = self.net.is_enabled_source_nat(ipaddressid)
        self.logger.debug(res)
    
    @watch_test
    def test_is_enabled_static_nat(self):
        ipaddressid = '2aa96042-7c1e-4c6a-a2f1-a0a887b2ad11'
        res = self.net.is_enabled_static_nat(ipaddressid)
        self.logger.debug(res)
        
    @watch_test
    def test_enable_static_nat(self):
        ipaddressid = '2aa96042-7c1e-4c6a-a2f1-a0a887b2ad11'
        virtualmachineid = '4b728f59-1133-4756-8ca4-42af1322da9a'
        res = self.net.enable_static_nat(ipaddressid, virtualmachineid)

    @watch_test
    def test_disable_static_nat(self):
        ipaddressid = '2aa96042-7c1e-4c6a-a2f1-a0a887b2ad11'
        res = self.net.disable_static_nat(ipaddressid)
    #-----------------------------------STATIC NAT-----------------------------#


def test_suite():
    tests = [
             #'test_info',
             #'test_get_network_type',
             #'test_get_service',
             #'test_restart',
             #'test_delete',
             #'test_list_all_virtual_machines',
             #'test_tree',
             
             #'test_create_remote_access_vpn',
             #'test_list_remote_access_vpns',
             #'test_add_vpn_user',
             #'test_list_vpn_user',
             #'test_remove_vpn_user',
             #'test_delete_remote_access_vpn',
             
             #'test_list_public_ip_addresses',
             #'test_associate_disassociate_public_ip_addresses',
             
             #'test_list_firewall_rules',
             #'test_create_remove_firewall_rule',
             
             #'test_list_port_forwarding_rules',
             #'test_create_remove_port_forward_rule',
             
             #'test_list_egress_rules',
             #'test_create_remove_egress_rule',
             
             ##'test_list_load_balancer_rules',
             ##'test_create_remove_load_balancer_rule',
             
             'test_enable_static_nat',
             'test_is_enabled_source_nat',
             'test_is_enabled_static_nat',
             'test_disable_static_nat',
            ]
    return unittest.TestSuite(map(SDNTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])