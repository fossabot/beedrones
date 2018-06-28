'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .virtual_machine import VirtualMachine
from .network import Network
from .template import Template
from .volume import Volume

class Resource(object):
    res = [('Instance', 'Number of instances a user can create'),
           ('IP', 'Number of public IP addresses an account can own'),
           ('Volume', 'Number of disk volumes an account can own'),
           ('Snapshot', 'Number of snapshots an account can own'),             
           ('Template', 'Number of templates an account can register/create'),
           ('Project', 'Number of projects an account can own'),
           ('Network', 'Number of networks an account can own'),
           ('VPC', 'Number of VPC an account can own'),
           ('CPU', 'Number of CPU an account can allocate for his resources'),             
           ('Memory', 'Amount of RAM an account can allocate for his resources'),             
           ('PrimaryStorage', 'Amount of Primary storage an account can allocate for his resoruces'),
           ('SecondaryStorage', 'Amount of Secondary storage an account can allocate for his resources')]
    
    @staticmethod
    def name(resource_id):
        return Resource.res[resource_id][0]

    @staticmethod
    def desc(resource_id):
        return Resource.res[resource_id][1]

    @staticmethod
    def respurce_id(name):
        return [Resource.res.index(r) for r in Resource.res if r[0] == name][0]

class Account(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None, domain_id=None):
        ''' '''
        # attributes
        self._obj_type = 'account'
        self._domain_id = None
        
        if data:
            self._domain_id = data['domainid']
        elif domain_id:
            self._domain_id = domain_id
        else:
            raise ClskObjectError('Domain id must be provided.')
        
        ClskObject.__init__(self, api_client, data=data, oid=oid)

    def tree(self):
        '''Return host tree.'''
        account = {'name':self._data['name'], 
                   'id':self._id, 
                   'type':self._obj_type, 
                   'childs':[]}
        
        vms = self.list_virtual_machines()
        vms.extend(self.list_routers())
        
        # root admin - add also system vms
        if self._data['accounttype'] == 1:
            vms.extend(self.list_system_vms())
            
        for vm in vms:
            account['childs'].append({'name':vm.name,
                                      'id':vm.id,
                                      'type':vm.obj_type,
                                      'vm_type':vm.type,
                                      'state':vm.get_state()})
        return account

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listAccounts',
                  'id':self._id,
                  'domainid':self._domain_id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listaccountsresponse']['account'][0]
            self._data = res
            
            return self._data
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def delete(self, job_id):
        """Delete the account.
        Async command.
        """        
        params = {'command':'deleteAccount',
                  'id':self._id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteaccountresponse']['jobid']
            job_res = self._api_client.query_async_job(job_id, clsk_job_id, delta=1)
            
            return job_res
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)  

    def get_resource_limit(self):
        """
        :param max: new resource limit max value
        :param type: 0 - Instance. Number of instances a user can create.
                     1 - IP. Number of public IP addresses an account can own.
                     2 - Volume. Number of disk volumes an account can own.
                     3 - Snapshot. Number of snapshots an account can own.
                     4 - Template. Number of templates an account can register/create.5 - Project. Number of projects an account can own.
                     5 - Project. Number of projects an account can own
                     6 - Network. Number of networks an account can own.
                     7 - VPC. Number of VPC an account can own.
                     8 - CPU. Number of CPU an account can allocate for his resources.
                     9 - Memory. Amount of RAM an account can allocate for his resources.
                     10 - PrimaryStorage. Amount of Primary storage an account can allocate for his resoruces.
                     11 - SecondaryStorage. Amount of Secondary storage an account can allocate for his resources.
        """
        params = {'command':'listResourceLimits',
                  'account':self._data['name'],
                  'domainid':self._domain_id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listresourcelimitsresponse']['resourcelimit']
            items = {Resource.name(int(i['resourcetype'])):[i['max'], Resource.desc(int(i['resourcetype']))] for i in res}
            return items
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def update_resource_limit(self, type, max):
        """
        :param max: new resource limit max value
        :param type: 0 - Instance. Number of instances a user can create.
                     1 - IP. Number of public IP addresses a user can own.
                     2 - Volume. Number of disk volumes a user can create.
                     3 - Snapshot. Number of snapshots a user can create.
                     4 - Template. Number of templates that a user can register/create.
                     6 - Network. Number of guest network a user can create.
                     7 - VPC. Number of VPC a user can create.
                     8 - CPU. Total number of CPU cores a user can use.
                     9 - Memory. Total Memory (in MB) a user can use.
                     10 - PrimaryStorage. Total primary storage space (in GiB) a user can use.
                     11 - SecondaryStorage.
        """
        params = {'command':'updateResourcelimit',
                  'resourcetype':type,
                  'account':self._data['name'],
                  'domainid':self._domain_id,
                  'max':max,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            return res
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def list_all_virtual_machines(self):
        '''List all clusters'''
        vms = self.list_virtual_machines()
        vms.extend(self.list_system_vms())
        vms.extend(self.list_routers())
        return vms

    def list_system_vms(self):
        '''List all system vms'''
        params = {'command':'listSystemVms',
                  'domainid':self._domain_id,
                  'account':self._data['name'],                  
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listsystemvmsresponse']
            if len(res) > 0:
                data = res['systemvm']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)       
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms 

    def list_routers(self):
        '''List all routers'''
        params = {'command':'listRouters',
                  'domainid':self._domain_id,
                  'account':self._data['name'],
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms

    def list_virtual_machines(self):
        '''List virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'domainid':self._domain_id,
                  'account':self._data['name'],
                 }      

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)      
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms

    def list_templates(self, zoneid, hypervisor):
        '''List all templates.'''
        params = {'command':'listTemplates',
                  'templatefilter':'all',
                  'domainid':self._domain_id,
                  'account':self._data['name'],
                  'hypervisor':hypervisor,
                  'zoneid':zoneid,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listtemplatesresponse']
            if len(res) > 0:
                data = res['template']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        templates = []
        for item in data:
            # create Template instance
            template = Template(self._api_client, item)
            templates.append(template)
        
        return templates

    def list_isos(self, zoneid, hypervisor):
        '''List all templates.'''
        params = {'command':'listIsos',
                  'isofilter':'all',
                  'domainid':self._domain_id,
                  'account':self._data['name'],
                  'hypervisor':hypervisor,
                  'isready':True,
                  'zoneid':zoneid,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listisosresponse']
            if len(res) > 0:
                data = res['iso']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        templates = []
        for item in data:
            # create Template instance
            template = Template(self._api_client, item)
            templates.append(template)
        
        return templates

    def list_networks(self, zone_id=None):
        '''List network.
        
        :param zone_id: [optional] id of the zone         
        '''
        params = {'command':'listNetworks',
                  'listall':'true',
                  'domainid':self._domain_id,
                  'account':self._data['name']       
                 }
        if zone_id:
            params['zoneid'] = zone_id

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listnetworksresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        networks = []
        for item in data:
            # create Account instance
            network = Network(self._api_client, item)
            networks.append(network)
        
        return networks           

    def list_volumes(self, zone_id=None):
        '''List volumes.

        :param zone_id: [optional] id of the zone 
        '''
        params = {'command':'listVolumes',
                  'listall':'true',
                  'domainid':self._domain_id,
                  'account':self._data['name']       
                 }

        if zone_id:
            params['zoneid'] = zone_id

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                data = res['volume']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

        volumes = []
        for item in data:
            # create Volume instance
            volume = Volume(self._api_client, item)
            volumes.append(volume)
        
        return volumes 

    def create_private_guest_network(self, name, displaytext, 
                                     networkoffering_id, zone_id):
        '''Create network for the account'''
        if not self._domain_id or not self._data['name']:
            raise ApiError("Domain id or account name are not specified.")
        
        params = {'command':'createNetwork',
                  'name':self._data['name'],
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'domainid':self._domain_id,
                  'account':self._data['name'],
                 }
        
        try:
            res = self._api_client.send_api_request(params)['listnetworksresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        networks = []
        for item in data:
            # create Account instance
            network = Network(self._api_client, item)
            networks.append(network)
        
        return networks
        
    def create_direct_guest_network(self, name, displaytext, 
                                     networkoffering_id, zone_id,
                                     physical_network_id, gateway, netmask,
                                     startip, endip, vlan):
        '''Create diretc network for the account
        
        :param gateway: 10.102.221.129
        :param netmask: 255.255.255.240
        :param startip: 10.102.221.130
        :param endip: 10.102.221.142
        :param vlan: 329
        '''
        if not self._domain_id or not self._data['name']:
            raise ApiError("Domain id or account name are not specified.")
        
        params = {'command':'createNetwork',
                  'name':self._data['name'],
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'domainid':self._domain_id,
                  'account':self._data['name'],
                  'physicalnetworkid':physical_network_id,
                  'gateway':gateway,
                  'netmask':netmask,
                  'startip':startip,
                  'endip':endip,
                  'vlan':vlan,
                  'acltype':'account',
                 }
        
        try:
            res = self._api_client.send_api_request(params)['listnetworksresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return []
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        networks = []
        for item in data:
            # create Account instance
            network = Network(self._api_client, item)
            networks.append(network)
        
        return networks