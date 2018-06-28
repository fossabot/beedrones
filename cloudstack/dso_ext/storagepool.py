'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .virtual_machine import VirtualMachineExt
from .volume import VolumeExt
from gibboncloud.cloudstack.dso.virtual_machine import VirtualMachine
from gibboncloud.cloudstack.dso import StoragePool
from gibboncloud.cloudstack.dso.base import ClskObjectError, ApiError
from gibboncloud.cloudstack.dso_ext.base import ApiManagerError
from gibboncloud.virt.domain import VirtDomain, VirtDomainError

class StoragePoolExt(StoragePool):
    ''' '''
    def __init__(self, clsk_instance, data=None, oid=None):
        ''' '''
        self.clsk_instance = clsk_instance
        #self.db_manager = VmModelManager(self.clsk_instance.db_manager)
        
        api_client = clsk_instance.get_api_client()
        StoragePool.__init__(self, api_client, data=data, oid=oid)

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
            volume = VolumeExt(self.clsk_instance, data=item)
            volumes.append(volume)
        
        return volumes 