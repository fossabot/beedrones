'''
Created on May 10, 2013

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .network import Network
from .template import Template
from .iso import Iso
from .volume import Volume
from .virtual_machine import VirtualMachine
from .virtual_router import VirtualRouter
from .system_virtual_machine import SystemVirtualMachine

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
    """Account api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'account'

    @watch
    def tree(self):
        """Return account tree.

        :return: Dictionary with all the info
        :rtype: dict       
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        account = {'name':self.name, 
                   'id':self.id, 
                   'type':self._obj_type, 
                   'childs':[]}
        
        vms = self.list_virtual_machines()
        vms.extend(self.list_routers())
        
        # root admin - add also system vms
        if self.accounttype == 1:
            vms.extend(self.list_system_vms())
            
        for vm in vms:
            account['childs'].append({'name':vm.name,
                                      'id':vm.id,
                                      'type':vm._obj_type,
                                      'state':vm.state})
        return account

    @watch
    def delete(self):
        """Delete account.

        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'deleteAccount',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteaccountresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'deleteAccount', res))
            return clsk_job_id
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)  

    @watch
    def get_resource_limit(self):
        """Get account resource limits.
        
        :return: Dictionary with all the account resource
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listResourceLimits',
                  'account':self.name,
                  'domainid':self.domainid}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listresourcelimitsresponse']['resourcelimit']
            items = {int(i['resourcetype']):(Resource.name(int(i['resourcetype'])),
                                             Resource.desc(int(i['resourcetype'])),
                                             i['max']) for i in res}
            self.logger.debug('Get account %s resource limits: %s' % (
                              self.name, items))
            return items
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def update_resource_limit(self, type, max):
        """Update account resource limit.
        
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
                     
        :return: Update response
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`                     
        """
        params = {'command':'updateResourceLimit',
                  'resourcetype':type,
                  'account':self.name,
                  'domainid':self.domainid,
                  'max':max}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            self.logger.debug('Update account %s resource limit: %s' % (
                              self.name, res))
            return res
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    def list_all_virtual_machines(self):
        """List all account virtual machines.
        
        :return: list of :class:`VirtualRouter` or :class:`VirtualMachine`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        vms = self.list_virtual_machines()
        vms.extend(self.list_routers())
        return vms
    
    @watch
    def list_system_vms(self, oid=None):
        """List all system vms
        
        :return: list of :class:`SystemVirtualMachine`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'listSystemVms',
                  'listAll':'true'}

        if oid:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listsystemvmsresponse']['systemvm']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = SystemVirtualMachine(self, item)
            vms.append(vm)
            
        self.logger.debug('List account %s Virtual Routers: %s' % (
                          self.name, vms)) 
        return vms    
    
    @watch    
    def list_routers(self):
        """List all account virtual routers.
        
        :return: list of :class:`VirtualRouter`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listRouters',
                  'domainid':self.domainid,
                  'account':self.name,}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
            else:
                data = []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)
        
        vms = []
        for item in data:
            vm = VirtualRouter(self._orchestrator, item)
            vms.append(vm)
            
        self.logger.debug('List account %s Virtual Routers: %s' % (
                          self.name, vms))            
        return vms         

    @watch
    def list_virtual_machines(self):
        """List all account virtual machines.
        
        :return: list of :class:`VirtualMachine`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listVirtualMachines',
                  'listall':True,
                  'domainid':self.domainid,
                  'account':self.name}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                data = []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)
        
        vms = []
        for item in data:
            vm = VirtualMachine(self._orchestrator, item)
            vms.append(vm)
            
        self.logger.debug('List account %s Virtual Machines: %s' % (
                          self.name, vms))                
        return vms

    @watch
    def list_templates(self, zoneid=None, hypervisor=None):
        """List all account templates.
        
        :param str zoneid: zone id [optional]
        :param str hypervisor: hypervisor. Es. KVM [optional]
        :return: list of :class:`Template`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listTemplates',
                  'templatefilter':'all',
                  'domainid':self.domainid,
                  'account':self.name}

        if zoneid:
            params['zoneid'] = zoneid
        if hypervisor:
            params['hypervisor'] = hypervisor

        try:
            response = self.send_request(params)
            res = json.loads(response)['listtemplatesresponse']
            if len(res) > 0:
                data = res['template']
            else:
                data = []
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        templates = []
        for item in data:
            # create Template instance
            template = Template(self._orchestrator, item)
            templates.append(template)
        
        self.logger.debug('List account %s templates: %s' % (
                          self.name, templates))          
        
        return templates

    @watch
    def list_isos(self, zoneid=None, hypervisor=None):
        """List all account isos.
        
        :param str zoneid: zone id [optional]
        :param str hypervisor: hypervisor. Es. KVM [optional]
        :return: list of :class:`Iso`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listIsos',
                  'isofilter':'all',
                  'domainid':self.domainid,
                  'account':self.name}

        if zoneid:
            params['zoneid'] = zoneid
        if hypervisor:
            params['hypervisor'] = hypervisor

        try:
            response = self.send_request(params)
            res = json.loads(response)['listisosresponse']
            print res
            if len(res) > 0:
                data = res['iso']
            else:
                data = []
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        isos = []
        for item in data:
            # create Template instance
            iso = Iso(self._orchestrator, item)
            isos.append(iso)
        
        self.logger.debug('List account %s isos: %s' % (
                          self.name, isos))          
        
        return isos

    @watch
    def list_sdns(self, zone_id=None):
        """List account software defined network.
        
        :param str zoneid: zone id [optional]
        :return: list of :class:`SDN`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listNetworks',
                  'listall':'true',
                  'domainid':self.domainid,
                  'account':self.name}
        if zone_id:
            params['zoneid'] = zone_id

        try:
            response = self.send_request(params)
            res = json.loads(response)['listnetworksresponse']
            if len(res) > 0:
                data = res['network']
            else:
                data = []
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        networks = []
        for item in data:
            # create Account instance
            network = SDN(self._orchestrator, item)
            networks.append(network)
        
        self.logger.debug('List account %s sdns: %s' % (
                          self.name, networks))         
        
        return networks           

    @watch
    def list_volumes(self, zone_id=None):
        """List account volumes.
        
        :param str zoneid: zone id [optional]
        :return: list of :class:`Volume`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listVolumes',
                  'listall':'true',
                  'domainid':self.domainid,
                  'account':self.name}

        if zone_id:
            params['zoneid'] = zone_id

        try:
            response = self.send_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                data = res['volume']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        volumes = []
        for item in data:
            # create Volume instance
            volume = Volume(self._orchestrator, item)
            volumes.append(volume)
        
        self.logger.debug('List account %s volumes: %s' % (
                          self.name, volumes))          
        
        return volumes 

    @watch
    def create_isolated_sdn(self, name, displaytext, networkoffering_id, 
                                  zone_id, networkdomain=None, 
                                  physicalnetworkid=None):
        """Create isolated network.
        
        :param str name: network name
        :param str displaytext: network displaytext
        :param str networkoffering_id: network offering id
        :param str zone_id: id of the zone
        :param str networkdomain: network domain [optional]
        :param str physicalnetworkid: physical network id [optional]        
        :return: 
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`  
        """       
        params = {'command':'createNetwork',
                  'name':name,
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'domainid':self.domainid,
                  'account':self.name}        
        
        if physicalnetworkid:
            params['physicalnetworkid'] = physicalnetworkid
        if networkdomain:
            params['networkdomain'] = networkdomain            
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = SDN(self._orchestrator, data)
            self.logger.debug('Create account %s isolated network: %s' % (
                          self.name, name))
            return net   
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def create_guest_sdn(self, name, displaytext, 
                               networkoffering_id, zone_id,
                               gateway, netmask, startip, endip, vlan,
                               networkdomain=None, physicalnetworkid=None):
        """Create guest cloudstack network
        
        :param str name: network name
        :param str displaytext: network displaytext
        :param str networkoffering_id: network offering id
        :param str zone_id: id of the zone
        :param str networkdomain: network domain [optional]
        :param str physicalnetworkid: physical network id [optional]
        :param gateway: 10.102.221.129
        :param netmask: 255.255.255.240
        :param startip: 10.102.221.130
        :param endip: 10.102.221.142
        :param vlan: 329
        """
        params = {'command':'createNetwork',
                  'name':name,
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'domainid':self.domainid,
                  'account':self.name,
                  'acltype':'account',                
                  'zoneid':zone_id,
                  'gateway':gateway,
                  'netmask':netmask,
                  'startip':startip,
                  'endip':endip,
                  'vlan':vlan}
        
        if physicalnetworkid:
            params['physicalnetworkid'] = physicalnetworkid
        if networkdomain:
            params['networkdomain'] = networkdomain        
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = SDN(self._orchestrator, data)
            self.logger.debug('Create account %s guest network: %s' % (
                          self.name, name))            
            return net            
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def create_vm(self, name, displayname, serviceofferingid, templateid,
                        zoneid, hypervisor, networkids,
                        hostid=None, diskofferingid=None, size=None, 
                        keyboard='it', startvm=True):
        """Create virtual machine.
        
        *Async command*

        :param job_id: unique id of the async job
        :param name: host name for the virtual machine
        :param displayname: an optional user generated name for the 
                            virtual machine
        :param serviceofferingid: the ID of the service offering for the 
                                  virtual machine
        :param templateid: the: ID of the template for the virtual machine
        :param zoneid: availability zone for the virtual machine
        :param projectid: Deploy vm for the project        
        :param diskofferingid: the ID of the disk offering for the virtual 
                               machine. If the template is of ISO format, the 
                               diskOfferingId is for the root disk volume. 
                               Otherwise this parameter is used to indicate the 
                               offering for the data disk volume. If the 
                               templateId parameter passed is from a Template 
                               object, the diskOfferingId refers to a DATA Disk 
                               Volume created. If the templateId parameter 
                               passed is from an ISO object, the diskOfferingId 
                               refers to a ROOT Disk Volume created.
        :param hostid: destination Host ID to deploy the VM to - parameter 
                       available for root admin only
        :param hypervisor: the hypervisor on which to deploy the virtual machine
        :param networkids: list of network ids used by virtual machine. 
                           Can't be specified with ipToNetworkList parameter        
        :param keyboard: an optional keyboard device type for the virtual 
                         machine. valid value can be one of de,de-ch,es,fi,fr,
                         fr-be,fr-ch,is,it,jp,nl-be,no,pt,uk,us
        :param keypair: name of the ssh key pair used to login to the 
                        virtual machine
        :param size: the arbitrary size for the DATADISK volume. Mutually 
                     exclusive with diskOfferingId
        :param startvm: true if network offering supports specifying ip ranges; 
                        defaulted to true if not specified
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`                         
        """        
        params = {'command':'deployVirtualMachine',
                  'name':name,
                  'displayname':displayname,
                  'serviceofferingid':serviceofferingid,
                  'templateid':templateid,
                  'zoneid':zoneid,
                  'domainid':self.domainid,
                  'account':self.name,
                  'hypervisor':hypervisor,
                  'networkids':networkids,
                  'keyboard':keyboard,
                  'startvm':startvm}
        
        if diskofferingid != None:
            params['diskofferingid'] = diskofferingid
        if size != None:
            params['size'] = size            
        if diskofferingid != None:
            params['hostid'] = hostid
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deployvirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'deployVirtualMachine', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def create_data_volume(self, name, zone_id,
                                 diskofferingid=None, 
                                 snapshotid=None,
                                 size=None,
                                 virtualmachineid=None,
                                 maxiops=None, miniops=None):
        """Create a disk volume from a disk offering. This disk volume must 
        still be attached to a virtual machine to make use of it.
        
        *Async command*
        
        :param name: the name of the disk volume
        :param zoneid: the ID of the availability zone
        :param diskofferingid: the ID of the disk offering. Either 
                               diskOfferingId or snapshotId must be passed in.
        :param snapshotid: the snapshot ID for the disk volume. Either 
                           diskOfferingId or snapshotId must be passed in.
        :param int size: Arbitrary volume size
        :param virtualmachineid: the ID of the virtual machine; to be used with 
                                 snapshot Id, VM to which the volume gets 
                                 attached after creation
        :param maxiops: max iops
        :param miniops: min iops
        
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`           
        """
        self.logger.debug('Create data volume: %s' % name)
        
        params = {'command':'createVolume',
                  'name':name,
                  'zoneid':zone_id,
                  'domainid':self.domainid,
                  'account':self.name}
        
        if diskofferingid:
            params['diskofferingid'] = diskofferingid
        if snapshotid:
            params['snapshotid'] = snapshotid            
        if size:
            params['size'] = size 
        if virtualmachineid:
            params['virtualmachineid'] = virtualmachineid 
        if maxiops:
            params['maxiops'] = maxiops 
        if miniops:
            params['miniops'] = miniops            
        
        try:
            response = self.send_request(params)
            res = json.loads(response)            
            clsk_job_id = res['createvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'createVolume', res))             
            return clsk_job_id            
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def upload_data_volume(self, name, zoneid, format, url,
                                 checksum=None, 
                                 imagestoreuuid=None):
        """Uploads a data disk.
        
        :param name: the name of the volume
        :param format: the format for the volume. Possible values include QCOW2,
                       OVA, and VHD.        
        :param url: the URL of where the volume is hosted. Possible URL include http:// and https://
        :param zoneid: the ID of the zone the volume is to be hosted on
        :param checksum: the MD5 checksum value of this volume
        :param imagestoreuuid: Image store uuid
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`           
        """
        self.logger.debug('Create data volume: %s' % name)
        
        params = {'command':'uploadVolume',
                  'name':name,
                  'zoneid':zoneid,
                  'domainid':self.domainid,
                  'account':self.name,
                  'format':format,
                  'url':url}
        
        if checksum:
            params['checksum'] = checksum
        if imagestoreuuid:
            params['imagestoreuuid'] = imagestoreuuid          
        
        try:
            response = self.send_request(params)
            res = json.loads(response)            
            clsk_job_id = res['uploadvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'uploadVolume', res))               
            return clsk_job_id            
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def list_configurations(self, page=None, pagesize=None):
        """Lists account configurations.
        
        :param page: [optional] page number to display
        :param pagesize: [optional] number of item to display per page
        :return: Dictionary with following key:
                id: the value of the configuration,
                category: the category of the configuration
                description: the description of the configuration
                name: the name of the configuration
                scope: scope(zone/cluster/pool/account) of the parameter that needs to be updated
                value: the value of the configuration        
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listConfigurations',
                  'accountid':self.id}
        
        if page:
            params['page'] = page
        if pagesize:
            params['pagesize'] = pagesize

        try:
            response = self.send_request(params)
            res = json.loads(response)['listconfigurationsresponse']['configuration']
            data = res
            self.logger.debug('Get account %s configurations: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def update_configuration(self, name, value):
        """Update account configuration.
        
        :param name: the name of the configuration
        :param value: the value of the configuration
        :return: Dictionary with following key:
                id: the value of the configuration,
                category: the category of the configuration
                description: the description of the configuration
                name: the name of the configuration
                scope: scope(zone/cluster/pool/account) of the parameter that needs to be updated
                value: the value of the configuration        
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateConfiguration',
                  'name':name,
                  'value':value,
                  'accountid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['updateconfigurationresponse']['configuration']
            data = res
            self.logger.debug('Set account %s configuration: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data        