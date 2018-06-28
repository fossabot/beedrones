'''
Created on May 10, 2013

@author: darkbk
'''
import json
from gibboncloud.cloudstack.dso import Volume
from gibboncloud.cloudstack.dso.base import ClskObjectError, ApiError
from gibboncloud.cloudstack.dso_ext.base import ApiManagerError
from gibboncloud.virt.domain import VirtDomain, VirtDomainError

class VolumeExt(Volume):
    ''' '''
    def __init__(self, clsk_instance, data=None, oid=None):
        ''' '''
        self.clsk_instance = clsk_instance
        #self.db_manager = VmModelManager(self.clsk_instance.db_manager)
        
        api_client = clsk_instance.get_api_client()
        Volume.__init__(self, api_client, data=data, oid=oid)
        
    def get_storagepool_info(self):
        '''List all storage pools.'''
        params = {'command':'listStoragePools',
                  'name':self._data['storage']}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['liststoragepoolsresponse']
            if len(res) > 0:
                data = res['storagepool'][0]
                pool_info = {'type':data['type'],
                             'state':data['state'],
                             'path':data['path'],
                             'ipaddress':data['ipaddress']}
                
                return pool_info
            else:
                return None
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def tree(self):
        
        
        return None