'''
Created on May 10, 2013

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .host import Host
from .cluster import Cluster

class Pod(ClskObject):
    """Pod api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'pod'

    def get_zone(self):
        return self._data['zoneid']

    '''
    @watch
    def info(self):
        """Describe pod
        
        :return: Dictionary with all pod configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listPods',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listpodsresponse']['pod'][0]
            self._data = res
            self.logger.debug('Get pod %s description' % self.name)
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
    '''

    @watch
    def update(self, allocationstate=None, name=None, startip=None,
                     endip=None, gateway=None, netmask=None):
        """Updates a Pod.
        
        :param allocationstate: Allocation state of this cluster for allocation 
                                of new resources
        :param name: the name of the Pod
        :param startip: the starting IP address for the Pod
        :param endip: the ending IP address for the Pod
        :param gateway: the gateway for the Pod
        :param netmask: the netmask of the Pod
        :return: Dictionary with all cluster configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updatePod',
                  'id':self.id}
        
        if allocationstate:
            params['allocationstate'] = allocationstate
        if name:
            params['name'] = name
        if startip:
            params['startip'] = startip
        if endip:
            params['endip'] = endip            
        if gateway:
            params['gateway'] = gateway        
        if netmask:
            params['netmask'] = netmask 

        try:
            response = self.send_request(params)
            res = json.loads(response)['updatepodresponse']['pod'][0]
            self._data = res
            self.logger.debug('Update pod %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    
    @watch
    def delete(self):
        """Deletes a pod.
        
        :return: True if operation is executed successfully
        :rtype: bool        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'deletePod',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['deletepodresponse']['success']
            self._data = res
            self.logger.debug('Delete pod %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def tree(self):
        '''Return pod tree.'''
        pod = {'name':self.name, 
               'id':self.id, 
               'type':self._obj_type, 
               'childs':[]} 
        for cluster in self.list_clusters():
            pod['childs'].append(cluster.tree())
        
        self.logger.debug('Get pod %s tree' % self.name)
        return pod

    @watch
    def list_clusters(self):
        """List all clusters.
        
        :return: Clusters list
        :rtype: lsit
        :raises ClskError: raise :class:`.base.ClskError`
        """          
        params = {'command':'listClusters',
                  'podid':self.id,
                 }
        
        try:
            response = self.send_request(params)
            data = json.loads(response)['listclustersresponse']['cluster']
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        clusters = []
        for item in data:
            # create Account instance
            cluster = Cluster(self._orchestrator, item)
            clusters.append(cluster)
            
        self.logger.debug('Get pod %s clusters: %s' % (self.name, clusters))
        return clusters
    
    @watch
    def add_cluster(self, hypervisor, 
                          url=None, username=None, password=None, 
                          allocationstate=None,
                          guestvswitchname=None, guestvswitchtype=None,
                          publicvswitchname=None, publicvswitchtype=None,
                          vsmipaddress=None, vsmusername=None, vsmpassword=None):
        """Adds a new host.
        
        :param hypervisor: hypervisor type of the cluster: XenServer, KVM, 
                           VMware, Hyperv, BareMetal, Simulator        
        :param allocationstate: Allocation state of this cluster for allocation 
                                of new resources
        :param url: the URL
        :param username: the username for the cluster
        :param password: the password for the host
        :param guestvswitchname: Name of virtual switch used for guest traffic 
                                 in the cluster. This would override zone wide 
                                 traffic label setting.
        :param guestvswitchtype: Type of virtual switch used for guest traffic 
                                 in the cluster. Allowed values are, vmwaresvs 
                                 (for VMware standard vSwitch) and vmwaredvs 
                                 (for VMware distributed vSwitch)        
        :param publicvswitchname: Name of virtual switch used for public traffic
                                  in the cluster. This would override zone wide 
                                  traffic label setting.
        :param publicvswitchtype: Type of virtual switch used for public traffic 
                                  in the cluster. Allowed values are, vmwaresvs 
                                  (for VMware standard vSwitch) and vmwaredvs 
                                  (for VMware distributed vSwitch)
        :param vsmipaddress: the ipaddress of the VSM associated with this cluster
        :param vsmusername: the username for the VSM associated with this cluster
        :param vsmpassword: the password for the VSM associated with this cluster
        :return: Object of type :class:`.cluster.Cluster`
        :rtype: :class:`.host.Host`      
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'addCluster',
                  'zoneid':self.get_zone(),
                  'podid':self.id,
                  'clusterid':self.id,
                  'hypervisor':hypervisor}

        if allocationstate:
            params['allocationstate'] = allocationstate
        if url:
            params['url'] = url
        if username:
            params['username'] = username
        if password:
            params['password'] = password
        if guestvswitchname:
            params['guestvswitchname'] = guestvswitchname
        if guestvswitchtype:
            params['guestvswitchtype'] = guestvswitchtype
        if publicvswitchname:
            params['publicvswitchname'] = publicvswitchname      
        if publicvswitchtype:
            params['publicvswitchtype'] = publicvswitchtype
        if vsmipaddress:
            params['vsmipaddress'] = vsmipaddress                        
        if vsmusername:
            params['vsmusername'] = vsmusername 
        if vsmpassword:
            params['vsmpassword'] = vsmpassword 

        try:
            response = self.send_request(params)
            data = json.loads(response)['addclusterresponse']['cluster']
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        cluster = Cluster(self._orchestrator, data)
        
        self.logger.debug('Add cluster %s to pod %s' % (cluster, self))
        return cluster      