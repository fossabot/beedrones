'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .cluster import Cluster

class Volume(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'volume'

    def info(self, cache=True):
        '''Describe volume'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listVolumes',
                  'id':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvolumesresponse']['volume'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)     