'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .virtual_machine import VirtualMachine

class Host(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'host'

    def info(self, cache=True):
        '''Describe host'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data
        
        params = {'command':'listHosts',
                  'name':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listhostsresponse']['host'][0]
            self._data = res
            return self._data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def tree(self):
        '''Return host tree.'''
        host = {'name':self._name, 
                'id':self._id, 
                'type':self._obj_type, 
                'childs':[]} 
        for vm in self.list_all_virtual_machines():
            host['childs'].append({'name':vm.name,
                                   'id':vm.id,
                                   'type':vm.obj_type,
                                   'vm_type':vm.type,
                                   'state':vm.get_state()})
        return host
        
    def list_all_virtual_machines(self):
        '''List all clusters'''
        vms = self.list_virtual_machines()
        vms.extend(self.list_system_vms())
        vms.extend(self.list_routers())
        return vms
    
    def list_system_vms(self):
        '''List all system vms'''
        params = {'command':'listSystemVms',
                  'listall':'true',
                  'hostid':self._id,                
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listsystemvmsresponse']
            if len(res) > 0:
                data = res['systemvm']
            else:
                return []
        except KeyError as ex:
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
                  'listall':'true',
                  'hostid':self._id,  
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
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms

    def list_virtual_machines(self):
        '''List virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'listall':'true',
                  'hostid':self._id,
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
            vm = VirtualMachine(self._api_client, item)
            vms.append(vm)
        return vms  