'''
Created on May 11, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError

class Template(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        self._obj_type = 'template'

    def info(self, cache=True):
        '''Describe template '''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data        
        
        params = {'command':'listTemplates',
                  'templatefilter':'community',
                  'id':self._id}
        
        try:
            response = self._api_client.send_api_request(params)        
            res = json.loads(response)['listtemplatesresponse']
            if len(res) > 0:
                self._data = res['template'][0]
                return self._data
            else:
                return None
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)