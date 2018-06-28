'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .cluster import Cluster

class Pod(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'pod'

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listPods',
                  'id':self._id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listpodsresponse']['pod'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)

    def tree(self):
        '''Return pod tree.'''
        pod = {'name':self._name, 
               'id':self._id, 
               'type':self._obj_type, 
               'childs':[]} 
        for cluster in self.list_clusters():
            pod['childs'].append(cluster.tree())
        return pod
        
    def list_clusters(self):
        '''List all clusters'''
        params = {'command':'listClusters',
                  'podid':self._id}
        
        try:
            response = self._api_client.send_api_request(params)
            data = json.loads(response)['listclustersresponse']['cluster']
        except KeyError:
            data = []
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        clusters = []
        for item in data:
            # create Account instance
            cluster = Cluster(self._api_client, item)
            clusters.append(cluster)
        return clusters         