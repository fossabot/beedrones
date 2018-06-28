'''
Created on May 21, 2014

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError
from gibbonutil.simple import get_attrib

class VirtualMachineType(object):
    GUEST_VM = 0
    SYSTEM_VM = 1
    ROUTER_VM = 2

class VirtualRouter(ClskObject):
    ''' '''   
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)
        
        # attributes
        self._type = None 
        self._obj_type = 'vrouter'
        self._domain_id = None
    
    def get_state(self):
        """Return running status. Possible value are:
        - Running
        - Stoppend
        - Stopping
        """
        if not self._data:
            self.info()
        
        return self._data['state']
    
    def info(self, cache=True):
        """Describe virtual router """
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data

        # get virtual machine info
        params = {'command':'listRouters',
                  'id':self._id}
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listroutersresponse']['routers'][0]
            self._data = res
            
            return self._data 
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)
        
    def list_volume(self):
        """List virtual machine volume."""
        # get virtual machine info
        params = {'command':'listVolumes',
                  'listall':'true',
                  'virtualmachineid':self._id}
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                vols = res['volume']
                volumes = []
                for vol in vols:
                    print vol
                    volumes.append({'id':vol['id'],
                                    'name':vol['name'],
                                    'offering':get_attrib(vol, 'diskofferingdisplaytext', ''),
                                    'size':vol['size'],
                                    'storage':vol['storage'],
                                    'type':vol['type'],
                                    'deviceid':vol['deviceid'],
                                    'attached':get_attrib(vol, 'attached', '')})
                return volumes
                
            else:
                return []
            
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def start(self, job_id):
        """Start virtual machine. 
        Async command."""
        params = {'command':'startVirtualMachine',
                  'id':self._id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['startvirtualmachineresponse']['jobid']
            # query async cloudstakc job
            job_res = self._api_client.query_async_job(job_id, clsk_job_id)
            
            return job_res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def stop(self, job_id):
        """Stop virtual machine.
        Async command."""        
        params = {'command':'stopVirtualMachine',
                  'id':self._id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['stopvirtualmachineresponse']['jobid']
            job_res = self._api_client.query_async_job(job_id, clsk_job_id)
            
            return job_res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)

    def destroy(self, job_id):
        """Destroy virtual machine.
        Async command."""        
        params = {'command':'destroyVirtualMachine',
                  'id':self._id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['destroyvirtualmachineresponse']['jobid']
            job_res = self._api_client.query_async_job(job_id, clsk_job_id)
            
            return job_res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)  

    def migrate(self, job_id, hostid=None, storageid=None):
        """Migrate a virtual machine.
        
        TO-DO: migrate correctly vm if is started or stopped
        
        Async command."""
        params = {'command':'migrateVirtualMachine',
                  'virtualmachineid':self._id}
        if hostid:
            params['hostid'] = hostid
        elif storageid:
            params['storageid'] = storageid            

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['migratevirtualmachineresponse']['jobid']
            job_res = self.query_async_job(job_id, clsk_job_id)
            
            return job_res
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)           