'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .pod import Pod

class Zone(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'zone'

    def info(self, cache=True):
        """Describe zone"""
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data
        
        params = {'command':'listZones',
                  'id':self._id}
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listzonesresponse']['zone'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)

    def tree(self):
        '''Return zone tree.'''
        zone = {'name':self._name, 
                'id':self._id, 
                'type':self._obj_type, 
                'childs':[]}        
        for pod in self.list_pods():
            zone['childs'].append(pod.tree())
        return zone

    def list_pods(self):
        '''List all pods'''
        params = {'command':'listPods',
                  'listAll':'true',
                  'zoneid':self._id,
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listpodsresponse']['pod']
            data = res
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        pods = []
        for item in data:
            # create Account instance
            pod = Pod(self._api_client, item)
            pods.append(pod)
        return pods

    def list_hypervisors(self):
        '''List all hypervisors'''
        params = {'command':'listHypervisors',
                  'zoneid':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listhypervisorsresponse']['hypervisor']
            data = res
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)

        return data    