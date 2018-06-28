'''
Created on May 10, 2013

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .virtual_machine import VirtualMachine
from .virtual_router import VirtualRouter

class Network(ClskObject):
    """Network api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'network'

    @watch
    def get_network_type(self):
        """Get network type. Cloudstack define isolated and guest network. 
        
        Isolated network is used in private and hybrid cloud. Subnet is completely 
        private and cannot published without a router that route correctly all 
        the network packets.
        
        Guest network is used when you want to configure a network with a vlan
        and a subnet configured on the physical network appliance and visible in 
        your lan.
        
        :return: Network type.
        :rtype: str
        """
        net_type = self._data['type']
        if net_type == 'Shared':
            return 'guest'
        elif net_type == 'Isolated':
            return 'isolated'

    @watch
    def get_service(self):
        """Get all service offered by the network. Service are firewall, port
        forward, static nat, etc.
        
        :return: Dictionary with all network service.
        :rtype: dict        
        """
        if 'service' in self._data:
            return self._data['service']
        else:
            raise ClskError('Network %s does not have service confgiured' % 
                                  self.name)

    @watch
    def restart(self, cleanup=False):
        """Restarts the network. Includes 
        1) restarting network elements - virtual routers, dhcp servers 
        2) reapplying all public ips 
        3) reapplying loadBalancing/portForwarding rules
        
        *Async command*

        :param cleanup: If True delete and create Virual Router
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'restartNetwork',
                  'id':self.id,
                  'cleanup':cleanup}

        name = self.name
        self.logger.debug('Restart network %s' % name)

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['restartnetworkresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'restartNetwork', res))
            return clsk_job_id
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def delete(self):
        """Deletes the network.
        
        *Async command*

        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteNetwork',
                  'id':self.id}
        
        self.logger.debug('Remove network %s' % self.name)
        
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletenetworkresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'deleteNetwork', res))
            return clsk_job_id
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)     

    def list_all_virtual_machines(self):
        '''List all clusters'''
        vms = self.list_virtual_machines()
        vms.extend(self.list_routers())
        return vms
    
    @watch
    def list_routers(self):
        '''List all system vms'''
        params = {'command':'listRouters',
                  'networkid':self.id,
                  'domainid':self._data['domainid']}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
                self.logger.debug('List network %s router: %s' % (
                                  self.name, data))
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualRouter(self._api_client, data=item)
            vms.append(vm)
        return vms         

    @watch
    def list_virtual_machines(self):
        '''List all virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'listall':True,
                  'networkid':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
                self.logger.debug('List network %s vm: %s' % (
                                  self.name, data))
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._orchestrator, item)
            vms.append(vm)
        return vms

    @watch
    def tree(self):
        '''Return host tree.'''
        network = {'name':self.info()['name'], 
                   'oid':self.id,
                   'type':self._obj_type,
                   'state':self._data['state'],
                   'children':[]} 
        for vm in self.list_all_virtual_machines():
            network['children'].append({'name':vm.name,
                                        'oid':vm.id,
                                        'type':vm.obj_type,
                                        'state':vm.data['state']})
        self.logger.debug('Create network %s tree' % self.name)
        return network

    #-----------------------------------VPN------------------------------------#
    @watch    
    def list_remote_access_vpns(self, ipaddressid=None):
        '''List remote access vpn.        :return: Cloudstack asynchronous job id
        :rtype: str
        
        :param ipaddressid: [optional] public IP address id
        
        Return:
        [{u'presharedkey': u'9O89veQ8s9mHpna6ZjrmzcYn', 
          u'account': u'admin', 
          u'domainid': u'ae3fad3c-d518-11e3-8225-0050560203f1', 
          u'publicipid': u'fc9fc2ce-98df-48d5-99c8-7d960a843f07', 
          u'id': u'2761b5a3-9949-4714-8610-656f5e978510', 
          u'publicip': u'10.102.43.124', 
          u'state': u'Running', 
          u'domain': u'ROOT', 
          u'iprange': u'10.1.2.2-10.1.2.8'}]

        '''
        params = {'command':'listRemoteAccessVpns',
                  'listall':'true',
                  'networkid':self.id,}

        if ipaddressid:
            params['publicipid'] = ipaddressid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listremoteaccessvpnsresponse']
            if len(res) > 0:
                data = res['remoteaccessvpn']
                self.logger.debug('List network %s remote access vpns: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    @watch        
    def create_remote_access_vpn(self, publicipid):
        """Creates a l2tp/ipsec remote access vpn.
        
        *Async command*

        :param publicipid: public ip address id of the vpn server
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createRemoteAccessVpn',
                  'publicipid':publicipid}
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createremoteaccessvpnresponse']['jobid']
            self.logger.debug('Start job - createRemoteAccessVpn: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    @watch        
    def delete_remote_access_vpn(self, publicipid):
        """Destroys a l2tp/ipsec remote access vpn.

        *Async command*

        :param publicipid: public ip address id of the vpn server
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`     
        """        
        params = {'command':'deleteRemoteAccessVpn',
                  'publicipid':publicipid}
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteremoteaccessvpnresponse']['jobid']
            self.logger.debug('Start job - deleteRemoteAccessVpn: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def list_vpn_user(self):
        '''List remote access vpn.
        
        Return:
        [{u'presharedkey': u'9O89veQ8s9mHpna6ZjrmzcYn', 
          u'account': u'admin', 
          u'domainid': u'ae3fad3c-d518-11e3-8225-0050560203f1', 
          u'publicipid': u'fc9fc2ce-98df-48d5-99c8-7d960a843f07', 
          u'id': u'2761b5a3-9949-4714-8610-656f5e978510', 
          u'publicip': u'10.102.43.124', 
          u'state': u'Running', 
          u'domain': u'ROOT', 
          u'iprange': u'10.1.2.2-10.1.2.8'}]

        '''
        params = {'command':'listVpnUsers',
                  'listall':'true',
                  'account':self._data['account'],
                  'domainid':self._data['domainid']}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listvpnusersresponse']
            if len(res) > 0:
                data = res['vpnuser']
                self.logger.debug('List network %s remote access vpn users: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def add_vpn_user(self, username, password):
        """Adds vpn user.
        
        *Async command*

        :param username: username for the vpn user
        :param password: password for the username
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'addVpnUser',
                  'username':username, 
                  'password':password,
                  'account':self._data['account'],
                  'domainid':self._data['domainid'],
                  }
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['addvpnuserresponse']['jobid']
            self.logger.debug('Start job - addVpnUser: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)  

    @watch
    def remove_vpn_user(self, username):
        """Removes vpn user.
        
        *Async command*

        :param username: username for the vpn user
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'removeVpnUser',
                  'username':username,
                  'account':self._data['account'],
                  'domainid':self._data['domainid'],
                  }
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['removevpnuserresponse']['jobid']
            self.logger.debug('Start job - removeVpnUser: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    #-----------------------------------VPN------------------------------------#

    #-----------------------------------PUBLIC IP------------------------------#
    @watch    
    def list_public_ip_addresses(self, ipaddressid=None):
        '''List public Ip Addresses.
        
        :param ipaddressid: [optional] public IP address id
        
        Return:
        
        [{u'networkid': u'48e77c5a-c8d6-4c8a-a5e4-675b0f555507', 
          u'physicalnetworkid': u'c0bdc2a5-a222-49cf-a11a-98ff886ee210', 
          u'account': u'oasis', 
          u'domainid': u'92e75598-4604-43d3-a8ad-b3a96bfabcb1', 
          u'isportable': False, u'issourcenat': True, 
          u'associatednetworkname': u'oasis-network01', 
          u'tags': [], 
          u'isstaticnat': False, 
          u'domain': u'PRG-EUROPEI', 
          u'vlanid': u'1ed1b9e8-bfac-4cf2-be93-052fe0b182ea', 
          u'zoneid': u'2af97976-9679-427b-8dbd-6b11f9dfa169', 
          u'vlanname': u'vlan://28', 
          u'state': u'Allocated', 
          u'associatednetworkid': u'48a74a6f-c839-4ffc-9fa6-d5f9d453cd56', 
          u'forvirtualnetwork': True, 
          u'allocated': u'2014-05-07T11:16:25+0200', 
          u'issystem': False, 
          u'ipaddress': u'10.102.43.125', 
          u'id': u'c08a5410-1bf3-4250-b1ed-41a0354c9821', 
          u'zonename': u'zona_kvm_01'}, ...]
        '''
        params = {'command':'listPublicIpAddresses',
                  'listall':'true',
                  'associatednetworkid':self.id,
                  'allocatedonly':'true'}
        
        if ipaddressid:
            params['id'] = ipaddressid
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listpublicipaddressesresponse']
            if len(res) > 0:
                data = res['publicipaddress']
                self.logger.debug('List network %s public ip address: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def associate_public_ip_addresses(self):
        """Associate public Ip Addresses to network.

        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'associateIpAddress',
                  'account':self._data['account'],
                  'domainid':self._data['domainid'],
                  'networkid':self.id}
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['associateipaddressresponse']['jobid']
            self.logger.debug('Start job - associateIpAddress: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def disassociate_public_ip_addresses(self, ipaddressid):
        """Associate public Ip Addresses to network.

        *Async command*

        :param ipaddressid: [optional] public IP address id
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'disassociateIpAddress',
                  'id':ipaddressid}
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['disassociateipaddressresponse']['jobid']
            self.logger.debug('Start job - disassociateIpAddress: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    #-----------------------------------PUBLIC IP------------------------------# 

    #-----------------------------------FIREWALL-------------------------------#
    @watch    
    def list_firewall_rules(self, ipaddressid=None):
        '''List firewall rules
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`   
        '''
        params = {'command':'listFirewallRules',
                  'networkid':self.id,
                  'listall':True}
        
        if ipaddressid:
            params['ipaddressid'] = ipaddressid
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listfirewallrulesresponse']
            if len(res) > 0:
                data = res['firewallrule']
                self.logger.debug('List network firewall rules: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def create_firewall_rule(self, ipaddressid, protocol, cidrlist, ftype, 
                                   startport=None, endport=None,
                                   icmpcode=None, icmptype=None):
        """Create firewall rules
        
        *Async command*
        
        :param ipaddressid: the IP address id of the port forwarding rule
        :param str protocol: the protocol for the firewall rule. Valid values are TCP/UDP/ICMP.
        :param cidrlist: the cidr list to forward traffic from
        :param int startport: the starting port of firewall rule. Use with TCP/UDP.
        :param int endport: the ending port of firewall rule. Use with TCP/UDP.
        :param icmpcode: error code for this icmp message. Use with ICMP.
        :param icmptype: type of the icmp message being sent. Use with ICMP.
        :param str ftype: type of firewall rule: system/user
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createFirewallRule',
                  'ipaddressid':ipaddressid,
                  'protocol':protocol,
                  'cidrlist':cidrlist,
                  'type':ftype}

        if startport:
            params['startport'] = startport
        if endport:
            params['endport'] = endport
        if icmpcode:
            params['icmpcode'] = icmpcode
        if icmptype:
            params['icmptype'] = icmptype                        

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createfirewallruleresponse']['jobid']
            self.logger.debug('Start job - createfirewallruleresponse: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete_firewall_rule(self, firewall_rule_id):
        """Create firewall rules
        
        *Async command*
        
        :param str firewall_rule_id: the ID of the firewall rule
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteFirewallRule',
                  'id':firewall_rule_id}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletefirewallruleresponse']['jobid']
            self.logger.debug('Start job - deleteFirewallRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)        
    #-----------------------------------FIREWALL-------------------------------#

    #-----------------------------------PORT FORWARD---------------------------#
    @watch    
    def list_port_forward_rules(self, ipaddressid=None):
        '''List port forwarding rules
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`             
        '''
        params = {'command':'listPortForwardingRules',
                  'networkid':self.id,
                  'listall':True}

        if ipaddressid:
            params['ipaddressid'] = ipaddressid        
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listportforwardingrulesresponse']
            if len(res) > 0:
                data = res['portforwardingrule']
                self.logger.debug('List network %s port forwarding rules: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def create_port_forward_rule(self, ipaddressid, protocol, virtualmachineid,
                                       privateport, privateendport,
                                       publicport, publicendport):
        """Create port forward rules
        
        *Async command*
        
        :param ipaddressid: the IP address id of the port forwarding rule
        :param privateport: the starting port of port forwarding rule's private 
                            port range
        :param privateendport: the ending port of port forwarding rule's private 
                               port range
        :param publicport: the starting port of port forwarding rule's public 
                           port range
        :param publicendport: the ending port of port forwarding rule's private 
                              port range
        :param protocol: the protocol for the port fowarding rule. Valid values 
                         are TCP or UDP.
        :param virtualmachineid: the ID of the virtual machine for the port 
                                 forwarding rule
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createPortForwardingRule',
                  'ipaddressid':ipaddressid,
                  'protocol':protocol,
                  'privateport':privateport,
                  'privateendport':privateendport,
                  'publicport':publicport,
                  'publicendport':publicendport,
                  'virtualmachineid':virtualmachineid,
                  'openfirewall':False}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createportforwardingruleresponse']['jobid']
            self.logger.debug('Start job - createPortForwardingRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def delete_port_forward_rule(self, port_forward_rule_id):
        """Create port forward rules
        
        *Async command*
        
        :param str port_forward_rule_id: the ID of the firewall rule
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deletePortForwardingRule',
                  'id':port_forward_rule_id}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteportforwardingruleresponse']['jobid']
            self.logger.debug('Start job - deletePortForwardingRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    #-----------------------------------PORT FORWARD---------------------------#

    #-----------------------------------EGRESS RULES---------------------------#
    @watch    
    def list_egress_rules(self):
        '''List egress firewall rules
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        '''
        params = {'command':'listEgressFirewallRules',
                  'networkid':self.id,
                  'listall':True}    
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listegressfirewallrulesresponse']
            if len(res) > 0:
                data = res['firewallrule']
                self.logger.debug('List network %s egress rules: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def create_egress_rule(self, ipaddressid, protocol, cidrlist, ftype, 
                                 startport=None, endport=None,
                                 icmpcode=None, icmptype=None):
        """Create egress rules
        
        *Async command*
        
        :param ipaddressid: the IP address id of the port forwarding rule
        :param str protocol: the protocol for the firewall rule. Valid values 
                             are TCP/UDP/ICMP.
        :param cidrlist: the cidr list to forward traffic from
        :param int startport: the starting port of firewall rule. Use with TCP/UDP.
        :param int endport: the ending port of firewall rule. Use with TCP/UDP.
        :param icmpcode: error code for this icmp message. Use with ICMP.
        :param icmptype: type of the icmp message being sent. Use with ICMP.
        :param str ftype: type of firewall rule: system/user
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createEgressFirewallRule',
                  'networkid':self.id,
                  'protocol':protocol,
                  'cidrlist':cidrlist,
                  'type':ftype}

        if startport:
            params['startport'] = startport
        if endport:
            params['endport'] = endport
        if icmpcode:
            params['icmpcode'] = icmpcode
        if icmptype:
            params['icmptype'] = icmptype                        

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createegressfirewallruleresponse']['jobid']
            self.logger.debug('Start job - createEgressFirewallRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def delete_egress_rule(self, egress_rule_id):
        """Create egress rules
        
        *Async command*
        
        :param str egress_rule_id: the ID of the firewall rule
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteEgressFirewallRule',
                  'id':egress_rule_id}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteegressfirewallruleresponse']['jobid']
            self.logger.debug('Start job - deleteEgressFirewallRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)                
    #-----------------------------------EGRESS RULES---------------------------#
    
    #-----------------------------------LOAD BALANCE---------------------------#
    @watch    
    def list_load_balancer_rules(self):
        '''List load balancer rules
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        '''
        params = {'command':'listLoadBalancerRules',
                  'networkid':self.id,
                  'listall':True}    
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listloadbalancerrulesresponse']
            if len(res) > 0:
                data = res['loadbalancerrule']
                self.logger.debug('List netwrok %s load balancer rules: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch        
    def create_load_balancer_rule(self, name, description, algorithm, 
                                        privateport, publicport, 
                                        publicipid, protocol='tcp'):
        """Create load balancer rule
        
        *Async command*
        
        :param algorithm: load balancer algorithm (source, roundrobin, leastconn)
        :param name: name of the Load Balancer rule
        :param description: the description of the Load Balancer rule
        :param privateport: the private port of the private ip address/virtual 
                            machine where the network traffic will be load 
                            balanced to
        :param publicport: the public port from where the network traffic will 
                           be load balanced from
        :param protocol: The protocol for the LB
        :param publicipid: public ip address id from where the network traffic 
                           will be load balanced from
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createLoadBalancerRule',
                  'networkid':self.id,
                  'algorithm':algorithm,
                  'name':name,
                  'description':description,
                  'privateport':privateport,
                  'publicport':publicport,
                  'protocol':protocol,
                  'publicipid':publicipid}                      

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createloadbalancerruleresponse']['jobid']
            self.logger.debug('Start job - createLoadBalancerRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def delete_load_balancer_rule(self, load_balancer_rule_id):
        """Delete load balancer rule
        
        *Async command*
        
        :param load_balancer_rule_id: the ID of the load balancer rule
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteLoadBalancerRule',
                  'id':load_balancer_rule_id}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteloadbalancerruleresponse']['jobid']
            self.logger.debug('Start job - deleteLoadBalancerRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)                    

    @watch
    def list_load_balancer_rule_instances(self, load_balancer_rule_id):
        '''List load balancer rules
        
        :param load_balancer_rule_id: the ID of the load balancer rule
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        '''
        params = {'command':'listLoadBalancerRuleInstances',
                  'id':load_balancer_rule_id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listloadbalancerruleinstancesresponse']
            if len(res) > 0:
                data = res['loadbalancerruleinstance']
                self.logger.debug('List network %s load balancer rule instances: %s' % (
                                  self.name, data))
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms        
        
    @watch
    def assign_to_load_balancer_rule(self, load_balancer_rule_id, 
                                           virtualmachineids):
        """Delete load balancer rule
        
        *Async command*
        
        :param load_balancer_rule_id: the ID of the load balancer rule
        :param virtualmachineids: the list of IDs of the virtual machine that 
                                  are being assigned to the load balancer 
                                  rule(i.e. virtualMachineIds=1,2,3)
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'assignToLoadBalancerRule',
                  'id':load_balancer_rule_id,
                  'virtualmachineids':virtualmachineids}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['assigntoloadbalancerruleresponse']['jobid']
            self.logger.debug('Start job - assignToLoadBalancerRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def remove_from_load_balancer_rule(self, load_balancer_rule_id, 
                                             virtualmachineids):
        """Removes a virtual machine or a list of virtual machines from a load 
        balancer rule.
        
        *Async command*
        
        :param load_balancer_rule_id: the ID of the load balancer rule
        :param virtualmachineids: the list of IDs of the virtual machines that 
                                  are being removed from the load balancer rule 
                                  (i.e. virtualMachineIds=1,2,3)
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'removeFromLoadBalancerRule',
                  'id':load_balancer_rule_id,
                  'virtualmachineids':virtualmachineids}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['removefromloadbalancerruleresponse']['jobid']
            self.logger.debug('Start job - removeFromLoadBalancerRule: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def list_lb_stickiness_policies(self, load_balancer_rule_id):
        '''Lists LBStickiness policies.

        :param load_balancer_rule_id: the ID of the load balancer rule
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        '''
        params = {'command':'listLBStickinessPolicies',
                  'lbruleid':load_balancer_rule_id}    
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listlbstickinesspoliciesresponse']
            print res
            if len(res) > 0:
                data = res['loadbalancerruleinstance']
                self.logger.debug('List network %s load balancer rule instances: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def create_lb_stickiness_policy(self, lbruleid, name, description,
                                          methodname, param=None):
        """Creates a Load Balancer stickiness policy.
        
        *Async command*
        
        :param lbruleid: the ID of the load balancer rule
        :param methodname: name of the LB Stickiness policy method, possible 
                           values can be obtained from ListNetworks API
        :param name: name of the LB Stickiness policy
        :param description: the description of the LB Stickiness policy
        :param param: param list. Example: param[0].name=cookiename&param[0].value=LBCooki
                      [optional]
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createLBStickinessPolicy',
                  'lbruleid':lbruleid,
                  'name':name,
                  'description':description,
                  'methodname':methodname}
        
        if param:
            params['param'] = param               

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createLBStickinessPolicy']['jobid']
            self.logger.debug('Start job - createLBStickinessPolicy: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete_lb_stickiness_policy(self, policy_id):
        """Deletes a LB stickiness policy.
        
        *Async command*
        
        :param policy_id: the ID of the LB stickiness policy
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteLBStickinessPolicy',
                  'id':policy_id}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteLBstickinessrruleresponse']['jobid']
            self.logger.debug('Start job - deleteLBStickinessPolicy: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def list_lb_health_check_policies(self, load_balancer_rule_id):
        '''Lists load balancer HealthCheck policies.

        :param load_balancer_rule_id: the ID of the load balancer rule
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        '''
        params = {'command':'listLBHealthCheckPolicies',
                  'lbruleid':load_balancer_rule_id}    
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listlbhealthcheckpoliciesresponse']
            if len(res) > 0:
                print res
                data = res['loadbalancerruleinstance']
                self.logger.debug('List network %s load balancer rule instances: %s' % (
                                  self.name, data))
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def create_lb_health_check_policy(self, lbruleid, description, 
                                            healthythreshold=None, intervaltime=None,
                                            pingpath=None, responsetimeout=None,
                                            unhealthythreshold=None):
        """Creates a Load Balancer healthcheck policy
        
        *Async command*
        
        :param lbruleid: the ID of the load balancer rule
        :param description: the description of the LB Stickiness policy
        :param healthythreshold: Number of consecutive health check success 
                                 before declaring an instance healthy
        :param intervaltime: Amount of time between health checks 
                            (1 sec - 20940 sec)
        :param pingpath: HTTP Ping Path
        :param responsetimeout: Time to wait when receiving a response from the 
                                health check (2sec - 60 sec)
        :param unhealthythreshold: Number of consecutive health check failures 
                                   before declaring an instance unhealthy
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'createLBHealthCheckPolicy',
                  'lbruleid':lbruleid,
                  'description':description}

        if healthythreshold:
            params['healthythreshold'] = healthythreshold  
        if intervaltime:
            params['intervaltime'] = intervaltime         
        if pingpath:
            params['pingpath'] = pingpath               
        if responsetimeout:
            params['responsetimeout'] = responsetimeout  
        if unhealthythreshold:
            params['unhealthythreshold'] = unhealthythreshold

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createlbhealthcheckpolicyresponse']['jobid']
            self.logger.debug('Start job - createLBHealthCheckPolicy: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete_lb_health_check_policy(self, policy_id):
        """Deletes a load balancer HealthCheck policy.
        
        *Async command*
        
        :param policy_id: the ID of the load balancer HealthCheck policy
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteLBHealthCheckPolicy',
                  'id':policy_id}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletelbhealthcheckpolicyresponse']['jobid']
            self.logger.debug('Start job - deleteLBHealthCheckPolicy: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    #TODO gestire la parte dei certificati ssl per il bilanciatore
    #-----------------------------------LOAD BALANCE---------------------------#
    
    #-----------------------------------STATIC NAT-----------------------------#
    def is_enabled_source_nat(self, ipaddressid):
        data = self.list_public_ip_addresses(ipaddressid=ipaddressid)[0]
        return data['issourcenat']
    
    def is_enabled_static_nat(self, ipaddressid):
        data = self.list_public_ip_addresses(ipaddressid=ipaddressid)[0]
        return data['isstaticnat']
    
    @watch    
    def enable_static_nat(self, ipaddressid, virtualmachineid):
        '''Enables static nat for given ip address.

        :param ipaddressid: the public IP address id for which static nat 
                            feature is being enabled
        :param virtualmachineid: the ID of the virtual machine for enabling 
                                 static nat feature
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        '''
        params = {'command':'enableStaticNat',
                  'ipaddressid':ipaddressid,
                  'virtualmachineid':virtualmachineid}    
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['enablestaticnatresponse']
            if len(res) > 0:
                data = res['success']
                self.logger.debug('Enables static nat: %s' % data)
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def disable_static_nat(self, ipaddressid):
        """Disables static rule for given ip address.
        
        *Async command*
        
        :param ipaddressid: the public IP address id for which static nat 
                            feature is being disableed
        :return: Cloudstack asynchronous job id
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'disableStaticNat',
                  'ipaddressid':ipaddressid}                   

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['disablestaticnatresponse']['jobid']
            self.logger.debug('Start job - disableStaticNat: %s' % res)
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    #-----------------------------------STATIC NAT-----------------------------#