"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .host import Host

class Cluster(ClskObject):
    """Cluster api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'cluster'

    def get_zone(self):
        return self._data['zoneid']

    def get_pod(self):
        return self._data['podid']

    @watch
    def update(self, allocationstate=None, clustername=None, clustertype=None,
                     hypervisor=None, managedstate=None):
        """Update cluster.
        
        :param allocationstate: Allocation state of this cluster for allocation 
                                of new resources
        :param clustername: the cluster name
        :param clustertype: hypervisor type of the cluster
        :param hypervisor: hypervisor type of the cluster
        :param managedstate: whether this cluster is managed by cloudstack
        :return: Dictionary with all cluster configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateCluster',
                  'id':self.id}
        
        if allocationstate:
            params['allocationstate'] = allocationstate
        if clustername:
            params['clustername'] = clustername
        if clustertype:
            params['clustertype'] = clustertype
        if hypervisor:
            params['hypervisor'] = hypervisor            
        if managedstate:
            params['managedstate'] = managedstate        

        try:
            response = self.send_request(params)
            res = json.loads(response)['updateclusterresponse']['cluster'][0]
            self._data = res
            self.logger.debug('Update cluster %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete(self):
        """Deletes a cluster.
        
        :return: True if operation is executed successfully
        :rtype: bool        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'deleteCluster',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['deleteclusterresponse']['success']
            self._data = res
            self.logger.debug('Delete cluster %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def tree(self):
        """Return cluster tree."""
        cluster = {'name':self.name, 'id':self.id, 'childs':[]}
        for host in self.list_hosts():
            cluster['childs'].append(host.tree())
        return cluster

    @watch
    def list_hosts(self):
        """List hosts.
        
        :return: Lis of :class:`.host.Host`
        :rtype: List     
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'listHosts',
                  'listAll':'true',
                  'clusterid':self.id}

        try:
            response = self.send_request(params)
            print response
            res = json.loads(response)['listhostsresponse']
            if len(res) > 0:
                data = res['host']
            else:
                data = []
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._orchestrator, item)
            hosts.append(host)
        
        self.logger.debug('List cluster %s hosts: %s' % (self.id, hosts))
        return hosts

    @watch
    def add_host(self, hypervisor, url, username, password, 
                       allocationstate=None, hosttags=None):
        """Adds a new host.
        
        :param hypervisor: hypervisor type of the host
        :param url: the host URL
        :param username: the username for the host
        :param password: the password for the host
        :param allocationstate: Allocation state of this Host for allocation of 
                                new resources [optional]
        :param hosttags: list of tags to be added to the host 
        :return: Object of type :class:`.host.Host`
        :rtype: :class:`.host.Host`      
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'addHost',
                  'zoneid':self.get_zone(),
                  'podid':self.get_pod(),
                  'clusterid':self.id,
                  'hypervisor':hypervisor,
                  'url':url,
                  'username':username,
                  'password':password}

        if allocationstate:
            params['allocationstate'] = allocationstate
        if hosttags:
            params['hosttags'] = hosttags        

        try:
            response = self.send_request(params)
            data = json.loads(response)['addhostresponse']['host']
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        host = Host(self._orchestrator, data)
        
        self.logger.debug('Add host %s to cluster %s' % (host, self))
        return host

    @watch
    def list_configurations(self, page=None, pagesize=None):
        """Lists cluster configurations.
        
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
                  'clusterid':self.id}
        
        if page:
            params['page'] = page
        if pagesize:
            params['pagesize'] = pagesize

        try:
            response = self.send_request(params)
            res = json.loads(response)['listconfigurationsresponse']['configuration']
            data = res
            self.logger.debug('Get cluster %s configurations: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def update_configuration(self, name, value):
        """Update cluster configuration.
        
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
                  'clusterid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['updateconfigurationresponse']['configuration']
            data = res
            self.logger.debug('Set cluster %s configuration: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data    