'''
Created on May 10, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from .host import Host

class Cluster(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        self._obj_type = 'cluster'

    def info(self, cache=True):
        '''Describe account'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        params = {'command':'listClusters',
                  'name':self._name,
                  'domainid':self._domain_id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listclustersresponse']['cluster'][0]
            self._data = res
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)

    def tree(self):
        '''Return cluster tree.'''
        cluster = {'name':self._name, 'id':self._id, 'childs':[]}
        for host in self.list_hosts():
            cluster['childs'].append(host.tree())
        return cluster

    
    def list_hosts(self):
        '''List hosts'''
        params = {'command':'listHosts',
                  'listAll':'true',
                  'clusterid':self._id,
                 }

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listhostsresponse']
            if 'host' in res:
                data = res['host']
            else:
                data = []
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskObjectError(ex)
        
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._api_client, item)
            hosts.append(host)
        return hosts  