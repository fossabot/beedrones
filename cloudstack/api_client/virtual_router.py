'''
Created on May 21, 2014

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch

class VirtualRouter(ClskObject):
    """VirtualRouter api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        # attributes
        self._type = None 
        self._obj_type = 'vr'
        self._domain_id = None

    def list_nics(self):
        """List virtual machine nics."""
        return self._data['nic']

    @watch
    def start(self, job_id):
        """Start virtual router. 
        
        *Async command*
        
        """
        params = {'command':'startRouter',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['startrouterresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def stop(self, job_id):
        """Stop virtual router.
        
        *Async command*
        
        """        
        params = {'command':'stopRouter',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['stoprouterresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def destroy(self, job_id):
        """Destroy virtual router.
        
        *Async command*
        """        
        params = {'command':'destroyRouter',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['destroyrouterresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def migrate(self, job_id, hostid):
        """Migrate system virtual machine.
        
        *Async command*
        """        
        params = {'command':'migrateSystemVm',
                  'virtualmachineid':self.id,
                  'hostid':hostid}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            print res
            clsk_job_id = res['migratesystemvmresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def change_service_offering(self, job_id, serviceofferingid):
        """Upgrades domain router to a new service offering.
        
        *Async command*
        
        :param str serviceofferingid: the service offering ID to apply to the domain router
        """        
        params = {'command':'changeServiceForRouter',
                  'id':self.id,
                  'serviceofferingid':serviceofferingid}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['changeserviceforrouterresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)