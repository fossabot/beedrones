'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .account import Account
from .domain import Domain
from .zone import Zone
from .region import Region
from .pod import Pod
from .host import Host
from .network import Network
from .virtual_machine import VirtualMachine
from .virtual_router import VirtualRouter
from .template import Template
from .iso import Iso
from .volume import Volume
from .offering import ServiceOffering, NetworkOffering, DiskOffering
from .storagepool import StoragePool

class System(ClskObject):
    def __init__(self, api_client, name=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=None, oid=oid)
        
        self._name = name
        self._id = oid
        self._obj_type = 'system'

    def get_cloud_identifier(self, userid):
        '''Get cloud identifier'''
        params = {'command':'getCloudIdentifier',
                  'userid':userid,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['getcloudidentifierresponse']['cloudidentifier']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

        return data

    def list_apis(self):
        '''List all regions'''
        params = {'command':'listApis'
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listapisresponse']['api']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

        return data
    
    def list_regions(self):
        '''List all regions'''
        params = {'command':'listRegions',
                  'listAll':'true'
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listregionsresponse']['region']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

        regions = []
        for item in data:
            # create Account instance
            region = Region(self._api_client, item)
            regions.append(region)   
        return regions

    def list_zones(self):
        '''List all zones'''
        params = {'command':'listZones',
                  'listAll':'true'
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listzonesresponse']['zone']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        zones = []
        for item in data:
            # create Account instance
            zone = Zone(self._api_client, item)
            zones.append(zone)
        return zones      

    def list_pods(self):
        '''List all pods'''
        params = {'command':'listPods',
                  'listAll':'true'
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listpodsresponse']['pod']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        pods = []
        for item in data:
            # create Account instance
            pod = Pod(self._api_client, item)
            pods.append(pod)
        return pods  

    def list_clusters(self):
        '''List all clusters'''
        params = {'command':'listClusters',
                  'listAll':'true'
                 }
        
        response = self._api_client.send_api_request(params)

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listclustersresponse']['cluster']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        clusters = []
        for item in data:
            # create Account instance
            cluster = Pod(self._api_client, item)
            clusters.append(cluster)
        return clusters       

    def list_hosts(self, oid=None, name=None, zoneid=None, podid=None, 
                         clusterid=None, resourcestate='Enabled',
                         virtualmachineid=None, htype=None):
        '''List all hosts
        
        :param oid: id of the host
        :param name: name of the host
        :param zoneid: zone id of the host
        :param podid: pod id of the host
        :param clusterid: cluster id of the host
        :param resourcestate: list hosts by resource state. Resource state 
                              represents current state determined by admin of 
                              host, valule can be one of [Enabled, Disabled, 
                              Unmanaged, PrepareForMaintenance, ErrorInMaintenance, 
                              Maintenance, Error]
        :param virtualmachineid: lists hosts in the same cluster as this VM and 
                                 flag hosts with enough CPU/RAm to host this VM
        :param htype: type of host
        '''
        params = {'command':'listHosts',
                  'listAll':'true'
                 }

        if oid:
            params['id'] = oid
        if name:
            params['name'] = name
        if zoneid:
            params['zoneid'] = zoneid
        if podid:
            params['podid'] = podid
        if clusterid:
            params['clusterid'] = clusterid            
        if resourcestate:
            params['resourcestate'] = resourcestate
        if virtualmachineid:
            params['virtualmachineid'] = virtualmachineid
        if htype:
            params['type'] = htype                        

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listhostsresponse']['host']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._api_client, item)
            hosts.append(host)
        return hosts 

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
            storagepool = StoragePool(self._api_client, item)
            storagepools.append(storagepool)
        return storagepools

    def list_imagestores(self):
        '''List all image stores'''
        params = {'command':'listImageStores',
                  'listAll':'true'
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listimagestoresresponse']['imagestore']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        '''
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._api_client, item)
            hosts.append(host)
        return hosts
        '''
    
    def list_system_vms(self):
        '''List all system vms'''
        params = {'command':'listSystemVms',
                  'listAll':'true'
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listsystemvmsresponse']['systemvm']
            data = res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, data=item)
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
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualRouter(self._api_client, data=item)
            vms.append(vm)
        return vms

    def list_virtual_machines(self):
        '''List all virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'listall':'true',
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._api_client, data=item)
            vms.append(vm)
        return vms

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
            # create Volume instance
            volume = Volume(self._api_client, item)
            volumes.append(volume)
        
        return volumes 
        
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
        if domain:
            params['domainid'] = self.get_domain_id(domain)
        if domain_id:
            params['domainid'] = domain_id
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
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        networks = []
        for item in data:
            # create Network instance
            network = Network(self._api_client, item)
            networks.append(network)
        
        return networks 

    def list_physical_networks(self, pnid=None, name=None, zone_id=None, ):
        '''List physical networks.
        
        :param pnid: [optional] physical network id
        :param name: [optional] physical network name
        :param zone_id: [optional] id of the zone
        
        Return:
        
        [{u'name': u'cloudbr0', 
          u'broadcastdomainrange': u'ZONE', 
          u'state': u'Enabled', 
          u'zoneid': u'2af97976-9679-427b-8dbd-6b11f9dfa169', 
          u'isolationmethods': u'VLAN', 
          u'id': u'5b72e792-bb66-4fad-9e16-8f4f7c290a07'}, 
         {u'name': u'cloudbr1', 
          u'broadcastdomainrange': u'ZONE', 
          u'vlan': u'1200-1204', 
          u'isolationmethods': u'VLAN', 
          u'zoneid': u'2af97976-9679-427b-8dbd-6b11f9dfa169', 
          u'state': u'Enabled', 
          u'id': u'c0bdc2a5-a222-49cf-a11a-98ff886ee210'}]        
        '''
        params = {'command':'listPhysicalNetworks',
                  'listall':'true'}

        if pnid:
            params['id'] = pnid  
        if name:
            params['name'] = name  
        if zone_id:
            params['zoneid'] = zone_id

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listphysicalnetworksresponse']
            if len(res) > 0:
                data = res['physicalnetwork']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        return data

    def list_remote_access_vpns(self, networkid=None, publicipid=None,
                                       domainid=None, account=None):
        '''List remote access vpn.
        
        :param networkid: [optional] list remote access VPNs for ceratin network
        :param publicipid: [optional] public ip address id of the vpn server
        :param domainid: [optional] list only resources belonging to the domain specified
        :param account: [optional]list resources by account. Must be used with the domainId parameter.
        
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
                  'listall':'true'}

        if domainid:
            params['domainid'] = domainid
        if account:
            params['account'] = account
        if networkid:
            params['networkid'] = networkid
        if publicipid:
            params['publicipid'] = publicipid

        try:
            response = self._api_client.send_api_request(params)
            print response
            res = json.loads(response)['listremoteaccessvpnsresponse']
            if len(res) > 0:
                data = res['remoteaccessvpn']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        return data

    def list_public_ip_addresses(self, ipaddressid=None, ipaddress=None, zone_id=None, 
                                       domainid=None, account=None):
        '''List public Ip Addresses.
        
        :param ipaddressid: [optional] Ip Address id
        :param ipaddress: [optional] lists the specified IP address
        :param zone_id: [optional] id of the zone
        :param domainid: [optional] list only resources belonging to the domain specified
        :param account: [optional]list resources by account. Must be used with the domainId parameter.
        
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
                  'allocatedonly':'true'}

        if zone_id:
            params['zoneid'] = zone_id
        if domainid:
            params['domainid'] = domainid
        if account:
            params['account'] = account
        if ipaddressid:
            params['ipid'] = ipaddressid
        if ipaddress:
            params['ipaddress'] = ipaddress

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listpublicipaddressesresponse']
            if len(res) > 0:
                data = res['publicipaddress']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        return data

    def list_templates(self, zoneid=None, hypervisor=None):
        '''List all templates.'''
        params = {'command':'listTemplates',
                  'listall':'true',
                  'templatefilter':'all',
                 }
        
        if zoneid:
            params['zoneid'] = zoneid
        if hypervisor:
            params['hypervisor'] = hypervisor

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listtemplatesresponse']
            if len(res) > 0:
                data = res['template']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        templates = []
        for item in data:
            # create Template instance
            template = Template(self._api_client, item)
            templates.append(template)
        
        return templates

    def list_isos(self, zoneid=None, hypervisor=None):
        '''List all isos.'''
        params = {'command':'listIsos',
                  'listall':'true',
                  'isofilter':'all',
                 }
        
        if zoneid:
            params['zoneid'] = zoneid
        if hypervisor:
            params['hypervisor'] = hypervisor

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listisosresponse']
            if len(res) > 0:
                data = res['iso']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        isos = []
        for item in data:
            # create Iso instance
            iso = Iso(self._api_client, item)
            isos.append(iso)
        
        return isos

    def list_domains(self, domain_id=None):
        ''' list domains'''

        params = {'command':'listDomains',
                  'listall':'true',}
        
        if domain_id:
            params['id'] = domain_id
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listdomainsresponse']
            if len(res) > 0:
                data = res['domain']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        domains = []
        for item in data:
            # create Account instance
            domain = Domain(self._api_client, item)
            domains.append(domain)
        
        return domains

    def list_accounts(self, domain=None, domain_id=None, account=None):
        '''List all accounts

        :param domain: full domain path like ROOT/CSI/dc
        :param domain_id: id of the domain the account belongs. This param and
                          domain are mutually exclusive
        '''
        params = {'command':'listAccounts',
                  'listall':'true'}
        
        if domain:
            try:
                params['domainid'] = self.get_domain_id(domain)
            except ApiError as ex:
                raise ClskObjectError(ex)
        if domain_id:
            params['domainid'] = domain_id
        if account:
            params['name'] = account
            
        self.logger.debug("Get account list: %s" % params)

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listaccountsresponse']
            if len(res) > 0:
                data = res['account']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        accounts = []
        for item in data:
            # create Account instance
            account = Account(self._api_client, item)
            accounts.append(account)
        
        return accounts        

    def list_service_offerings(self):
        '''List all accounts'''
        params = {'command':'listServiceOfferings',
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listserviceofferingsresponse']
            if len(res) > 0:
                data = res['serviceoffering']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        serviceofferings = []
        for item in data:
            serviceoffering = ServiceOffering(self._api_client, item)
            serviceofferings.append(serviceoffering)
        
        return serviceofferings
    
    def list_network_offerings(self):
        '''List all accounts'''
        params = {'command':'listNetworkOfferings',
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listnetworkofferingsresponse']
            if len(res) > 0:
                data = res['networkoffering']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        networkofferings = []
        for item in data:
            networkoffering = NetworkOffering(self._api_client, item)
            networkofferings.append(networkoffering)
        
        return networkofferings    

    def list_disk_offerings(self):
        '''List all accounts'''
        params = {'command':'listDiskOfferings',
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listdiskofferingsresponse']
            if len(res) > 0:
                data = res['diskoffering']
            else:
                return []
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        diskofferings = []
        for item in data:
            diskoffering = DiskOffering(self._api_client, item)
            diskofferings.append(diskoffering)
        
        return diskofferings

    # tree object
    def physical_tree(self):
        '''Return physical tree.'''
        system = {'name':self._name, 
                  'id':self._id, 
                  'type':self._obj_type, 
                  'childs':[]}
        for zone in self.list_zones():
            system['childs'].append(zone.tree())
        return system

    def logical_tree(self):
        '''Return logical tree.'''
        system = {'name':self._name, 
                  'id':self._id, 
                  'type':self._obj_type, 
                  'childs':[]}
        for domain in self.list_domains():
            system['childs'].append(domain.tree())
        return system
    
    def network_tree(self):
        '''Return network tree.'''
        system = {'name':self._name, 
                  'id':self._id, 
                  'type':self._obj_type, 
                  'childs':[]}
        for network in self.list_networks():
            system['childs'].append(network.tree())
        return system

    # create object
    def create_domain(self, name, parent_domain_id=None):
        '''Create domain 
        
        :param name: full domain path like ROOT/CSI/dc
        '''
        params = {'command':'createDomain',
                  'name':name,
                 }
        if parent_domain_id:
            params['parentdomainid'] = parent_domain_id
        
        try:
            response = self._api_client.send_api_request(params)
            data = json.loads(response)['createdomainresponse']['domain']
            
            # create Account instance
            domain = Domain(self._api_client, data) 
            
            return domain
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def create_vm(self, job_id, name, displayname, serviceofferingid, templateid,
                        zoneid, domainid, account, hypervisor, networkids,
                        hostid=None, diskofferingid=None, size=None, keyboard='it'):
        """Create virtual machine.
        Async command.

        :param job_id: unique id of the async job
        :param name: host name for the virtual machine
        :param displayname: an optional user generated name for the virtual machine        
        
        :param serviceofferingid: the ID of the service offering for the virtual machine
        :param templateid: the: ID of the template for the virtual machine
        
        :param zoneid: availability zone for the virtual machine
        :param domainid: an optional domainId for the virtual machine. If the account parameter is used, domainId must also be used.        
        :param account: an optional account for the virtual machine. Must be used with domainId.
        :param projectid: Deploy vm for the project        
        
        :param diskofferingid: the ID of the disk offering for the virtual machine. If the template is of ISO format, the diskOfferingId is for the root disk volume. Otherwise this parameter is used to indicate the offering for the data disk volume. If the templateId parameter passed is from a Template object, the diskOfferingId refers to a DATA Disk Volume created. If the templateId parameter passed is from an ISO object, the diskOfferingId refers to a ROOT Disk Volume created.

        :param hostid: destination Host ID to deploy the VM to - parameter available for root admin only
        :param hypervisor: the hypervisor on which to deploy the virtual machine
        :param networkids: list of network ids used by virtual machine. Can't be specified with ipToNetworkList parameter        
        
        :param keyboard: an optional keyboard device type for the virtual machine. valid value can be one of de,de-ch,es,fi,fr,fr-be,fr-ch,is,it,jp,nl-be,no,pt,uk,us
        :param keypair: name of the ssh key pair used to login to the virtual machine

        :param size: the arbitrary size for the DATADISK volume. Mutually exclusive with diskOfferingId
        :param startvm: true if network offering supports specifying ip ranges; defaulted to true if not specified
        """        
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
        
        if diskofferingid != None:
            params['diskofferingid'] = diskofferingid
        if size != None:
            params['size'] = size            
        if diskofferingid != None:
            params['hostid'] = hostid
            
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['deployvirtualmachineresponse']['jobid']
            data = self._api_client.query_async_job(job_id, clsk_job_id)['jobresult']['virtualmachine']
            #virtualmachine
            vm = VirtualMachine(self._api_client, data)
            self.logger.debug('Default cloudstack virtual machine was created: %s' % name)
            return vm
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

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
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = Network(self._api_client, data=data)
            self.logger.debug('Private cloudstack network was created: %s' % name)
            return net   
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def create_hybrid_network(self, name, displaytext, 
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
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = Network(self._api_client, data=data)
            self.logger.debug('Hybrid cloudstack network was created: %s' % name)
            return net            
        except KeyError as ex :
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def get_domain_id(self, path):
        '''Get id for the domain specified.
        
        :param path: full domain path like ROOT/CSI/dc
        '''
        self.logger.debug("Get domain id for domain: %s" % path)
        
        name = path.split('/')[-1]
        params = {'command':'listDomains',
                  'name':name,
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            data = json.loads(response)['listdomainsresponse']['domain']
            domain_id = [d['id'] for d in data if str(d['path']) == path][0]
            return domain_id
        except (KeyError, IndexError):
            raise ClskObjectError('Domain %s does not exist' % path)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def get_account_id(self, domainid, name):
        '''Get id for the account specified.
        
        :param name: name of the account
        '''
        self.logger.debug("Get acoount id for account: %s %s" % (domainid, name))
        
        params = {'command':'listAccounts',
                  'domainid':domainid,
                  'name':name,
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            data = json.loads(response)['listaccountsresponse']['account'][0]
            return data['id']
        except (KeyError, TypeError):
            raise ClskObjectError('Account %s.%s does not exist' % (domainid, name))
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def get_domain_path(self, domain_id):
        """ """
        # get virtual machine domain path
        params = {'command':'listDomains',
                  'id':domain_id}
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listdomainsresponse']['domain'][0]
            return res['path']
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)          