"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .virtual_machine import VirtualMachine
from .virtual_router import VirtualRouter
from .system_virtual_machine import SystemVirtualMachine

class Host(ClskObject):
    """Host api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'host'

    def get_zone(self):
        return self._data['zoneid']

    def get_pod(self):
        return self._data['podid']

    def get_cluster(self):
        return self._data['clusterid']

    @watch
    def update(self, allocationstate=None, hosttags=None, oscategoryid=None):
        """Update host.
        
        :param allocationstate: Change resource state of host, valid values are 
                                [Enable, Disable]. Operation may failed if host 
                                in states not allowing Enable/Disable
        :param hosttags: list of tags to be added to the host
        :param oscategoryid: the id of Os category to update the host with
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateHost',
                  'id':self.id}
        
        if allocationstate:
            params['allocationstate'] = allocationstate
        if hosttags:
            params['hosttags'] = hosttags
        if oscategoryid:
            params['oscategoryid'] = oscategoryid

        try:
            response = self.send_request(params)
            res = json.loads(response)['updatehostresponse']['host'][0]
            self._data = res
            self.logger.debug('Update host %s' % self.name)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete(self, forced=None, forcedestroylocalstorage=None):
        """Deletes a host.
        
        :param forced: Force delete the host. All HA enabled vms running on the 
                       host will be put to HA; HA disabled ones will be stopped
        :param forcedestroylocalstorage: Force destroy local storage on this 
                                         host. All VMs created on this local 
                                         storage will be destroyed
        :return: True if operation is executed successfully
        :rtype: bool        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'deleteHost',
                  'password':forced,
                  'username':forcedestroylocalstorage,
                  'id':self.id}

        if forced:
            params['forced'] = forced
        if forcedestroylocalstorage:
            params['forcedestroylocalstorage'] = forcedestroylocalstorage

        try:
            response = self.send_request(params)
            res = json.loads(response)['deletehostresponse']['success']
            self._data = res
            self.logger.debug('Delete host %s' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def update_password(self, username, password):
        """Update password of a host/pool on management server.
        
        :param password: the new password for the host/cluster
        :param username: the username for the host/cluster
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateHostPassword',
                  'password':password,
                  'username':username,
                  'hostid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['updatehostpasswordresponse']['host'][0]
            self._data = res
            self.logger.debug('Update host %s password' % self)
            return self._data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def tree(self):
        """Return host tree.
        
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        host = {'name':self.name, 
                'id':self.id, 
                'type':self._obj_type, 
                'childs':[]}
        
        for vm in self.list_all_virtual_machines():
            host['childs'].append({'name':vm.name,
                                   'id':vm.id,
                                   'type':vm._obj_type,
                                   'state':vm.state})
            
        self.logger.debug('List host %s tree' % (self.name))
        return host

    def list_all_virtual_machines(self):
        """List all visrtual machines.
        
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        vms = self.list_virtual_machines()
        vms.extend(self.list_system_vms())
        vms.extend(self.list_routers())
        return vms

    @watch    
    def list_system_vms(self):
        """List all system vms.
        
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'listSystemVms',
                  'listall':'true',
                  'hostid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listsystemvmsresponse']
            if len(res) > 0:
                data = res['systemvm']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)      
        
        vms = []
        for item in data:
            # create Account instance
            vm = SystemVirtualMachine(self._orchestrator, item)
            vms.append(vm)
            
        self.logger.debug('List host %s virtual machine: %s' % (self.name, vms))
        return vms 

    @watch
    def list_routers(self):
        """List all routers.
        
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'listRouters',
                  'listall':'true',
                  'hostid':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualRouter(self._orchestrator, item)
            vms.append(vm)
            
        self.logger.debug('List host %s virtual router: %s' % (self.name, vms))
        return vms

    @watch
    def list_virtual_machines(self):
        """List virtual machines.
        
        :return: Dictionary with all host configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'listVirtualMachines',
                  'listall':'true',
                  'hostid':self.id}      

        try:
            response = self.send_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)     
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachine(self._orchestrator, item)
            vms.append(vm)
        
        self.logger.debug('List host %s virtual machine: %s' % (self.name, vms))
        return vms

    @watch
    def maintenance(self):
        """Prepares a host for maintenance.

        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'prepareHostForMaintenance',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['preparehostformaintenanceresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'prepareHostForMaintenance', res))
            return clsk_job_id
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def cancel_maintenance(self):
        """Cancels host maintenance.

        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'cancelHostMaintenance',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['cancelhostmaintenanceresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'cancelHostMaintenance', res))
            return clsk_job_id
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def reconnect(self):
        """Reconnects a host.

        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'reconnectHost',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['reconnecthostresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'reconnectHost', res))
            return clsk_job_id
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)