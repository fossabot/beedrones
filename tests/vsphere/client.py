'''
Created on Dec 14, 2015

@author: darkbk
'''
import gevent
from beedrones.vsphere.client import VsphereManager
import json
import unittest
import random
from pyVmomi import vim
from beedrones.tests.test_util import BeedronesTestCase, runtest

contid = 14
component = u'NSX'

class VsphereClientTestCase(BeedronesTestCase):
    """
    """
    def setUp(self):
        BeedronesTestCase.setUp(self)

        '''
        # test vcloud
        vcenter = {'host':'vc-tstvcloud.vfarm.csi.it', 'port':443, 
                   'user':'administrator@vsphere.local', 
                   'pwd':'Admin$01', 'verified':False}
        nsx = None
        
        # test vpshere6.5
        vcenter = {'host':'vm-vcenter-to.vfarm.csi.it', 'port':443, 
                   'user':'01353adm@admin.csi.it', 
                   'pwd':'xxxxx', 'verified':False}
        nsx = None
        '''
        env = u'tstsddc'
        params = self.platform.get(u'vsphere').get(env)
        self.util = VsphereManager(params.get(u'vcenter', None), 
                                   params.get(u'nsxmanager', None))
        
    def tearDown(self):
        BeedronesTestCase.tearDown(self)
    
    def wait_task(self, task):
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            self.logger.info(task.info.state)
            gevent.sleep(1)
            
        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.info("Error: %s" % task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.info("Completed")
    
    #
    # system nsx
    #
    def test_nsx_global_info(self):
        res = self.util.system.nsx.global_info()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_summary_info(self):
        res = self.util.system.nsx.summary_info()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_reboot_appliance(self):
        res = self.util.system.nsx.reboot_appliance()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_cpu(self):
        res = self.util.system.nsx.query_appliance_cpu()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_uptime(self):
        res = self.util.system.nsx.query_appliance_uptime()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_memory(self):
        res = self.util.system.nsx.query_appliance_memory()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_storage(self):
        res = self.util.system.nsx.query_appliance_storage()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_network(self):
        res = self.util.system.nsx.query_appliance_network()
        self.logger.info(self.pp.pformat(res))    
    

    def test_nsx_configure_appliance_dns(self):
        res = self.util.system.nsx.configure_appliance_dns()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_delete_appliance_dns(self):
        res = self.util.system.nsx.delete_appliance_dns()
        self.logger.info(self.pp.pformat(res))    
    

    def test_nsx_query_appliance_time_settings(self):
        res = self.util.system.nsx.query_appliance_time_settings()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_configure_appliance_time_settings(self):
        res = self.util.system.nsx.configure_appliance_time_settings()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_delete_appliance_time_settings(self):
        res = self.util.system.nsx.delete_appliance_time_settings()
        self.logger.info(self.pp.pformat(res))    
    

    def test_nsx_query_appliance_local(self):
        res = self.util.system.nsx.query_appliance_local()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_configure_appliance_local(self):
        res = self.util.system.nsx.configure_appliance_local()
        self.logger.info(self.pp.pformat(res))    
    

    def test_nsx_query_appliance_syslog(self):
        res = self.util.system.nsx.query_appliance_syslog()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_configure_appliance_syslog(self):
        res = self.util.system.nsx.configure_appliance_syslog()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_delete_appliance_syslog(self):
        res = self.util.system.nsx.delete_appliance_syslog()
        self.logger.info(self.pp.pformat(res))    
    

    def test_nsx_components_summary(self):
        res = self.util.system.nsx.components_summary()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_components(self):
        res = self.util.system.nsx.query_appliance_components()
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_component(self):
        res = self.util.system.nsx.query_appliance_component(component)
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_component_dependency(self):
        res = self.util.system.nsx.query_appliance_component_dependency(component)
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_query_appliance_component_status(self):
        res = self.util.system.nsx.query_appliance_component_status(component)
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_toggle_appliance_component_status(self):
        res = self.util.system.nsx.toggle_appliance_component_status(component)
        self.logger.info(self.pp.pformat(res))    
    
    def test_nsx_restart_appliance_webapp(self):
        res = self.util.system.nsx.restart_appliance_webapp()
        self.logger.info(self.pp.pformat(res))    
    

    def test_nsx_get_system_events(self):
        res = self.util.system.nsx.get_system_events(page_size=5)
        self.logger.info(self.pp.pformat(res))
        print(type(res))
        #self.logger.info(json.dumps(res))
    
    def test_nsx_get_system_audit_logs(self):
        res = self.util.system.nsx.get_system_audit_logs()
        self.logger.info(self.pp.pformat(res))    
    
    #
    def test_get_nsx_transport_zones(self):
        res = self.util.system.nsx.list_transport_zones()
        self.logger.info(json.dumps(res, indent=4))
    
    #
    # nsx controller
    #
    def test_list_controllers(self):
        res = self.util.system.nsx.list_controllers()
        self.logger.info(json.dumps(res, indent=4))        
    
    #
    # network
    #        
    def test_list_distributed_virtual_switches(self):
        res = self.util.network.list_distributed_virtual_switches()
        self.logger.info(self.pp.pformat(res))
    
    def test_get_distributed_virtual_switch(self):
        res = self.util.network.get_distributed_virtual_switch('dvs-25')
        #res = self.util.network.get_distributed_virtual_switch('dvs-74')
        self.logger.info(self.pp.pformat(res))
        self.logger.info(self.util.network.detail_distributed_virtual_switch(res))
        
    def test_list_networks(self):
        res = self.util.network.list_networks()
        self.logger.info(self.pp.pformat(res))
        
    def test_get_network(self):
        network = self.util.network.get_network('dvportgroup-127')
        info = self.util.network.detail_network(network)
        self.logger.info(self.pp.pformat(info))
    
    def test_get_network_servers(self):
        servers = self.util.network.get_network_servers('dvportgroup-127')
        self.logger.info(self.pp.pformat(servers))
    
    def test_create_network(self):
        name = 'L-dvpg-567_DCCTP-tst-FE-Rupar'
        desc= name
        vlan = 567
        dvs = self.util.network.get_distributed_virtual_switch('dvs-74')
        numports = 24
        res = self.util.network.create_distributed_port_group(name, desc, 
                                                              vlan, dvs, 
                                                              numports)
        self.logger.info(res)
        
    def test_delete_network(self):
        oid = 'dvportgroup-813'
        network = self.util.network.get_network(oid)
        res = self.util.network.remove_network(network)
        self.logger.info(res)
    
    #
    # network nsx logical switch
    #    
    def test_nsx_list_logical_switches(self):
        res = self.util.network.nsx.lg.list()
        #self.logger.info(json.dumps(res, indent=4))
        for item in res:
            print "\n %s  - %s" % (item['name'], item['objectId'])
    
    def test_nsx_list_logical_switch(self):
        res = self.util.network.nsx.ls.get('virtualwire-1')
        #self.logger.info(self.util.network.nsx.info_logical_switch(res))
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_create_logical_switch(self):
        scope_id = 'vdnscope-1'
        name = 'prova_net-intermedia_by_API'
        desc = name
        res = self.util.network.nsx.lg.create(scope_id, name, desc)
        self.logger.info(json.dumps(res, indent=4))
        #job = self.util.query_nsx_job(jobid)
        
    def test_nsx_delete_logical_switch(self):
        oid = 'virtualwire-6'
        res = self.util.network.nsx.lg.delete(oid)
        self.logger.info(json.dumps(res, indent=4))          
    
    #
    # network nsx security group
    #        
    def test_nsx_list_security_group(self):
        res = self.util.network.nsx.sg.list()
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_list_security_group_by_server(self):
        res = self.util.network.nsx.sg.list_by_server('vm-150')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_get_security_group(self):
        res = self.util.network.nsx.sg.get('securitygroup-139')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        print res['objectId']
        print self.util.network.nsx.sg.info(res)
        self.logger.info(json.dumps(res, indent=4))        
        
    def test_nsx_get_allowed_member_type(self):
        res = self.util.network.nsx.sg.get_allowed_member_type('securitygroup-139')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_update_security_group(self):
        res = self.util.network.nsx.sg.update('securitygroup-30')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_security_group_add_member(self):
        res = self.util.network.nsx.sg.add_member('securitygroup-139', 'ipset-2')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_security_group_delete_member(self):
        res = self.util.network.nsx.sg.delete_member('securitygroup-139', 'ipset-2')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_security_group_create(self):
        res = self.util.network.nsx.sg.create('prova')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_security_group_delete(self):
        res = self.util.network.nsx.sg.delete('securitygroup-39')
        #self.logger.info(self.pp.pformat(res))
        #info = self.util.network.nsx.print_logicalswitch(res)
        self.logger.info(json.dumps(res, indent=4))

    #
    # network nsx ipset
    #        
    def test_nsx_list_ipset(self):
        res = self.util.network.nsx.ipset.list()
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_get_ipset(self):
        res = self.util.network.nsx.ipset.get('ipset-2')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_create_ipset(self):
        res = self.util.network.nsx.ipset.create('Miko_prova-ipset_by_API',
                                                 '09/03/2017 Descr di Miko_prova-ipset_by_API',
                                                 '158.102.160.50/32,158.102.160.215/32')
        self.logger.info(json.dumps(res, indent=4))

    def test_nsx_update_ipset(self):
        res = self.util.network.nsx.ipset.update('ipset-3',None,None,'158.102.160.0/24')
        self.logger.info(json.dumps(res, indent=4))
    
    
    
    
    def test_nsx_delete_ipset(self):
        res = self.util.network.nsx.ipset.delete('ipset-2')
        self.logger.info(json.dumps(res, indent=4))

    #
    # network nsx service
    #        
    def test_nsx_list_service(self):
        res = self.util.network.nsx.service.list()
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_get_service(self):
        res = self.util.network.nsx.service.get('TCP', '8080')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_create_service(self):
        protocol = 'TCP'
        ports = '4000-4001'
        name = 'tcp-4000'
        desc = 'tcp 4000-4001'
        res = self.util.network.nsx.service.create(protocol, ports, name, desc)
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_delete_service(self):
        res = self.util.network.nsx.service.delete('application-371')
        self.logger.info(json.dumps(res, indent=4))


    #
    # network nsx LB ( load balancing )
    #        
    def test_nsx_lb_get_config (self):
        res = self.util.network.nsx.lb.get_config('edge-57')
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_lb_enable_true(self):
        res=self.util.network.nsx.lb.update_global_config('edge-57',edgeLogging='true',edgeLogLevel='warning',
                              accelerationEnabled='true')
        self.logger.info(json.dumps(res, indent=4))

    def test_nsx_lb_enable_false(self):
        res=self.util.network.nsx.lb.update_global_config('edge-57',enable='False')
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_lb_list_app_profile(self):
        res=self.util.network.nsx.lb.list_app_profile('edge-57')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_lb_get_app_profiles(self):
        res=self.util.network.nsx.lb.get_app_profile('edge-57','applicationProfile-19')
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_lb_add_app_profile(self):
        
        '''
        ## HTTP ##
        # test persistence NONE
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTP', 'httpt_by_api_NONE')
        
        # test persistence COOKIE        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTP', 'httpt_by_api_cookie',
                                                     persistence='cookie',expire=120,cookiename='MyCookie',cookiemode='insert')
        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTP', 'http_by_api_cookie_prefix',
                                                     persistence='cookie',expire=120,cookiename='myName2',cookiemode='prefix')
         
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTP', 'http_by_api_cookie_AppSession',
                                                     persistence='cookie',expire=120,cookiename='myName2',cookiemode='app')
        
        # test persistence Source IP        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTP', 'http_by_api_SourceIP',
                                                     persistence='sourceip',expire=120)
        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTP', 'http_by_api_SourceIP_noexp',
                                                     persistence='sourceip')
        
        ## HTTPS ##
        # test persistence NONE
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTPS', 'https_by_api_NONE',sslPassthrough='true')
         
        # test persistence Source IP        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTPS', 'https_by_api_SourceIP',sslPassthrough='true',
                                                     persistence='sourceip',expire=120)
            #### no expire ####        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTPS', 'https_by_api_SourceIP_noexp',sslPassthrough='true',
                                                     persistence='sourceip')

        # test persistence SSl session ID
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTPS', 'https_by_api_SSL_sessionID',sslPassthrough='true',
                                                     persistence='ssl_sessionid',expire=120)
            #### no expire ####
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'HTTPS', 'https_by_api_SSL_sessionID_noexp',sslPassthrough='true',
                                                     persistence='ssl_sessionid')
        
        
        
        '''
        
        res=self.util.network.nsx.lb.add_app_profile('edge-57', 'TCP', 'msrdp_by_api',
                                                     persistence='msrdp',expire=120)
 
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_lb_update_app_profile(self):
        res= self.util.network.nsx.lb.update_app_profile('edge-57', 'applicationProfile-42',name="pluto e minnie",
                                                         persistence='sourceip',expire='2010')
        self.logger.info(json.dumps(res, indent=4))
    
    
    def test_nsx_lb_del_app_profile(self):
        res=self.util.network.nsx.lb.del_app_profile('edge-57', 'applicationProfile-39')
        self.logger.info(json.dumps(res, indent=4))

    def test_nsx_lb_del_all_app_profiles(self):
        res=self.util.network.nsx.lb.del_all_app_profiles('edge-57')
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_lb_list_pools(self):
        res=self.util.network.nsx.lb.list_pools('edge-57')
        self.logger.info(json.dumps(res, indent=4))


    def test_nsx_lb_get_pool(self):
        res=self.util.network.nsx.lb.get_pool('edge-57','pool-2')
        self.logger.info(json.dumps(res, indent=4))
        
        
    def test_nsx_lb_add_pool (self):
        res=self.util.network.nsx.lb.add_pool('edge-57', 'prova_by_api4', 
                                        'URl',algorithmParameters='urlParam=http://pippo.com')
        self.logger.info(json.dumps(res, indent=4))

    def test_nsx_lb_add_pool_member(self):
        res=self.util.network.nsx.lb.add_pool_member('edge-57','pool-2',
                                                     ipAddress='10.102.189.17',
                                                     monitorPort='80',
                                                     name='server3')
        self.logger.info(json.dumps(res, indent=4))

        
    def test_nsx_lb_delete_pool(self):
        res=self.util.network.nsx.lb.del_pool('edge-57', 'pool-26')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_lb_delete_all_pools(self):
        res=self.util.network.nsx.lb.del_all_pools('edge-57')
        self.logger.info(json.dumps(res, indent=4))
         
                
    def test_nsx_lb_list_virtual_servers(self):
        res=self.util.network.nsx.lb.list_virt_servers('edge-57')
        self.logger.info(json.dumps(res, indent=4))

    def test_nsx_lb_get_virtual_server(self):
        res=self.util.network.nsx.lb.get_virt_server('edge-57','virtualServer-4')
        self.logger.info(json.dumps(res, indent=4))
 
    
    def test_nsx_lb_delete(self):
        res=self.util.network.nsx.lb.delete('edge-57')
        self.logger.info(json.dumps(res, indent=4))
        
    
    #
    # network nsx dlr
    #    
    def test_nsx_list_all_dlr(self):
        res = self.util.network.nsx.dlr.list()
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_get_dlr(self):
        res = self.util.network.nsx.dlr.get('edge-10')
        print self.util.network.nsx.dlr.info(res)
        self.logger.info(json.dumps(res, indent=4))  
    
    def test_nsx_create_dlr(self):
        # by miko
        dictNewDlr= {'datacenterMoid':'datacenter-38',
                    'name':'NSX_Miko-API DLR',
                    'staticRouting':{'enabled':'true','vnic':'2','mtu':'1500','description':'Miko Gateway','gatewayAddress':'10.102.184.1'},  
                    'appliances':{'deployAppliances':'true','resourcePoolId':'domain-c54',
                                  'datastoreId':'datastore-93'},
                    'cliSettings':{'remoteAccess':'true','userName':'admin','password':'Applenumber!143'},
                    'mgmtInterface':{'connectedToId':'dvportgroup-82'},
                    'interfaces':{'interface':[{'name':'Uplink_miko_by_API','mtu':'1500','type':'uplink',
                                                 'connectedToId':'dvportgroup-82',
                                                 'primaryAddress':'10.102.184.40','subnetMask':'255.255.255.0','subnetPrefixLength':'24',
                                                 'isConnected':'true'},
                                               {'name':'internal_miko_by_API','mtu':'1500','type':'internal',
                                                 'connectedToId':'virtualwire-7',
                                                 'primaryAddress':'192.168.100.1','subnetMask':'255.255.255.0','subnetPrefixLength':'24',
                                                 'isConnected':'true'},
                                                {'name':'internal_miko_by_API2','mtu':'1500','type':'internal',
                                                 'connectedToId':'virtualwire-1',
                                                 'primaryAddress':'192.168.10.1','subnetMask':'255.255.255.0','subnetPrefixLength':'24',
                                                 'isConnected':'true'}
                                                ]}       
                    }
            
        res = self.util.network.nsx.dlr.create(dictNewDlr)
        self.logger.info(json.dumps(res, indent=4)) 
              
        
    #
    # network nsx edge
    #    
    
    def test_nsx_list_all_edge(self):
        res = self.util.network.nsx.edge.list()
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_get_edge(self):
        res = self.util.network.nsx.edge.get('edge-14')
        print self.util.network.nsx.edge.info(res)
        self.logger.info(json.dumps(res, indent=4))  

    def test_nsx_create_edge(self):
        
        dictNewEsg= {'datacenterMoid':'datacenter-38',
                    'name':'NSX_EDGE primo by miko',
                    'tenant':'Default',
                    'vseLogLevel':'emergency',
                    'staticRouting':{'enabled':'true','vnic':'0','mtu':'1500','description':'Miko Gateway','gatewayAddress':'10.102.184.1'},  
                    'appliances':{'applianceSize':'compact','resourcePoolId':'domain-c54','datastoreId':'datastore-93'},
                    'cliSettings':{'remoteAccess':'true','userName':'admin','password':'Applenumber!143'},
                    'vnics':{'vnic':[{'name':'Uplink_miko_by_API','mtu':'1500','type':'uplink',
                                                 'portgroupId':'dvportgroup-82',
                                                 'primaryAddress':'10.102.184.40','subnetPrefixLength':'24',
                                                 'enableProxyArp':'false',
                                                 'enableSendRedirects':'true',
                                                 'isConnected':'true'},
                                               {'name':'internal_miko_by_API','mtu':'1500','type':'internal',
                                                 'portgroupId':'virtualwire-7',
                                                 'primaryAddress':'192.168.100.1','subnetPrefixLength':'24',
                                                 'enableProxyArp':'false',
                                                 'enableSendRedirects':'true',                                                
                                                 'isConnected':'true'},
                                                {'name':'internal_miko_by_API2','mtu':'1500','type':'internal',
                                                 'portgroupId':'virtualwire-1',
                                                 'primaryAddress':'192.168.10.1','subnetPrefixLength':'24',
                                                 'enableProxyArp':'false',
                                                 'enableSendRedirects':'true',                                                
                                                 'isConnected':'true'}
                                                ]}       
                    }
            
        res = self.util.network.nsx.edge.create(dictNewEsg)
        self.logger.info(json.dumps(res, indent=4)) 
        
        
        

        
    def test_nsx_delete_edge(self):
        res = self.util.network.nsx.edge.delete('edge-6')
        #print self.util.network.nsx.edge.info(res)
        self.logger.info(json.dumps(res, indent=4))  
        
        
    #
    # network nsx dfw
    #
    def test_nsx_list_all_dfw_rules(self):
        res = self.util.network.nsx.dfw.get_config()
        #self.util.network.nsx.dfw.print_sections(res, print_rules=True, table=False)
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_get_sections(self):
        res = self.util.network.nsx.dfw.get_sections(rule_type=u'L3REDIRECT')
        self.logger.info(json.dumps(res, indent=2))
    
    def test_nsx_get_dfw_section(self):
        res = self.util.network.nsx.dfw.get_layer3_section(u'1009')
        self.util.network.nsx.dfw.print_section(res, table=False)
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_get_dfw_rule(self):
        res = self.util.network.nsx.dfw.get_rule(u'1031', u'133087')
        self.util.network.nsx.dfw.print_rule(res)
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_create_dfw_section(self):
        res = self.util.network.nsx.dfw.create_section('prova', action='allow', 
                                                       logged=False)
        self.logger.info(json.dumps(res, indent=4))
    
    def test_nsx_delete_dfw_section(self):
        res = self.util.network.nsx.dfw.delete_section('1027')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_create_dfw_rule(self):
        source = None
        destination = None
        service = [{u'port':u'*', u'protocol':u'*'}] # -> *:*
        #service = [{u'port':u'*', u'protocol':6}] # -> tcp:*
        #service = [{u'port':80, u'protocol':6}] # -> tcp:80
        #service = [{u'port':80, u'protocol':17}] # -> udp:80
        service = [{u'protocol':1, u'subprotocol':8}] # -> icmp:echo request
        appliedto = None
        res = self.util.network.nsx.dfw.create_rule('1009', 'prova', 
                                                    'allow', 'out', False, 
                                                    source, destination, 
                                                    service, appliedto)
        self.logger.info(json.dumps(res, indent=4))

    '''
    def test_nsx_create_dfw_rule_net_307_deny(self):
        source = None
        destination = [{'name':'CARBON_dvpg-307_mgmt', 
                        'value':'dvportgroup-128', 
                        'type':'DistributedVirtualPortgroup'}]
        appliedto = [{'name':'DISTRIBUTED_FIREWALL', 
                      'value':'DISTRIBUTED_FIREWALL', 
                      'type':'DISTRIBUTED_FIREWALL'}]
        service = None
        res = self.util.network.nsx.dfw.create_rule('1022', 'disable-vlan-307', 
                                                    'deny', 'inout', 'false', 
                                                    source, destination, 
                                                    service, appliedto)
        self.logger.info(res)'''

    def test_nsx_create_dfw_rule_deny_isolotti(self):
        source = [{'name':None, 
                   'value':'securitygroup-1120', 
                   'type':'SecurityGroup'}]
        destination = [{'name':None, 
                        'value':'securitygroup-1120', 
                        'type':'SecurityGroup'}]
        #source = None
        #destination = None
        appliedto = [{'name':None,
                      'value':'securitygroup-1120', 
                      'type':'SecurityGroup'}]
        service = None
        res = self.util.network.nsx.dfw.create_rule('1028', 'deny_csi', 
                                                    'deny', 'in', False, 
                                                    source, destination, 
                                                    service, appliedto)
        self.logger.info(json.dumps(res, indent=4))

    def test_nsx_create_dfw_rule_158(self):
        source = [{'name':None, 
                   'value':'158.102.160.0/24', 
                   'type':'Ipv4Address'}]
        destination = [{'name':'ISOLOTTI', 
                        'value':'securitygroup-29', 
                        'type':'SecurityGroup'}]
        appliedto = [{'name':'ISOLOTTI', 
                      'value':'securitygroup-29', 
                      'type':'SecurityGroup'}]
        service = None
        res = self.util.network.nsx.dfw.create_rule('1022', 'enable-158', 
                                                    'allow', 'inout', False, 
                                                    source, destination, 
                                                    service, appliedto)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_create_dfw_rule_allow_demo(self):
        source = [{'name':'DEMO', 
                   'value':'securitygroup-30', 
                   'type':'SecurityGroup'}]
        destination = [{'name':'DEMO', 
                        'value':'securitygroup-30', 
                        'type':'SecurityGroup'}]
        appliedto = [{'name':'DEMO', 
                      'value':'securitygroup-30', 
                      'type':'SecurityGroup'}]
        service = None
        res = self.util.network.nsx.dfw.create_rule('1022', 'allow_demo', 
                                                    'allow', 'inout', False, 
                                                    source, destination, 
                                                    service, appliedto)
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_update_dfw_rule(self):
        res = self.util.network.nsx.dfw.update_rule('1022', '133065')
        #new_action='allow')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_move_dfw_rule(self):
        res = self.util.network.nsx.dfw.move_rule('1022', '133065', 
                                                  ruleafter='133067')
        self.logger.info(json.dumps(res, indent=4))      

    def test_nsx_delete_dfw_rule(self):
        res = self.util.network.nsx.dfw.delete_rule('1027', '133075')
        self.logger.info(json.dumps(res, indent=4))
        
    def test_nsx_get_exclusion_list(self):
        res = self.util.network.nsx.dfw.get_exclusion_list()
        self.logger.info(json.dumps(res, indent=4))
    
    
    #
    # vsphere manager
    #  
    def test_ping_vsphere(self):
        res = self.util.system.ping_vsphere()
        self.logger.info(res)
        
    def test_ping_nsx(self):
        res = self.util.system.ping_nsx()
        self.logger.info(res)        
    
    #
    # virtual app
    #  
    def test_list_virtualapp(self):
        vms = self.util.vapp.list()
        for vm in vms:
            self.logger.info(vm)
            
    def test_get_virtualapp(self):
        server = self.util.vapp.get_by_morid('vm-533')
        info = self.util.vapp.info(server)
        self.logger.info(self.pp.pformat(info))    
    
    #
    # server
    #  
    def test_list_servers(self):
        vms = self.util.server.list(template=False)
        self.logger.info(self.pp.pformat(vms))
        for vm in vms:
            self.logger.info(self.pp.pformat(self.util.server.info(vm)))
            
    def test_get_server(self):
        server = self.util.server.get_by_morid('vm-205')
        info = self.util.server.detail(server)
        self.logger.info(self.pp.pformat(info))
        
    def test_get_server_hardware(self):
        server = self.util.server.get_by_morid('vm-150')
        info = self.util.server.hardware.info(server)
        self.logger.info(self.pp.pformat(info))
        
    def test_get_server_devices(self):
        server = self.util.server.get_by_morid('vm-150')
        info = self.util.server.hardware.get_devices(server,
                                                     dev_type=u'vim.vm.device.VirtualVmxnet3')
        self.logger.info(self.pp.pformat(info))        
        
    def test_get_server_guest_info(self):
        server = self.util.server.get_by_morid('vm-40')
        info = self.util.server.guest_info(server)
        self.logger.info(self.pp.pformat(info))
    
    def test_get_server_runtime(self):
        server = self.util.server.get_by_morid('vm-205')
        info = self.util.server.runtime(server)
        self.logger.info(self.pp.pformat(info))   
        
    def test_get_server_usage(self):
        server = self.util.server.get_by_morid('vm-4')
        info = self.util.server.usage(server)
        self.logger.info(self.pp.pformat(info))
    
    def test_assign_server_tag(self):
        server = self.util.server.get_by_morid('vm-150')
        info = self.util.server.assign_tag(server, 'tag1')
        self.logger.info(self.pp.pformat(info))      
    
    def test_get_server_tags(self):
        server = self.util.server.get_by_morid('vm-150')
        info = self.util.server.get_tags(server)
        self.logger.info(self.pp.pformat(info))
        
    def test_get_server_permissions(self):
        server = self.util.server.get_by_morid('vm-150')
        info = self.util.server.permissions(server)
        self.logger.info(self.pp.pformat(info))          
    
    def test_get_server_remote_console(self):
        server = self.util.server.get_by_morid('vm-1163')
        info = self.util.server.remote_console(server)
        self.logger.info(self.pp.pformat(info))
        
    def test_get_server_security_groups(self):
        server = self.util.server.get_by_morid('vm-150')
        info = self.util.server.security_groups(server)
        self.logger.info(self.pp.pformat(info))
    
    def test_get_server_by_dnsname(self):
        name = 'nsx-controller'
        vm = self.util.server.get_by_dnsname(name)
        self.logger.info(vm._moId)
        
    def test_get_server_by_ip(self):
        name = '172.25.5.5'
        vm = self.util.server.get_by_ip(name)
        self.logger.info(vm._moId)
        
    def test_get_server_network(self):
        server = self.util.server.get_by_morid('vm-150')
        net = self.util.server.network(server)
        self.logger.info(net)        
    
    def test_start_server(self):
        server = self.util.server.get_by_morid('vm-1220')
        task = self.util.server.start(server)        

        while True:
            tools_status = server.guest.toolsRunningStatus
            print tools_status
            gevent.sleep(1)
            
    
    #
    # server guest
    #
    def test_server_guest_list_process(self):
        server = self.util.server.get_by_morid('vm-205')
        res = self.util.server.guest_list_process(server, 'root', 'Admin$01')
        #server = self.util.server.get_by_morid('vm-25')
        #res = self.util.server.guest_list_process(server, 
        #                                          'administrator', 
        #                                          'Admin$01')
        self.logger.info(res)
        for i in res:
            print "%s %s %s %s %s %s %s" % (i.pid, i.name, i.owner, i.cmdLine, i.startTime, i.endTime, i.exitCode)

    def test_server_guest_execute_command(self):
        ip = u'172.25.5.154'
        nm = u'255.255.255.0'
        gw = u'172.25.5.18'
        cmd = u'-e "TYPE=Ethernet\nBOOTPROTO=static\nIPV6INIT=no\nDEVICE=eth0\nONBOOT=yes\nIPADDR=%s\nNETMASK=%s\nGATEWAY=%s" > /etc/sysconfig/network-scripts/ifcfg-eth0' % (ip, nm, gw)
        server = self.util.server.get_by_morid('vm-1220')
        proc = self.util.server.guest_execute_command(server, 'root', 'Admin$01', 
                                                      path_to_program='/bin/echo', 
                                                      program_arguments=cmd)
        res = self.util.server.guest_list_process(server, 'root', 'Admin$01', 
                                                  pids=[int(proc)])
        self.logger.info(res)
        proc = self.util.server.guest_execute_command(server, 'root', 'Admin$01', 
                                                      path_to_program='/bin/systemctl', 
                                                      program_arguments='restart network')        
        res = self.util.server.guest_list_process(server, 'root', 'Admin$01', 
                                                  pids=[int(proc)])
        self.logger.info(res)
        #time.sleep(2)
        #res = self.util.server.guest_list_process(server, 'root', 'Admin$01', 
        #                                          pids=[int(proc)])
        #self.logger.info(res)
    
    def test_server_guest_read_environment_variable(self):
        server = self.util.server.get_by_morid('vm-205')
        res = self.util.server.guest_read_environment_variable(server, 'root', 'Admin$01')
        self.logger.info(res)
    
    def test_server_guest_setup_network(self):
        ip = u'172.25.5.154'
        nm = u'255.255.255.0'
        gw = u'172.25.5.18'
        hostname = u'prova1'
        server = self.util.server.get_by_morid('vm-1225')
        res = self.util.server.guest_setup_network(server, 'root', 'Admin$01', 
                                                   ip, nm, gw, hostname)
        self.logger.info(res)
    
    # server create, delete
    #
    def test_create_server(self):
        name = 'vm-provaMikoOld-PythonAPI'
        guest_id = 'windows9Server64Guest'
        folder = self.util.folder.get('group-v3')
        datastore = self.util.datastore.get('datastore-48').name        
        resource_pool = self.util.cluster.resource_pool.get('resgroup-42')
        network=self.util.network.get_network('dvportgroup-66') # by miko
        task = self.util.server.create(name, guest_id, resource_pool, datastore, 
                                       folder, network, memory_mb=2048, cpu=2, 
                                       core_x_socket=1, disk_size_gb=40, 
                                       version='vmx-13')
        self.wait_task(task)
    
    def test_create_linked_clone(self):
        server = self.util.server.get_by_morid('vm-150')
        name = u'prova-vm-%s' % random.randint(1, 100000)
        folder = self.util.folder.get('group-v3')
        datastore = self.util.datastore.get('datastore-10')
        resource_pool = self.util.cluster.resource_pool.get('resgroup-45')
        self.logger.info('Attempt to create vm %s' % name)
        task = self.util.server.create_linked_clone(server, name, folder, 
                                                    datastore, resource_pool,
                                                    power_on=False)
        self.wait_task(task)    
    
    def test_create_from_template(self):
        template = self.util.server.get_by_morid('vm-215')
        name = 'prova-125'
        folder = self.util.folder.get('group-v3')
        datastore = self.util.datastore.get('datastore-10')
        resource_pool = self.util.cluster.resource_pool.get('resgroup-45')
        task = self.util.server.create_from_template(template, name, folder, 
                                                     datastore, resource_pool)
        self.wait_task(task)
        
    def test_update_server(self):
        server = self.util.server.get_by_morid('vm-232')
        task = self.util.server.update(server, 'cippalippa1', 'notes')
        self.wait_task(task)
        
    def test_remove_server(self):
        server = self.util.server.get_by_morid('vm-1181')
        task = self.util.server.remove(server)
        self.wait_task(task)        
    
    # server hw
    #
    def test_add_server_disk(self):
        server = self.util.server.get_by_morid('vm-533')
        disk_size = 10
        task = self.util.server.hardware.add_hard_disk(server, disk_size, 
                                                       disk_type='thin', 
                                                       existing=False)  
        self.wait_task(task)        
      
    def test_remove_server_disk(self):
        server = self.util.server.get_by_morid('vm-533')
        task = self.util.server.hardware.delete_hard_disk(server, 2)
        self.wait_task(task)       
      
    def test_add_server_network(self):
        server = self.util.server.get_by_morid('vm-533')
        network = self.util.network.get_network('dvportgroup-156')
        task = self.util.server.hardware.add_network(server, network)
        self.wait_task(task)        
    
    def test_update_server_network(self):
        server = self.util.server.get_by_morid('vm-533')
        network = self.util.network.get_network('dvportgroup-156')
        net_number = 1
        task = self.util.server.hardware.update_network(server, net_number, 
                                                        connect=True, network=None)
        self.wait_task(task)
    
    def test_remove_server_network(self):
        server = self.util.server.get_by_morid('vm-533')
        task = self.util.server.hardware.delete_network(server, 2)
        self.wait_task(task)
        
    def test_update_server_cdrom(self):
        server = self.util.server.get_by_morid('vm-150')
        full_path_to_iso = "[DatastoreNFS-ISO] virtio-win-0.1.102.iso"
        full_path_to_iso = ""
        cdrom_number = 1
        task = self.util.server.hardware.update_cdrom(server, cdrom_number, 
                                                      full_path_to_iso)
        self.wait_task(task)        
    
    #
    # server snapshot
    #
    def test_list_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-205')
        res = self.util.server.snapshot.list(server)
        self.logger.info(self.pp.pformat(res))
    
    def test_get_current_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-150')
        res = self.util.server.snapshot.get_current(server)
        self.logger.info(self.pp.pformat(res))        
    
    def test_get_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-150')
        res = self.util.server.snapshot.get(server, 'snapshot-1184')
        self.logger.info(self.pp.pformat(res))       
    
    def test_take_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-150')
        name = 'for_linked_clone'
        desc = 'for_linked_clone' 
        memory = False
        quiesce = False
        task = self.util.server.snapshot.take(server, name, desc, memory, quiesce)
        self.wait_task(task)

    def test_rename_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-205')
        self.util.server.snapshot.rename(server, 'snapshot-1187', 'snap-0000')
        
    def test_revert_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-205')
        task = self.util.server.snapshot.revert(server, 'snapshot-1187')
        self.wait_task(task)          
        
    def test_delete_server_snapshot(self):
        server = self.util.server.get_by_morid('vm-150')
        task = self.util.server.snapshot.remove(server, 'snapshot-1184')
        self.wait_task(task)        
        
    #
    # datacenter
    #  
    def test_list_datacenters(self):
        dcs = self.util.datacenter.list()
        for dc in dcs:
            self.logger.info(dc)
            
    def test_get_datacenter(self):
        dc = self.util.datacenter.get('datacenter-2')
        info = self.util.datacenter.info(dc)
        self.logger.info(self.pp.pformat(info))
    
    #
    # folder
    #  
    def test_list_folders(self):
        folders = self.util.folder.list()
        for folder in folders:
            self.logger.info(folder)
            
    def test_get_folder(self):
        folder = self.util.folder.get('group-v3')
        info = self.util.folder.info(folder)
        self.logger.info(self.pp.pformat(info))
    
    def test_create_folder(self):
        #folder = self.util.folder.get('group-v3')
        #folder = self.util.folder.create('prova', folder)
        datacenter = self.util.datacenter.get('datacenter-2')
        folder = self.util.folder.create('prova', datacenter=datacenter, host=True)
        self.logger.info(folder._moId) 
    
    def test_update_folder(self):
        folder = self.util.folder.get('group-v519')
        task = self.util.folder.update(folder, 'prova1')
        self.wait_task(task)
        
    def test_remove_folder(self):
        folder = self.util.folder.get('group-h532')
        task = self.util.folder.remove(folder)
        self.wait_task(task)
    
    #
    # datastore
    #  
    def test_list_datastores(self):
        vms = self.util.datastore.list()
        for vm in vms:
            self.logger.info(vm)
            
    def test_get_datastore(self):
        ds = self.util.datastore.get('datastore-10')
        info = self.util.datastore.detail(ds)
        self.logger.info(self.pp.pformat(info))
        
    def test_get_datastore_servers(self):
        ds = self.util.datastore.get('datastore-10')
        info = self.util.datastore.get_servers(ds)
        self.logger.info(self.pp.pformat(info))
        
    def test_get_datastore_hosts(self):
        ds = self.util.datastore.get('datastore-10')
        info = self.util.datastore.get_hosts(ds)
        self.logger.info(self.pp.pformat(info))
        
    def test_browse_datastore_files(self):
        ds = self.util.datastore.get('datastore-10')
        task = self.util.datastore.browse_files(ds, path='ISO')
        self.wait_task(task)
        files = task.info.result
        info = self.util.datastore.parse_files(files)
        self.logger.info(self.pp.pformat(info))
        
    #
    # cluster
    #  
    def test_list_clusters(self):
        clus = self.util.cluster.list()
        for clu in clus:
            self.logger.info(clu)
            
    def test_get_cluster(self):
        clu = self.util.cluster.get('domain-c44')
        self.logger.info(clu._moId)
        self.logger.info(clu.resourcePool.resourcePool)
        
    def test_list_hosts(self):
        hs = self.util.cluster.host.list()
        for h in hs:
            self.logger.info(h)
            
    def test_get_host(self):
        h = self.util.cluster.host.get('host-87')
        self.logger.info(h)
        
    def test_list_resource_pools(self):
        rps = self.util.cluster.resource_pool.list()
        for rp in rps:
            self.logger.info(rp)
            
    def test_get_resource_pool(self):
        rp = self.util.cluster.resource_pool.get('resgroup-710')
        self.logger.info(self.util.cluster.resource_pool.detail(rp))
        
    def test_get_resource_pool_servers(self):
        servers = self.util.cluster.resource_pool.get_servers('resgroup-45')
        self.logger.info(servers)
        
    def test_create_resource_pool(self):
        cluster = self.util.cluster.get('domain-c44')
        name = 'prova-respool-01'
        cpu = 4000
        memory = 10240
        shares = 'normal'
        res = self.util.cluster.resource_pool.create(cluster, name, cpu, 
                                                     memory, shares)
        self.logger.info(res)             
    
    def test_update_resource_pool(self):
        respool = self.util.cluster.resource_pool.get('resgroup-710')
        name = 'prova-respool-02'
        cpu = 4000
        memory = 10240
        shares = 'normal'
        res = self.util.cluster.resource_pool.update(respool, name, cpu, 
                                                     memory, shares)
        self.logger.info(res)
    
    def test_delete_resource_pool(self):
        respool = self.util.cluster.resource_pool.get('resgroup-711')
        res = self.util.cluster.resource_pool.remove(respool)
        self.logger.info(res)    

def test_suite():
    tests = [
        # system
        'test_ping_vsphere',
        #'test_ping_nsx',
        
        # datacenter
        #'test_list_datacenters',
        #'test_get_datacenter',
        
        # folder
        #'test_list_folders',
        #'test_get_folder',
        #'test_create_folder',
        #'test_update_folder',
        #'test_remove_folder',
        
        # virtual app
        #'test_list_virtualapp',
        #'test_get_virtualapp',
        
        # server
        #'test_list_servers',
        #'test_get_server',
        #'test_get_server_hardware',
        #'test_get_server_devices',
        #'test_get_server_guest_info',
        #'test_get_server_runtime',
        #'test_get_server_usage',
        #'test_assign_server_tag',
        #'test_get_server_tags',
        #'test_get_server_permissions',
        #'test_get_server_remote_console',
        #'test_get_server_security_groups',
        #'test_get_server_by_dnsname',
        #'test_get_server_by_ip',
        #'test_get_server_network',
        #'test_start_server',
        
        # server guest
        #
        #'test_server_guest_list_process',
        #'test_server_guest_execute_command',
        #'test_server_guest_read_environment_variable',
        #'test_server_guest_setup_network',
        
        # server create, delete
        #'test_create_server',
        #'test_create_linked_clone'
        #'test_create_from_template',
        #'test_update_server',
        #'test_remove_server',
        
        # server hw
        #'test_add_server_disk',
        #'test_remove_server_disk',
        #'test_add_server_network',
        #'test_update_server_network',
        #'test_remove_server_network',
        #'test_update_server_cdrom',
        
        # sever snapshot
        #'test_list_server_snapshot',
        #'test_get_current_server_snapshot',
        #'test_get_server_snapshot',
        #'test_take_server_snapshot',
        ##'test_rename_server_snapshot',
        ##'test_revert_server_snapshot',
        #'test_delete_server_snapshot',
        
        # network
        #'test_list_distributed_virtual_switches',
        #'test_get_distributed_virtual_switch',
        #'test_list_networks',
        #'test_get_network',
        #'test_get_network_servers',
        #'test_create_network',
        #'test_delete_network',
        
        # nsx manager
        #
        #'test_nsx_global_info',
        #'test_nsx_summary_info',
        
        #'test_nsx_reboot_appliance',
        #'test_nsx_query_appliance_cpu',
        #'test_nsx_query_appliance_uptime',
        #'test_nsx_query_appliance_memory',
        #'test_nsx_query_appliance_storage',
        #'test_nsx_query_appliance_network',
        
        #'test_nsx_configure_appliance_dns',
        #'test_nsx_delete_appliance_dns',
        
        #'test_nsx_query_appliance_time_settings',
        #'test_nsx_configure_appliance_time_settings',
        #'test_nsx_delete_appliance_time_settings',
        
        #'test_nsx_query_appliance_local',
        #'test_nsx_configure_appliance_local',
        
        #'test_nsx_query_appliance_syslog',
        #'test_nsx_configure_appliance_syslog',
        #'test_nsx_delete_appliance_syslog',
        
        #'test_nsx_components_summary',
        #'test_nsx_query_appliance_components',
        #'test_nsx_query_appliance_component',
        #'test_nsx_query_appliance_component_dependency',
        #'test_nsx_query_appliance_component_status',
        #'test_nsx_toggle_appliance_component_status',
        #'test_nsx_restart_appliance_webapp',
        
        #'test_nsx_get_system_events',
        #'test_nsx_get_system_audit_logs',
        
        #'test_get_nsx_transport_zones',             
        #'test_list_controllers',
        
        # network nsx
        #
        #'test_nsx_list_logical_switches',
        #'test_nsx_list_logical_switch',
        #'test_nsx_create_logical_switch',
        #'test_nsx_delete_logical_switch',
        
        # network nsx security group
        #
        #'test_nsx_list_security_group',
        #'test_nsx_list_security_group_by_server',
        #'test_nsx_get_security_group',
        #'test_nsx_get_allowed_member_type',
        #'test_nsx_security_group_add_member',
        #'test_nsx_security_group_delete_member',
        #'test_nsx_update_security_group',  
        #'test_nsx_security_group_create',
        #'test_nsx_security_group_delete',
        
        # network nsx ipset
        #
        #'test_nsx_create_ipset',
        #'test_nsx_list_ipset',
        #'test_nsx_get_ipset',  
        #'test_nsx_update_ipset',           
        #'test_nsx_delete_ipset',
        
        # network nsx service
        #
        #'test_nsx_create_service',
        #'test_nsx_list_service',
        #'test_nsx_get_service',             
        #'test_nsx_delete_service',             
        
        # network nsx dfw
        #
        #'test_nsx_list_all_dfw_rules',
        #'test_nsx_get_sections',
        #'test_nsx_get_dfw_section',
        #'test_nsx_get_dfw_rule',
        #'test_nsx_create_dfw_section',
        #'test_nsx_delete_dfw_section',
        #'test_nsx_create_dfw_rule',
        #'test_nsx_create_dfw_rule_deny_isolotti',
        #'test_nsx_create_dfw_rule_158',
        #'test_nsx_create_dfw_rule_allow_demo',
        #'test_nsx_update_dfw_rule',
        #'test_nsx_move_dfw_rule',
        #'test_nsx_delete_dfw_rule',             
        
        #'test_nsx_get_exclusion_list',
        
        # network nsx dlr
        #
        #'test_nsx_list_all_dlr',
        #'test_nsx_get_dlr',
        #'test_nsx_create_dlr',
        
        # network nsx edge
        #
        #'test_nsx_list_all_edge',
        #'test_nsx_get_edge',
        #'test_nsx_create_edge',
        #'test_nsx_delete_edge',
        
        # network nsx LB ( load balancing )
        #
        #'test_nsx_lb_get_config',
        #'test_nsx_lb_enable_true',
        #'test_nsx_lb_enable_false',
        #'test_nsx_lb_list_app_profile',
        #'test_nsx_lb_get_app_profiles',
        #'test_nsx_lb_add_app_profile',
        #'test_nsx_lb_update_app_profile',
        #'test_nsx_lb_del_app_profile',
        #'test_nsx_lb_configure',
        #'test_nsx_lb_del_all_app_profiles',
        #'test_nsx_lb_list_pools',
        #'test_nsx_lb_get_pool',
        #'test_nsx_lb_add_pool',
        #'test_nsx_lb_add_pool_member',
        #'test_nsx_lb_delete_pool',
        #'test_nsx_lb_delete_all_pools',
        #'test_nsx_lb_list_virtual_servers',
        #'test_nsx_lb_get_virtual_server'
        #'test_nsx_lb_delete',
        
        
        # cluster
        #'test_list_clusters',
        #'test_get_cluster',
        #'test_list_hosts',
        #'test_get_host',
        #'test_list_resource_pools',
        #'test_get_resource_pool',
        #'test_get_resource_pool_servers',
        #'test_create_resource_pool',
        #'test_update_resource_pool',
        #'test_delete_resource_pool',             
        
        # datastore
        #'test_list_datastores',
        #'test_get_datastore',
        #'test_get_datastore_servers',
        #'test_get_datastore_hosts',
        #'test_browse_datastore_files',   
    ]
    return unittest.TestSuite(map(VsphereClientTestCase, tests))

if __name__ == u'__main__':
    runtest(test_suite())
    