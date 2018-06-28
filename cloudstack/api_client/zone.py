"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .pod import Pod
from .cluster import Cluster
from .host import Host

class Zone(ClskObject):
    """Zone api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'zone'

    '''
    @watch
    def info(self):
        """Cloudstack zone configuration. Invoke cloudstack api to get data and 
        refresh network configuration. 
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listZones',
                  'id':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listzonesresponse']['zone'][0]
            self._data = res
            self.logger.debug('Get zone %s description' % self)
            return self._data
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
    '''

    @watch
    def update(self, name=None, details=None, dhcpprovider=None, 
                     dns1=None, dns2=None, ip6dns1=None, ip6dns2=None,
                     dnssearchorder=None, internaldns1=None, internaldns2=None, 
                     domain=None, guestcidraddress=None, ispublic=None, 
                     localstorageenabled=None, allocationstate=None):
        """Update a zone.
        

        :param name: the name of the Zone
        :param details: the details for the Zone
        :param dhcpprovider: the dhcp Provider for the Zone
        :param dns1: the first DNS for the Zone
        :param dns2: the second DNS for the Zone
        :param ip6dns1: the first DNS for IPv6 network in the Zone
        :param ip6dns2: the second DNS for IPv6 network in the Zone        
        :param dnssearchorder: the dns search order list
        :param internaldns1: the first internal DNS for the Zone
        :param internaldns2: the second internal DNS for the Zone        
        :param domain: Network domain name for the networks in the zone; empty 
                       string will update domain with NULL value
        :param guestcidraddress: the guest CIDR address for the Zone
        :param ispublic: updates a private zone to public if set, but not vice-versa
        :param localstorageenabled: true if local storage offering enabled, 
                                    false otherwise
        :param allocationstate: Allocation state of this cluster for allocation 
                                of new resources [optional]                                    
        :return: Dictionary with all zone configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateZone',
                  'id':self.id}

        if name:
            params['name'] = name
        if details:
            params['details'] = details
        if dhcpprovider:
            params['dhcpprovider'] = dhcpprovider            
        if dns1:
            params['dns1'] = dns1        
        if dns2:
            params['dns2'] = dns2
        if ip6dns1:
            params['ip6dns1'] = ip6dns1        
        if ip6dns2:
            params['ip6dns2'] = ip6dns2
        if dnssearchorder:
            params['dnssearchorder'] = dnssearchorder        
        if internaldns1:
            params['internaldns1'] = internaldns1
        if internaldns2:
            params['internaldns2'] = internaldns2        
        if domain:
            params['domain'] = domain
        if guestcidraddress:
            params['guestcidraddress'] = guestcidraddress        
        if ispublic:
            params['ispublic'] = ispublic
        if localstorageenabled:
            params['localstorageenabled'] = localstorageenabled        
        if allocationstate:
            params['allocationstate'] = allocationstate

        try:
            response = self.send_request(params)
            res = json.loads(response)['updatezoneresponse']['cluster'][0]
            self._data = res
            self.logger.debug('Update zone %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    
    @watch
    def delete(self):
        """Deletes a zone.
        
        :return: True if operation is executed successfully
        :rtype: bool        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'deleteZone',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['deletezoneresponse']['success']
            self._data = res
            self.logger.debug('Delete zone %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def tree(self):
        """Zone tree.
        
        :return: Dictionary zone tree.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        """
        zone = {'name':self.name,
                'id':self.id, 
                'type':self._obj_type, 
                'childs':[]}        
        for pod in self.list_pods():
            zone['childs'].append(pod.tree())
            
        self.logger.debug('Get zone %s tree' % self.name)
        return zone

    @watch
    def list_pods(self):
        """List zone pods.
        
        :return: List with pods.
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listPods',
                  'listAll':'true',
                  'zoneid':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listpodsresponse']['pod']
            data = res
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        pods = []
        for item in data:
            # create Account instance
            pod = Pod(self._orchestrator, item)
            pods.append(pod)
            
        self.logger.debug('Get zone %s pods: %s' % (self.name, pods))
        return pods

    @watch
    def add_pod(self, name, startip, endip, gateway, netmask,
                      allocationstate=None):
        """Creates a new Pod.
        
        :param name: the name of the Pod
        :param startip: the starting IP address for the Pod
        :param endip: the ending IP address for the Pod
        :param gateway: the gateway for the Pod
        :param netmask: the netmask for the Pod
        :param allocationstate: Allocation state of this Pod for allocation of 
                                new resources [optional]
        :return: Object of type :class:`.pod.Pod`
        :rtype: :class:`.host.Host`      
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'createPod',
                  'zoneid':self.id,
                  'name':name,
                  'startip':startip,
                  'endip':endip,
                  'gateway':gateway,
                  'netmask':netmask}

        if allocationstate:
            params['allocationstate'] = allocationstate     

        try:
            response = self.send_request(params)
            data = json.loads(response)['createpodresponse']['host']
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        pod = Pod(self, data)
        
        self.logger.debug('Add pod %s to zone %s' % (pod, self))
        return pod

    @watch
    def list_clusters(self):
        """List zone clusters.
        
        :return: List with clusters.
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listClusters',
                  'listAll':'true',
                  'zoneid':self.id}
        
        response = self.send_request(params)

        try:
            response = self.send_request(params)
            res = json.loads(response)['listclustersresponse']['cluster']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        clusters = []
        for item in data:
            # create Account instance
            cluster = Cluster(self._orchestrator, item)
            clusters.append(cluster)
            
        self.logger.debug('Get zone %s clusters: %s' % (self.name, clusters))
        return clusters 

    @watch
    def list_hosts(self):
        """List zone hosts.
        
        :return: List with hosts.
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listHosts',
                  'listAll':'true',
                  'zoneid':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listhostsresponse']['host']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._orchestrator, item)
            hosts.append(host)
            
        self.logger.debug('Get zone %s hosts: %s' % (self.name, hosts))
        return hosts

    @watch
    def list_hypervisors(self):
        """List zone hypervisors.
        
        :return: List with hypervisors.
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listHypervisors',
                  'zoneid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listhypervisorsresponse']['hypervisor']
            data = res
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)

        self.logger.debug('Get zone %s hypervisors: %s' % (self.name, data))
        return data
    
    @watch
    def list_hypervisor_capabilities(self, hypervisor=None):
        """List hypervisor capabilities.
        
        :param str hypervisor: the hypervisor for which to restrict the search
        :return: List with hypervisor capabilities.
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listHypervisorCapabilities'}

        if hypervisor:
            params['hypervisor'] = hypervisor

        try:
            response = self.send_request(params)
            res = json.loads(response)['listhypervisorcapabilitiesresponse']['hypervisorCapabilities']
            data = res
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)

        self.logger.debug('Get hypervisor capabilities: %s' % (data))
        return data
    
    @watch
    def list_configurations(self, page=None, pagesize=None):
        """Lists zone configurations.
        
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
                  'zoneid':self.id}
        
        if page:
            params['page'] = page
        if pagesize:
            params['pagesize'] = pagesize

        try:
            response = self.send_request(params)
            res = json.loads(response)['listconfigurationsresponse']['configuration']
            data = res
            self.logger.debug('Get zone %s configurations: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def update_configuration(self, name, value):
        """Update zone configuration.
        
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
                  'zoneid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['updateconfigurationresponse']['configuration']
            data = res
            self.logger.debug('Set zone %s configuration: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data
    
    @watch
    def list_vmware_dcs(self):
        """Retrieves VMware DC(s) associated with a zone.
        
        :return: List with VMware DC(s).
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listVmwareDcs',
                  'zoneid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listvmwaredcsresponse']['vmwaredc']
            data = res
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)

        self.logger.debug('Get zone %s vmwaredcs: %s' % (self, data))
        return data

    @watch
    def add_vmware_dc(self, name, vcenter, username, password):
        """Adds a VMware datacenter to specified zone.
        
        :param name: Name of VMware datacenter to be added to specified zone.
        :param vcenter: The name/ip of vCenter. Make sure it is IP address or 
                        full qualified domain name for host running vCenter server.
        :param username: The Username required to connect to resource.
        :param password: The password for specified username.
        :return: Dictionary with following key:
                 id: The VMware Datacenter ID
                 name: The VMware Datacenter name
                 vcenter: The VMware vCenter name/ip
                 zoneid: the Zone ID associated with this VMware Datacenter
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'addVmwareDc',
                  'zoneid':self.id,
                  'name':name,
                  'vcenter':vcenter,
                  'username':username,
                  'password':password}

        try:
            response = self.send_request(params)
            res = json.loads(response)['addvmwaredcresponse']['vmwaredc']
            data = res
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)

        self.logger.debug('Add vmwaredc %s to zone %s' % (data, self))
        return data

    @watch
    def remove_vmware_dc(self):
        """Remove a VMware datacenter from a zone.
        
        :return: True if operation is executed successfully
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'removeVmwareDc',
                  'zoneid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['removevmwaredcresponse']['success']
            data = res
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)

        self.logger.debug('Get zone %s vmwaredcs: %s' % (self, data))
        return data