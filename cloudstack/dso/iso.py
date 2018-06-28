'''
Created on May 11, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError

class Iso(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        self._obj_type = 'iso'

    def info(self, cache=True):
        ''' '''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data        
        
        params = {'command':'listIsos',
                  'templatefilter':'all',
                  'id':self._id}
        
        try:
            response = self.send_api_request(params)
            res = []
            data = json.loads(response)['listisosresponse']['iso'][0]
            # ostypename size
            os = ''
            if (data['ostypename'].find('Ubuntu') != -1 or
                data['ostypename'].find('Debian') != -1 or
                data['ostypename'].find('Fedora') != -1 or
                data['ostypename'].find('CentOS') != -1 or
                data['ostypename'].find('FreeBSD') != -1 or
                data['ostypename'].find('Linux') != -1):
                os = 'linux'
            elif (data['ostypename'].find('Windows') != -1):
                os = 'windows'
            res = {'os':os, 'disk_size':data['size']}
            return res
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)