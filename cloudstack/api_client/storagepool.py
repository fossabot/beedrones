'''
Created on May 10, 2013

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from .volume import Volume

class StoragePool(ClskObject):
    """StoragePool api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'storagepool'
    
    @watch
    def tree(self):
        '''Return host tree.'''
        host = {'name':self.name, 
                'id':self.id, 
                'type':self._obj_type, 
                'childs':[]} 
        for vm in self.list_all_virtual_machines():
            host['childs'].append({'name':vm.name,
                                   'id':vm.id,
                                   'type':vm.obj_type,
                                   'vm_type':vm.type,
                                   'state':vm.get_state()})
        return host

    @watch
    def list_volumes(self):
        '''List storage pool volumes.'''
        params = {'command':'listVolumes',
                  'listall':'true',
                  'zoneid':self._data['zoneid'],
                 }      

        try:
            response = self.send_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                data = res['volume']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)     
        
        volumes = []
        for item in data:
            # create Volume instance
            volume = Volume(self._orchestrator, item)
            volumes.append(volume)
        
        return volumes 