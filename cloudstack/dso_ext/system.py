'''
Created on Jul 29, 2013

@author: darkbk
'''
import json
from gibboncloud.cloudstack.dso.system import System
from gibboncloud.cloudstack.dso.base import ClskObjectError
from gibboncloud.cloudstack.dso.base import ApiError
from .virtual_machine import VirtualMachineExt
from .virtual_router import VirtualRouterExt
from .network import NetworkExt
from .volume import VolumeExt
from .storagepool import StoragePoolExt
    
class SystemExt(System):
    """This class extend original system api and implement all the action that 
    use cloudstack api and hypervisor api to complete operation not provided, 
    actually, by base cloudstack api
    """
    def __init__(self, clsk_instance, clsk_id):
        """
        """
        self.clsk_instance = clsk_instance
        
        api_client = clsk_instance.get_api_client()
        System.__init__(self, api_client, oid=clsk_id)
    
    def list_system_vms(self):
        '''List all system vms'''
        params = {'command':'listSystemVms',
                  'listAll':'true'
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listsystemvmsresponse']
            if len(res) > 0:
                data = res['systemvm']
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
            vm = VirtualMachineExt(self.clsk_instance, data=item)
            vms.append(vm)
        return vms

    def list_routers(self):
        '''List all routers'''
        params = {'command':'listRouters',
                  'listAll':'true'
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
            vm = VirtualRouterExt(self.clsk_instance, data=item)
            vms.append(vm)
        return vms

    def list_virtual_machines(self, domain=None, account=None, vm_id=None):
        '''List all virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'listall':'true',
                 }

        if domain:
            try:
                params['domainid'] = self.get_domain_id(domain)
            except ApiError as ex:
                raise ClskObjectError(ex)
        if account:
            params['account'] = account
        if vm_id:
            params['id'] = vm_id            
        
        try:
            response = self._api_client.send_api_request(params)
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
            vm = VirtualMachineExt(self.clsk_instance, data=item)
            vms.append(vm)
        return vms
    
    def list_networks(self, zone_id=None, domain=None, domain_id=None,
                            account=None, net_id=None):
        '''List network.
        
        :param zone_id: [optional] id of the zone
        :param domain_id: [optional] id of the domain        
        :param domain: [optional] name of the domain
        :param account: [optional] name of the account
        :param net_id: [optional] id of the network
        '''
        params = {'command':'listNetworks',
                  'listall':'true'}

        if zone_id:
            params['zoneid'] = zone_id
        if domain_id:
            params['domainid'] = domain_id
        if domain:
            params['domainid'] = self.get_domain_id(domain)
        if account:
            params['account'] = account
        if net_id:
            params['id'] = net_id

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listnetworksresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        networks = []
        for item in data:
            # create Account instance
            network = NetworkExt(self.clsk_instance, data=item)
            networks.append(network)
        
        return networks    

    def list_volumes(self, zone_id=None, domain=None, domain_id=None,
                           account=None, vol_id=None):
        '''List volumes.

        :param zone_id: [optional] id of the zone
        :param domain_id: [optional] id of the domain
        :param domain: [optional] name of the domain
        :param account: [optional] name of the account
        :param vole_id: [optional] id of the volume        
        '''
        params = {'command':'listVolumes',
                  'listall':'true'}

        if zone_id:
            params['zoneid'] = zone_id  
        if domain:
            params['domainid'] = self.get_domain_id(domain)
        if domain_id:
            params['domainid'] = domain_id
        if account:
            params['account'] = account
        if vol_id:
            params['id'] = vol_id

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
            # create Network instance
            volume = VolumeExt(self.clsk_instance, data=item)
            volumes.append(volume)
        
        return volumes 

    def list_tenants(self):
        '''List all tenants 
        tenant syntax: <cloudsatck_id>.<domain_path>.<account>
        Ex. clsk42.ROOT/CSI/DC.test1
        '''
        params = {'command':'listAccounts',
                  'listall':'true'}

        tenants_list = []
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listaccountsresponse']
            if len(res) > 0:
                accounts = res['account']
                for account in accounts:
                    domain_path = self.get_domain_path(account['domainid'])
                    #domain = account['domain']
                    #if domain != 'ROOT':
                    #    domain = "ROOT/%s" % domain
                        
                    tenant = "%s.%s.%s" % (self.clsk_instance.name, 
                                           domain_path, 
                                           account['name'])
                    tenants_list.append(tenant)
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        return tenants_list       
    
    def list_storagepools(self, zoneid=None, name=None):
        '''List all storage pools.'''
        params = {'command':'listStoragePools'}
        
        if zoneid:
            params['zoneid'] = zoneid
        if name:
            params['name'] = name            
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['liststoragepoolsresponse']['storagepool']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        storagepools = []
        for item in data:
            # create StoragePool instance
            storagepool = StoragePoolExt(self.clsk_instance, data=item)
            storagepools.append(storagepool)
        return storagepools    
    
    # create object
    def create_vm(self, job_id, name, displayname, serviceofferingid, 
                        templateid, zoneid, domain, account, hypervisor, 
                        networkids, devices=None, hostid=None, 
                        diskofferingid=None, size=None, keyboard='it'):
        """Create virtual machine.
        Async command.

        TO-DO : extend to support vmware virtual machine

        :param job_id: unique id of the async job
        :param name: host name for the virtual machine
        :param displayname: an optional user generated name for the 
                            virtual machine
        :param serviceofferingid: the ID of the service offering for the 
                                  virtual machine
        :param templateid: the: ID of the template for the virtual machine
        :param zoneid: availability zone for the virtual machine
        :param domain: an optional domain for the virtual machine. If the 
                       account parameter is used, domain must also be used.        
        :param account: an optional account for the virtual machine. 
                        Must be used with domainId.
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
        :param devices: dict with additional devices : {'spice_graphics':''}
                        spice_graphics, vnc_graphics, rdp_graphics, 
                        video_cirrus, video_qxl,
                        virtio_serial, usb_redirect,
                        sound_card_ac97, sound_card_es1370, 
                        sound_card_sb16, sound_card_ich6
        """
        self.logger.info('Create new extended virtual machine - START')
        
        # get domain id
        domainid = self.get_domain_id(domain)
        
        # create vm with cloudstack api
        params = {'command':'deployVirtualMachine',
                  'name':name,
                  'displayname':displayname,
                  'serviceofferingid':serviceofferingid,
                  'templateid':templateid,
                  'zoneid':zoneid,
                  'domainid':domainid,
                  'account':account,
                  'hypervisor':hypervisor,
                  'networkids':networkids,
                  'keyboard':keyboard,
                  'startvm':'true',
                 }
        
        # the ID of the disk offering for the virtual machine. If the template 
        # is of ISO format, the diskOfferingId is for the root disk volume. 
        # Otherwise this parameter is used to indicate the offering for 
        # the data disk volume
        if diskofferingid != None:
            params['diskofferingid'] = diskofferingid
        # the arbitrary size for the DATADISK volume. Mutually exclusive with 
        # diskOfferingId
        if size != None:
            params['size'] = size
        # destination Host ID to deploy the VM to
        if hostid != None:
            params['hostid'] = hostid
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)

            clsk_job_id = res['deployvirtualmachineresponse']['jobid']
            data = self._api_client.query_async_job(job_id, clsk_job_id)['virtualmachine']

            # create virtualmachine object
            vm = VirtualMachineExt(self.clsk_instance, data=data)
            self.logger.debug('Default cloudstack virtual machine was created: %s' % name)
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        # append devices
        vm.append_device(devices)
        
        self.logger.info('Create new extended virtual machine - STOP')
        return vm
    
    def create_private_network(self, name, displaytext, 
                                     networkoffering_id, zone_id,
                                     domain_id=None, domain=None, account=None,
                                     networkdomain=None, 
                                     physicalnetworkid=None):
        '''Create private network.
        
        
        '''       
        params = {'command':'createNetwork',
                  'name':name,
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'acltype':'Account',
                 }
        
        if domain:
            params['domainid'] = self.get_domain_id(domain)
        elif domain_id:
            params['domainid'] = domain_id
        if account:
            params['account'] = account
        if physicalnetworkid:
            params['physicalnetworkid'] = physicalnetworkid
        if networkdomain:
            params['networkdomain'] = networkdomain            
        
        try:
            self._api_client.set_timeout(120)
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = NetworkExt(self.clsk_instance, data=data)
            self.logger.debug('Private cloudstack network was created: %s' % name)
            return net   
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
    def create_external_network(self, name, displaytext, 
                                      networkoffering_id, zone_id,
                                      gateway, netmask, startip, endip, vlan, 
                                      domain_id=None, domain=None, account=None,
                                      networkdomain=None, shared=False,
                                      physicalnetworkid=None):
        '''Create diretc network for the account
        
        :param shared: True set network shared for all account in the domain.
                       False set network isolated to account. 
        :param gateway: 10.102.221.129
        :param netmask: 255.255.255.240
        :param startip: 10.102.221.130
        :param endip: 10.102.221.142
        :param vlan: 329
        '''
        params = {'command':'createNetwork',
                  'name':name,
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'gateway':gateway,
                  'netmask':netmask,
                  'startip':startip,
                  'endip':endip,
                  'vlan':vlan,
                 }
        
        # set shared status of the network
        if shared:
            params['acltype'] = 'Domain'
        else:
            params['acltype'] = 'Account'
            
        if domain:
            params['domainid'] = self.get_domain_id(domain)
        elif domain_id:
            params['domainid'] = domain_id
        if account:
            params['account'] = account
        if physicalnetworkid:
            params['physicalnetworkid'] = physicalnetworkid
        if networkdomain:
            params['networkdomain'] = networkdomain
        
        try:
            self._api_client.set_timeout(120)
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = NetworkExt(self.clsk_instance, data=data)
            self.logger.debug('Hybrid cloudstack network was created: %s' % name)
            return net            
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
