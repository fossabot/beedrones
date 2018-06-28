'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .virtual_machine import VirtualMachine

class Network(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'network'

    def info(self, cache=True):
        '''Describe network'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listNetworks',
                  'listall':True,
                  'id':self._id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listnetworksresponse']['network'][0]
            self._data = res
            
            return self._data
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)

    def restart(self, job_id):
        """Restarts the network. Includes 
        1) restarting network elements - virtual routers, dhcp servers 
        2) reapplying all public ips 
        3) reapplying loadBalancing/portForwarding rules
        
        Async command."""        
        params = {'command':'restartNetwork',
                  'id':self._id}

        name = self.info()['name']
        self.logger.debug('Restart network %s' % name)

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['restartnetworkresponse']['jobid']
            job_res = self._api_client.query_async_job(job_id, clsk_job_id)       
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        if 'success' in job_res and job_res['success']:
            return True
        else:
            self.logger.error('Error restarting network: %s' % name)
            raise ClskObjectError('Error restarting network: %s' % name)

    def delete(self, job_id):
        """Deletes the network.
        
        Async command."""        
        params = {'command':'deleteNetwork',
                  'id':self._id}
        
        name = self.info()['name']
        self.logger.debug('Remove network %s' % name)
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletenetworkresponse']['jobid']
            job_res = self._api_client.query_async_job(job_id, clsk_job_id)
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        if 'success' in job_res and job_res['success']:
            return True
        else:
            self.logger.error('Error removing network: %s' % name)
            raise ClskObjectError('Error removing network: %s' % name)        

    def tree(self):
        '''Return host tree.'''
        network = {'name':self.info()['name'], 
                   'oid':self._id,
                   'class':'node',
                   'type':self._obj_type, 
                   'children':[]} 
        for vm in self.list_all_virtual_machines():
            network['children'].append({'name':vm.info()['name'],
                                        'oid':vm.id,
                                        'type':vm.obj_type,
                                        'vm_type':vm.type,
                                        'class':'node_green',})
        return network

    #-----------------------------------VPN------------------------------------#
    def list_remote_access_vpns(self, ipaddressid=None):
        '''List remote access vpn.
        
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
                  'networkid':self._id,}

        if ipaddressid:
            params['publicipid'] = ipaddressid

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listremoteaccessvpnsresponse']
            if len(res) > 0:
                data = res['remoteaccessvpn']
                return data
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def create_remote_access_vpn(self, job_id, publicipid):
        """Creates a l2tp/ipsec remote access vpn.
        Async command.

        :param job_id: unique id of the async job
        :param publicipid: public ip address id of the vpn server
        
        Return:
        
        """        
        params = {'command':'createRemoteAccessVpn',
                  'publicipid':publicipid}
            
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['createremoteaccessvpnresponse']['jobid']
            data = self._api_client.query_async_job(job_id, clsk_job_id)['jobresult']['remoteaccessvpn']
            self.logger.debug('Created remote access vpn associated to public ip %s' % publicipid)
            return data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def delete_remote_access_vpn(self, publicipid):
        """Destroys a l2tp/ipsec remote access vpn.
        Async command.

        :param publicipid: public ip address id of the vpn server
        
        Return:        
        """        
        params = {'command':'deleteRemoteAccessVpn',
                  'publicipid':publicipid}
            
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            job_id = res['deleteremoteaccessvpnresponse']['jobid']
            data = self._api_client.query_async_job(job_id)['jobresult']['remoteaccessvpn']
            self.logger.debug('Removed remote access vpn associated to public ip %s' % publicipid)
            return data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

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
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvpnusersresponse']
            if len(res) > 0:
                data = res['vpnuser']
                return data
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def add_vpn_user(self, username, password):
        """Adds vpn user.
        Async command.

        :param username: username for the vpn user
        :param password: password for the username
        
        Return:
        
        """        
        params = {'command':'addVpnUser',
                  'username':username, 
                  'password':password,
                  'account':self._data['account'],
                  'domainid':self._data['domainid'],
                  }
            
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            job_id = res['addvpnuserresponse']['jobid']
            data = self._api_client.query_async_job(job_id)['jobresult']['vpnuser']
            self.logger.debug('Add vpn user %s to domain/account' % (
                                  username, 
                                  self._data['domainid'], 
                                  self._data['account']))
            return data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)  
        
    def remove_vpn_user(self, username):
        """Removes vpn user.
        Async command.

        :param username: username for the vpn user
        
        Return:
        
        """        
        params = {'command':'removeVpnUser',
                  'username':username,
                  'account':self._data['account'],
                  'domainid':self._data['domainid'],
                  }
            
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            job_id = res['removevpnuserresponse']['jobid']
            data = self._api_client.query_async_job(job_id)['jobresult']['vpnuser']
            self.logger.debug('Remove vpn user %s to domain/account' % (
                                  username, 
                                  self._data['domainid'], 
                                  self._data['account']))
            return data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
    #-----------------------------------VPN------------------------------------#

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
                  'associatednetworkid':self._id,
                  'allocatedonly':'true'}
        
        if ipaddressid:
            params['id'] = ipaddressid
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listpublicipaddressesresponse']
            if len(res) > 0:
                data = res['publicipaddress']
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)

    def list_firewall_rules(self, ipaddressid=None):
        '''List firewall rules
        
        [{u'cidrlist': u'0.0.0.0/0',
          u'endport': u'80',
          u'id': u'8fb089a4-15c3-4755-91a2-0a3159142f8c',
          u'ipaddress': u'10.102.43.125',
          u'ipaddressid': u'c08a5410-1bf3-4250-b1ed-41a0354c9821',
          u'networkid': u'48a74a6f-c839-4ffc-9fa6-d5f9d453cd56',
          u'protocol': u'tcp',
          u'startport': u'80',
          u'state': u'Active',
          u'tags': []}]
        '''
        params = {'command':'listFirewallRules',
                  'networkid':self._id,
                  'listall':True,
                 }
        
        if ipaddressid:
            params['ipaddressid'] = ipaddressid
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listfirewallrulesresponse']
            if len(res) > 0:
                data = res['firewallrule']
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)

    def list_port_forwarding_rules(self, ipaddressid=None):
        '''List port forwarding rules
        
        [{u'cidrlist': u'',
          u'id': u'cd52eecc-2a4c-4ea2-90dd-b0e594f15998',
          u'ipaddress': u'10.102.43.125',
          u'ipaddressid': u'c08a5410-1bf3-4250-b1ed-41a0354c9821',
          u'networkid': u'48a74a6f-c839-4ffc-9fa6-d5f9d453cd56',
          u'privateendport': u'80',
          u'privateport': u'80',
          u'protocol': u'tcp',
          u'publicendport': u'80',
          u'publicport': u'80',
          u'state': u'Active',
          u'tags': [],
          u'virtualmachinedisplayname': u'vm-oasis-01',
          u'virtualmachineid': u'03d38085-154a-454e-9aa0-b81c717dc9ff',
          u'virtualmachinename': u'vm-oasis-01',
          u'vmguestip': u'172.16.1.242'}]
        '''
        params = {'command':'listPortForwardingRules',
                  'networkid':self._id,
                  'listall':True,
                 }

        if ipaddressid:
            params['ipaddressid'] = ipaddressid        
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listportforwardingrulesresponse']
            if len(res) > 0:
                data = res['portforwardingrule']
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)

    def list_egress_firewall_rules(self):
        '''List egress firewall rules
        
        [{u'cidrlist': u'0.0.0.0/0',
          u'id': u'1b72dd2c-db83-40a1-8ee1-06ac9c8d5dc2',
          u'networkid': u'48a74a6f-c839-4ffc-9fa6-d5f9d453cd56',
          u'protocol': u'all',
          u'state': u'Active',
          u'tags': []}]
        '''
        params = {'command':'listEgressFirewallRules',
                  'networkid':self._id,
                  'listall':True,
                 }    
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listegressfirewallrulesresponse']
            if len(res) > 0:
                data = res['firewallrule']
                return data
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)

    def list_all_virtual_machines(self):
        '''List all clusters'''
        vms = self.list_virtual_machines()
        vms.extend(self.list_routers())
        return vms
    
    def list_routers(self):
        '''List all system vms'''
        params = {'command':'listRouters',
                  'networkid':self._id,
                  'domainid':self.info()['domainid']
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, data=item)
            vms.append(vm)
        return vms         
        
    def list_virtual_machines(self):
        '''List all virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'listall':True,
                  'networkid':self._id,
                 }
        
        try:
            response = self.send_api_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms        