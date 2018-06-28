'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .volume import Volume

class StoragePool(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'storagepool'

    def info(self, cache=True):
        '''Describe host'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data
        
        params = {'command':'listStoragePools',
                  'name':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['liststoragepoolsresponse']['storagepool'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
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

    def list_volumes(self):
        '''List storage pool volumes.'''
        params = {'command':'listVolumes',
                  'listall':'true',
                  'zoneid':self._data['zoneid'],
                 }      

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
            volume = Volume(self._api_client, data=item)
            volumes.append(volume)
        
        return volumes 