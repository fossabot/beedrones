'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .zone import Zone

class Region(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'region'

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listRegions',
                  'id':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listregionsresponse']['region'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)