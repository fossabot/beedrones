'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError

class ServiceOffering(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None, domain_id=None):
        ''' '''
        # attributes
        self._obj_type = 'serviceoffering'
        
        ClskObject.__init__(self, api_client, data=data, oid=oid)

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listServiceOfferings',
                  'id':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listserviceofferingsresponse']['serviceoffering'][0]
            self._data = res
            return self._data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data - %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
class NetworkOffering(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None, domain_id=None):
        ''' '''
        # attributes
        self._obj_type = 'networkoffering'
        
        ClskObject.__init__(self, api_client, data=data, oid=oid)

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listNetworkOfferings',
                  'id':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listnetworkofferingsresponse']['networkoffering'][0]
            self._data = res
            return self._data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data - %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
class DiskOffering(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None, domain_id=None):
        ''' '''
        # attributes
        self._obj_type = 'diskoffering'
        
        ClskObject.__init__(self, api_client, data=data, oid=oid)

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listNetworkOfferings',
                  'id':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listnetworkofferingsresponse']['networkoffering'][0]
            self._data = res
            return self._data
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data - %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)